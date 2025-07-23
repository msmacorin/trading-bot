import schedule
import time
import logging
from datetime import datetime, time as dt_time
from sqlalchemy.orm import Session
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import pandas as pd
import numpy as np
from collections import defaultdict
from backend.analyzer import analyze_stock
from backend.notifier import send_email_notification
from backend.database import SessionLocal, Acao, Carteira, Usuario, get_acoes_ativas, get_carteira
import threading

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)

# Métricas Prometheus
RECOMMENDATIONS_COUNTER = Counter('trading_recommendations_total', 'Total de recomendações', ['action', 'stock', 'user_id'])
ANALYSIS_DURATION = Histogram('analysis_duration_seconds', 'Duração da análise em segundos')
RSI_GAUGE = Gauge('stock_rsi', 'RSI da ação', ['stock', 'user_id'])
MACD_GAUGE = Gauge('stock_macd', 'MACD da ação', ['stock', 'user_id'])
PRICE_GAUGE = Gauge('stock_price', 'Preço atual da ação', ['stock', 'user_id'])
TREND_GAUGE = Gauge('stock_trend', 'Tendência da ação (1=UP, 0=DOWN)', ['stock', 'user_id'])
EMAIL_NOTIFICATIONS = Counter('email_notifications_total', 'Total de notificações por email enviadas', ['user_id'])
ANALYSIS_ERRORS = Counter('analysis_errors_total', 'Total de erros na análise', ['stock', 'user_id'])

# Cache compartilhado para análises (para evitar análises duplicadas)
analysis_cache = {}
cache_timestamp = None

# Lock global para cada ação analisada on-demand
analysis_locks = {}
analysis_locks_global = threading.Lock()

def is_market_open():
    """
    Verifica se a bolsa brasileira está aberta
    Horário: 9h às 17h, segunda a sexta-feira (horário de Brasília)
    """
    now = datetime.now()
    
    # Verifica se é dia útil (segunda a sexta = 0 a 4)
    if now.weekday() >= 5:  # 5 = sábado, 6 = domingo
        return False
    
    # Verifica se está no horário de funcionamento (9h às 17h)
    market_open = dt_time(9, 0)   # 9:00
    market_close = dt_time(17, 0)  # 17:00
    current_time = now.time()
    
    return market_open <= current_time <= market_close

def get_all_unique_stocks():
    """
    Coleta todas as ações únicas monitoradas por todos os usuários ativos
    Retorna um dict com:
    - stock_code: set de user_ids que possuem essa ação
    """
    db = SessionLocal()
    try:
        # Busca todos os usuários ativos
        usuarios_ativos = db.query(Usuario).filter(Usuario.ativo == True).all()
        
        # Dicionário para armazenar: codigo_acao -> {usuario_ids}
        stocks_users = defaultdict(set)
        
        # Para cada usuário ativo, pega suas ações
        for usuario in usuarios_ativos:
            stocks = db.query(Acao).filter(
                Acao.ativo == True, 
                Acao.usuario_id == usuario.id
            ).all()
            
            for stock in stocks:
                stocks_users[stock.codigo].add(usuario.id)
        
        logging.info(f"📊 Encontradas {len(stocks_users)} ações únicas monitoradas por {len(usuarios_ativos)} usuários")
        
        # Log de estatísticas
        for codigo, user_ids in stocks_users.items():
            logging.info(f"   {codigo}: monitorada por {len(user_ids)} usuário(s)")
        
        return dict(stocks_users)
        
    except Exception as e:
        logging.error(f"❌ Erro ao coletar ações únicas: {str(e)}")
        return {}
    finally:
        db.close()

def analyze_unique_stocks():
    """
    Analisa cada ação única apenas uma vez e armazena no cache compartilhado
    """
    global analysis_cache, cache_timestamp
    
    logging.info("🔄 Iniciando análise otimizada com cache compartilhado...")
    
    # Limpa o cache anterior
    analysis_cache.clear()
    cache_timestamp = datetime.now()
    
    # Coleta todas as ações únicas
    stocks_users = get_all_unique_stocks()
    
    if not stocks_users:
        logging.warning("⚠️ Nenhuma ação encontrada para análise")
        return
    
    total_stocks = len(stocks_users)
    total_users_affected = sum(len(users) for users in stocks_users.values())
    
    logging.info(f"🎯 Iniciando análise de {total_stocks} ações únicas (afetando {total_users_affected} usuários)")
    
    analysis_errors = []
    successful_analyses = 0
    
    # Analisa cada ação única apenas uma vez
    for i, (codigo_acao, user_ids) in enumerate(stocks_users.items(), 1):
        try:
            logging.info(f"📈 [{i}/{total_stocks}] Analisando {codigo_acao} (usuários: {len(user_ids)})...")
            
            start_time = time.time()
            
            # Realiza a análise (única por ação)
            analysis = analyze_stock(codigo_acao)
            
            # Registra tempo de análise
            duration = time.time() - start_time
            ANALYSIS_DURATION.observe(duration)
            
            # Armazena no cache compartilhado
            analysis_cache[codigo_acao] = {
                'analysis': analysis,
                'user_ids': user_ids,
                'analyzed_at': datetime.now()
            }
            
            successful_analyses += 1
            
            logging.info(f"✅ {codigo_acao}: {analysis['current_position']}/{analysis['new_position']} - RSI: {analysis['rsi']:.2f}, MACD: {analysis['macd']:.2f} (duração: {duration:.2f}s)")
            
        except Exception as e:
            error_msg = f"❌ Erro ao analisar {codigo_acao}: {str(e)}"
            analysis_errors.append(error_msg)
            logging.error(error_msg)
            
            # Registra erro para todos os usuários desta ação
            for user_id in user_ids:
                ANALYSIS_ERRORS.labels(stock=codigo_acao, user_id=user_id).inc()
    
    # Estatísticas finais
    total_time = (datetime.now() - cache_timestamp).total_seconds()
    logging.info(f"🎯 Análise concluída: {successful_analyses}/{total_stocks} ações analisadas em {total_time:.2f}s")
    
    if analysis_errors:
        logging.warning(f"⚠️ {len(analysis_errors)} erros durante a análise")
    
    return successful_analyses, len(analysis_errors)

def process_user_notifications():
    """
    Processa notificações para cada usuário baseado no cache compartilhado
    """
    if not analysis_cache:
        logging.warning("⚠️ Cache de análises vazio, pulando notificações")
        return
    
    db = SessionLocal()
    try:
        # Busca todos os usuários ativos
        usuarios_ativos = db.query(Usuario).filter(Usuario.ativo == True).all()
        
        logging.info(f"📧 Processando notificações para {len(usuarios_ativos)} usuários...")
        
        for usuario in usuarios_ativos:
            try:
                process_single_user_notifications(usuario, db)
            except Exception as e:
                logging.error(f"❌ Erro ao processar notificações do usuário {usuario.nome}: {str(e)}")
    
    except Exception as e:
        logging.error(f"❌ Erro geral ao processar notificações: {str(e)}")
    finally:
        db.close()

def process_single_user_notifications(usuario, db):
    """
    Processa notificações para um único usuário baseado no cache
    """
    # Listas para armazenar resultados do usuário
    buy_signals = []
    sell_signals = []
    all_analyses = []
    
    # Para cada ação no cache, verifica se o usuário a possui
    for codigo_acao, cache_data in analysis_cache.items():
        if usuario.id not in cache_data['user_ids']:
            continue  # Usuário não possui esta ação
        
        analysis = cache_data['analysis']
        
        # Registra métricas específicas do usuário
        RSI_GAUGE.labels(stock=codigo_acao, user_id=usuario.id).set(analysis['rsi'])
        MACD_GAUGE.labels(stock=codigo_acao, user_id=usuario.id).set(analysis['macd'])
        PRICE_GAUGE.labels(stock=codigo_acao, user_id=usuario.id).set(analysis['price'])
        TREND_GAUGE.labels(stock=codigo_acao, user_id=usuario.id).set(1 if analysis['trend'] == 'UP' else 0)
        
        # Adiciona à lista de análises do usuário
        all_analyses.append({
            'stock': codigo_acao,
            'analysis': analysis
        })
        
        # Verifica se há posição na carteira do usuário
        portfolio_position = db.query(Carteira).filter(
            Carteira.codigo == codigo_acao, 
            Carteira.usuario_id == usuario.id
        ).first()
        
        # Lógica de notificação
        if portfolio_position:
            # Tem a ação na carteira - verifica sinais de venda
            if analysis['current_position'] == 'SELL':
                RECOMMENDATIONS_COUNTER.labels(action='SELL', stock=codigo_acao, user_id=usuario.id).inc()
                sell_signals.append({
                    'stock': codigo_acao,
                    'analysis': analysis,
                    'position': portfolio_position
                })
        else:
            # Não tem a ação na carteira - verifica sinais de compra
            if analysis['new_position'] == 'BUY':
                RECOMMENDATIONS_COUNTER.labels(action='BUY', stock=codigo_acao, user_id=usuario.id).inc()
                buy_signals.append({
                    'stock': codigo_acao,
                    'analysis': analysis
                })
    
    # Envia email com resumo das análises do usuário (se houver conteúdo)
    if buy_signals or sell_signals or all_analyses:
        send_user_analysis_summary_email(usuario, buy_signals, sell_signals, all_analyses, [])
        logging.info(f"📧 Email enviado para {usuario.nome} ({len(buy_signals)} compras, {len(sell_signals)} vendas, {len(all_analyses)} análises)")
    else:
        logging.info(f"📧 Nenhuma notificação para {usuario.nome}")

def analyze_all_stocks():
    """
    Função principal otimizada: analisa cada ação apenas uma vez e distribui para todos os usuários
    """
    logging.info("🚀 Iniciando ciclo de análise otimizado...")
    
    # Etapa 1: Analisa cada ação única uma vez e armazena no cache
    successful_analyses, errors = analyze_unique_stocks()
    
    # Etapa 2: Processa notificações para cada usuário baseado no cache
    if successful_analyses > 0:
        process_user_notifications()
    else:
        logging.warning("⚠️ Nenhuma análise bem-sucedida, pulando notificações")
    
    # Estatísticas finais
    total_time = (datetime.now() - cache_timestamp).total_seconds() if cache_timestamp else 0
    cache_size = len(analysis_cache)
    
    logging.info(f"🎯 Ciclo concluído: {cache_size} ações no cache, {successful_analyses} sucessos, {errors} erros em {total_time:.2f}s")

# Função legacy mantida para compatibilidade (agora usa o cache)
def analyze_user_stocks(usuario_id):
    """
    FUNÇÃO LEGACY: Analisa ações de um usuário (agora usa cache compartilhado)
    Mantida para compatibilidade com chamadas diretas
    """
    logging.info(f"🔄 Análise individual do usuário {usuario_id} (usando cache compartilhado)...")
    
    # Se não há cache, faz análise completa
    if not analysis_cache:
        logging.info("Cache vazio, executando análise completa...")
        analyze_all_stocks()
        return
    
    # Usa o cache existente
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.ativo == True).first()
        if not usuario:
            logging.warning(f"⚠️ Usuário {usuario_id} não encontrado ou inativo")
            return
        
        process_single_user_notifications(usuario, db)
        logging.info(f"🎯 Análise do usuário {usuario.nome} concluída usando cache!")
        
    except Exception as e:
        logging.error(f"❌ Erro na análise do usuário {usuario_id}: {str(e)}")
    finally:
        db.close()

def analyze_stock_on_demand(codigo_acao: str):
    """
    Analisa uma ação on-demand, com lock para evitar execuções simultâneas e salva no cache compartilhado.
    """
    global analysis_cache, cache_timestamp, analysis_locks, analysis_locks_global
    
    # Lock por ação
    with analysis_locks_global:
        if codigo_acao not in analysis_locks:
            analysis_locks[codigo_acao] = threading.Lock()
        lock = analysis_locks[codigo_acao]
    
    with lock:
        # Se já está no cache, retorna direto
        if codigo_acao in analysis_cache:
            return analysis_cache[codigo_acao]['analysis']
        
        # Faz análise e salva no cache
        from backend.analyzer import analyze_stock
        analysis = analyze_stock(codigo_acao)
        analysis_cache[codigo_acao] = {
            'analysis': analysis,
            'user_ids': set(),  # on-demand pode não saber os usuários, mas pode ser atualizado depois
            'analyzed_at': datetime.now()
        }
        cache_timestamp = datetime.now()
        return analysis

def send_user_analysis_summary_email(usuario, buy_signals, sell_signals, all_analyses, errors):
    """Envia email com resumo das análises de um usuário específico"""
    from datetime import datetime
    
    # Verifica se a bolsa está aberta antes de enviar o email
    if not is_market_open():
        logging.info(f"📧 Email para {usuario.nome} não enviado - bolsa fechada (horário: {datetime.now().strftime('%H:%M')})")
        return
    
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    subject = f"📊 Relatório de Análise - {usuario.nome} - {current_time}"
    
    # Cabeçalho personalizado
    body = f"""
    <h1>📊 Relatório de Análise de Ações</h1>
    <p><strong>Usuário:</strong> {usuario.nome}</p>
    <p><strong>Email:</strong> {usuario.email}</p>
    <p><strong>Data/Hora:</strong> {current_time}</p>
    <p><strong>Total de ações analisadas:</strong> {len(all_analyses)}</p>
    <p><strong>🎯 Sistema Otimizado:</strong> Análise única por ação (compartilhada entre usuários)</p>
    <hr>
    """
    
    # Seção de sinais de compra
    if buy_signals:
        body += f"""
        <h2>🟢 Sinais de Compra ({len(buy_signals)} ações)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #e8f5e8;">
            <th>Ação</th>
            <th>Preço</th>
            <th>RSI</th>
            <th>MACD</th>
            <th>Tendência</th>
            <th>Recomendação</th>
        </tr>
        """
        
        for signal in buy_signals:
            analysis = signal['analysis']
            body += f"""
            <tr>
                <td><strong>{signal['stock']}</strong></td>
                <td>R$ {analysis['price']:.2f}</td>
                <td>{analysis['rsi']:.1f}</td>
                <td>{analysis['macd']:.3f}</td>
                <td>{analysis['trend']}</td>
                <td style="color: green;"><strong>{analysis['new_position']}</strong></td>
            </tr>
            """
        
        body += "</table><br>"
    
    # Seção de sinais de venda
    if sell_signals:
        body += f"""
        <h2>🔴 Sinais de Venda ({len(sell_signals)} posições)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #ffe8e8;">
            <th>Ação</th>
            <th>Quantidade</th>
            <th>Preço Médio</th>
            <th>Preço Atual</th>
            <th>Lucro/Prejuízo</th>
            <th>RSI</th>
            <th>Recomendação</th>
        </tr>
        """
        
        for signal in sell_signals:
            analysis = signal['analysis']
            position = signal['position']
            current_value = position.quantidade * analysis['price']
            invested_value = position.quantidade * position.preco_medio
            profit_loss = current_value - invested_value
            profit_pct = (profit_loss / invested_value) * 100 if invested_value > 0 else 0
            
            profit_color = "green" if profit_loss >= 0 else "red"
            
            body += f"""
            <tr>
                <td><strong>{signal['stock']}</strong></td>
                <td>{position.quantidade}</td>
                <td>R$ {position.preco_medio:.2f}</td>
                <td>R$ {analysis['price']:.2f}</td>
                <td style="color: {profit_color};">R$ {profit_loss:.2f} ({profit_pct:+.1f}%)</td>
                <td>{analysis['rsi']:.1f}</td>
                <td style="color: red;"><strong>{analysis['current_position']}</strong></td>
            </tr>
            """
        
        body += "</table><br>"
    
    # Seção com todas as análises (resumo)
    if all_analyses:
        body += f"""
        <h2>📈 Resumo Geral ({len(all_analyses)} ações)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f0f0f0;">
            <th>Ação</th>
            <th>Preço</th>
            <th>RSI</th>
            <th>MACD</th>
            <th>Tendência</th>
            <th>Recomendação Atual</th>
            <th>Nova Posição</th>
        </tr>
        """
        
        for item in all_analyses:
            analysis = item['analysis']
            
            # Cores baseadas nas recomendações
            current_color = "red" if analysis['current_position'] == 'SELL' else "blue"
            new_color = "green" if analysis['new_position'] == 'BUY' else "gray"
            
            body += f"""
            <tr>
                <td><strong>{item['stock']}</strong></td>
                <td>R$ {analysis['price']:.2f}</td>
                <td>{analysis['rsi']:.1f}</td>
                <td>{analysis['macd']:.3f}</td>
                <td>{analysis['trend']}</td>
                <td style="color: {current_color};">{analysis['current_position']}</td>
                <td style="color: {new_color};">{analysis['new_position']}</td>
            </tr>
            """
        
        body += "</table><br>"
    
    # Seção de estatísticas do cache
    if cache_timestamp:
        cache_age = (datetime.now() - cache_timestamp).total_seconds()
        body += f"""
        <h3>📊 Informações do Sistema</h3>
        <ul>
            <li><strong>Cache gerado:</strong> {cache_timestamp.strftime('%H:%M:%S')}</li>
            <li><strong>Idade do cache:</strong> {cache_age:.0f} segundos</li>
            <li><strong>Ações no cache:</strong> {len(analysis_cache)}</li>
            <li><strong>Análises otimizadas:</strong> Uma análise por ação, compartilhada entre usuários</li>
        </ul>
        """
    
    # Rodapé
    body += """
    <hr>
    <p style="font-size: 12px; color: #666;">
    Este relatório foi gerado automaticamente pelo Trading Bot.<br>
    <strong>🚀 Novo sistema otimizado:</strong> Cada ação é analisada apenas uma vez por ciclo, 
    independentemente de quantos usuários a possuem, resultando em maior eficiência e menor uso de recursos.
    </p>
    """
    
    # Registra métrica de email
    EMAIL_NOTIFICATIONS.labels(user_id=usuario.id).inc()
    
    # Envia o email
    send_email_notification(subject, body, usuario.email)
    logging.info(f"📧 Email enviado para {usuario.nome} ({usuario.email})")

def get_cache_stats():
    """Retorna estatísticas do cache compartilhado"""
    if not analysis_cache:
        return {
            'cache_size': 0,
            'cache_timestamp': None,
            'cache_age_seconds': 0,
            'total_users_affected': 0
        }
    
    total_users = sum(len(data['user_ids']) for data in analysis_cache.values())
    cache_age = (datetime.now() - cache_timestamp).total_seconds() if cache_timestamp else 0
    
    return {
        'cache_size': len(analysis_cache),
        'cache_timestamp': cache_timestamp,
        'cache_age_seconds': cache_age,
        'total_users_affected': total_users,
        'stocks_analysis': {
            stock: {
                'users_count': len(data['user_ids']),
                'analyzed_at': data['analyzed_at'],
                'rsi': data['analysis']['rsi'],
                'recommendation': f"{data['analysis']['current_position']}/{data['analysis']['new_position']}"
            }
            for stock, data in analysis_cache.items()
        }
    }

def main():
    """Função principal do bot"""
    logging.info("🤖 Iniciando Trading Bot com sistema de cache otimizado...")
    
    # Inicia servidor de métricas Prometheus
    start_http_server(8000)
    logging.info("📊 Servidor de métricas iniciado na porta 8000")
    
    # Agenda análise a cada hora usando o novo sistema otimizado
    schedule.every().hour.do(analyze_all_stocks)
    logging.info("⏰ Análise otimizada agendada para executar a cada hora")
    
    # Log do status da bolsa na inicialização
    market_status = "aberta" if is_market_open() else "fechada"
    current_time = datetime.now().strftime("%H:%M")
    logging.info(f"📈 Status da bolsa: {market_status} (horário atual: {current_time})")
    
    # Executa análise inicial otimizada
    logging.info("🚀 Executando análise inicial com sistema otimizado...")
    analyze_all_stocks()
    
    # Loop principal
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
        except KeyboardInterrupt:
            logging.info("🛑 Bot interrompido pelo usuário")
            break
        except Exception as e:
            logging.error(f"❌ Erro no loop principal: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main()