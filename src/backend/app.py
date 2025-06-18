import schedule
import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import yfinance as yf
import pandas as pd
import numpy as np
from backend.database import SessionLocal, Acao, Carteira, Usuario, get_acoes_ativas, get_carteira
from backend.analyzer import analyze_stock
from backend.notifier import send_email_notification

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def analyze_user_stocks(usuario_id):
    """Analisa todas as ações de um usuário específico"""
    logging.info(f"🔄 Iniciando análise das ações do usuário {usuario_id}...")
    
    db = SessionLocal()
    try:
        # Busca o usuário
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.ativo == True).first()
        if not usuario:
            logging.warning(f"⚠️ Usuário {usuario_id} não encontrado ou inativo")
            return
        
        # Busca todas as ações ativas do usuário
        stocks = get_acoes_ativas(usuario_id)
        logging.info(f"📊 Analisando {len(stocks)} ações do usuário {usuario.nome}...")
        
        # Listas para armazenar resultados
        buy_signals = []
        sell_signals = []
        all_analyses = []
        errors = []
        
        for stock in stocks:
            try:
                start_time = time.time()
                
                # Realiza a análise
                analysis = analyze_stock(stock.codigo)
                
                # Registra métricas
                duration = time.time() - start_time
                ANALYSIS_DURATION.observe(duration)
                
                RSI_GAUGE.labels(stock=stock.codigo, user_id=usuario_id).set(analysis['rsi'])
                MACD_GAUGE.labels(stock=stock.codigo, user_id=usuario_id).set(analysis['macd'])
                PRICE_GAUGE.labels(stock=stock.codigo, user_id=usuario_id).set(analysis['price'])
                TREND_GAUGE.labels(stock=stock.codigo, user_id=usuario_id).set(1 if analysis['trend'] == 'UP' else 0)
                
                # Adiciona à lista de todas as análises
                all_analyses.append({
                    'stock': stock.codigo,
                    'analysis': analysis
                })
                
                # Verifica se há posição na carteira do usuário
                portfolio_position = db.query(Carteira).filter(
                    Carteira.codigo == stock.codigo, 
                    Carteira.usuario_id == usuario_id
                ).first()
                
                # Lógica de notificação
                if portfolio_position:
                    # Tem a ação na carteira
                    if analysis['current_position'] == 'SELL':
                        RECOMMENDATIONS_COUNTER.labels(action='SELL', stock=stock.codigo, user_id=usuario_id).inc()
                        sell_signals.append({
                            'stock': stock.codigo,
                            'analysis': analysis,
                            'position': portfolio_position
                        })
                else:
                    # Não tem a ação na carteira
                    if analysis['new_position'] == 'BUY':
                        RECOMMENDATIONS_COUNTER.labels(action='BUY', stock=stock.codigo, user_id=usuario_id).inc()
                        buy_signals.append({
                            'stock': stock.codigo,
                            'analysis': analysis
                        })
                
                logging.info(f"✅ {stock.codigo} (Usuário {usuario.nome}): {analysis['current_position']}/{analysis['new_position']} - RSI: {analysis['rsi']:.2f}, MACD: {analysis['macd']:.2f}")
                
            except Exception as e:
                ANALYSIS_ERRORS.labels(stock=stock.codigo, user_id=usuario_id).inc()
                error_msg = f"❌ Erro ao analisar {stock.codigo} (Usuário {usuario.nome}): {str(e)}"
                errors.append(error_msg)
                logging.error(error_msg)
        
        # Envia email com resumo das análises do usuário
        if buy_signals or sell_signals or all_analyses:
            send_user_analysis_summary_email(usuario, buy_signals, sell_signals, all_analyses, errors)
        
        logging.info(f"🎯 Análise do usuário {usuario.nome} concluída!")
        
    except Exception as e:
        logging.error(f"❌ Erro geral na análise do usuário {usuario_id}: {str(e)}")
    finally:
        db.close()

def analyze_all_stocks():
    """Analisa todas as ações de todos os usuários ativos"""
    logging.info("🔄 Iniciando análise de todas as ações de todos os usuários...")
    
    db = SessionLocal()
    try:
        # Busca todos os usuários ativos
        usuarios = db.query(Usuario).filter(Usuario.ativo == True).all()
        logging.info(f"👥 Analisando ações de {len(usuarios)} usuários...")
        
        for usuario in usuarios:
            analyze_user_stocks(usuario.id)
        
        logging.info("🎯 Análise de todos os usuários concluída!")
        
    except Exception as e:
        logging.error(f"❌ Erro geral na análise: {str(e)}")
    finally:
        db.close()

def send_user_analysis_summary_email(usuario, buy_signals, sell_signals, all_analyses, errors):
    """Envia email com resumo das análises de um usuário específico"""
    from datetime import datetime
    
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    subject = f"📊 Relatório de Análise - {usuario.nome} - {current_time}"
    
    # Cabeçalho personalizado
    body = f"""
    <h1>📊 Relatório de Análise de Ações</h1>
    <p><strong>Usuário:</strong> {usuario.nome}</p>
    <p><strong>Email:</strong> {usuario.email}</p>
    <p><strong>Data/Hora:</strong> {current_time}</p>
    <p><strong>Total de ações analisadas:</strong> {len(all_analyses)}</p>
    <hr>
    """
    
    # Sinais de compra
    if buy_signals:
        body += f"""
        <h2>🚀 Sinais de Compra ({len(buy_signals)})</h2>
        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #e8f5e8;">
                <th>Ação</th>
                <th>Preço</th>
                <th>RSI</th>
                <th>MACD</th>
                <th>Tendência</th>
                <th>Stop Loss</th>
                <th>Take Profit</th>
            </tr>
        """
        
        for signal in buy_signals:
            analysis = signal['analysis']
            body += f"""
            <tr>
                <td><strong>{signal['stock']}</strong></td>
                <td>R$ {analysis['price']:.2f}</td>
                <td>{analysis['rsi']:.2f}</td>
                <td>{analysis['macd']:.4f}</td>
                <td>{analysis['trend']}</td>
                <td>R$ {analysis['stop_loss']:.2f}</td>
                <td>R$ {analysis['take_profit']:.2f}</td>
            </tr>
            """
        
        body += "</table>"
    else:
        body += "<h2>🚀 Sinais de Compra</h2><p>Nenhum sinal de compra detectado.</p>"
    
    # Sinais de venda
    if sell_signals:
        body += f"""
        <h2>📉 Sinais de Venda ({len(sell_signals)})</h2>
        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #ffe8e8;">
                <th>Ação</th>
                <th>Preço Atual</th>
                <th>Preço Médio</th>
                <th>Quantidade</th>
                <th>Resultado</th>
                <th>RSI</th>
                <th>MACD</th>
                <th>Tendência</th>
            </tr>
        """
        
        for signal in sell_signals:
            analysis = signal['analysis']
            position = signal['position']
            
            # Calcula lucro/prejuízo
            current_value = position.quantidade * analysis['price']
            invested_value = position.quantidade * position.preco_medio
            profit_loss = current_value - invested_value
            profit_loss_pct = (profit_loss / invested_value) * 100
            
            body += f"""
            <tr>
                <td><strong>{signal['stock']}</strong></td>
                <td>R$ {analysis['price']:.2f}</td>
                <td>R$ {position.preco_medio:.2f}</td>
                <td>{position.quantidade}</td>
                <td style="color: {'green' if profit_loss >= 0 else 'red'};">
                    R$ {profit_loss:.2f} ({profit_loss_pct:+.2f}%)
                </td>
                <td>{analysis['rsi']:.2f}</td>
                <td>{analysis['macd']:.4f}</td>
                <td>{analysis['trend']}</td>
            </tr>
            """
        
        body += "</table>"
    else:
        body += "<h2>📉 Sinais de Venda</h2><p>Nenhum sinal de venda detectado.</p>"
    
    # Resumo geral
    body += f"""
    <h2>📈 Resumo Geral</h2>
    <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        <tr style="background-color: #f0f0f0;">
            <th>Métrica</th>
            <th>Valor</th>
        </tr>
        <tr>
            <td>Total de ações analisadas</td>
            <td>{len(all_analyses)}</td>
        </tr>
        <tr>
            <td>Sinais de compra</td>
            <td>{len(buy_signals)}</td>
        </tr>
        <tr>
            <td>Sinais de venda</td>
            <td>{len(sell_signals)}</td>
        </tr>
        <tr>
            <td>Erros</td>
            <td>{len(errors)}</td>
        </tr>
    </table>
    """
    
    # Top 10 ações por RSI (sobrevenda)
    if all_analyses:
        oversold = sorted(all_analyses, key=lambda x: x['analysis']['rsi'])[:10]
        body += """
        <h2>🔍 Top 10 - Menor RSI (Sobrevenda)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #e8f5e8;">
                <th>Posição</th>
                <th>Ação</th>
                <th>RSI</th>
                <th>Preço</th>
                <th>Tendência</th>
            </tr>
        """
        
        for i, item in enumerate(oversold, 1):
            analysis = item['analysis']
            body += f"""
            <tr>
                <td>{i}º</td>
                <td><strong>{item['stock']}</strong></td>
                <td>{analysis['rsi']:.2f}</td>
                <td>R$ {analysis['price']:.2f}</td>
                <td>{analysis['trend']}</td>
            </tr>
            """
        
        body += "</table>"
        
        # Top 10 ações por RSI (sobrecompra)
        overbought = sorted(all_analyses, key=lambda x: x['analysis']['rsi'], reverse=True)[:10]
        body += """
        <h2>🔍 Top 10 - Maior RSI (Sobrecompra)</h2>
        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #ffe8e8;">
                <th>Posição</th>
                <th>Ação</th>
                <th>RSI</th>
                <th>Preço</th>
                <th>Tendência</th>
            </tr>
        """
        
        for i, item in enumerate(overbought, 1):
            analysis = item['analysis']
            body += f"""
            <tr>
                <td>{i}º</td>
                <td><strong>{item['stock']}</strong></td>
                <td>{analysis['rsi']:.2f}</td>
                <td>R$ {analysis['price']:.2f}</td>
                <td>{analysis['trend']}</td>
            </tr>
            """
        
        body += "</table>"
    
    # Erros (se houver)
    if errors:
        body += f"""
        <h2>❌ Erros Encontrados ({len(errors)})</h2>
        <ul>
        """
        for error in errors:
            body += f"<li>{error}</li>"
        body += "</ul>"
    
    # Rodapé
    body += """
    <hr>
    <p><em>⚠️ Esta é uma análise automatizada. Sempre faça sua própria análise antes de investir.</em></p>
    <p><em>📊 Relatório gerado automaticamente pelo Trading Bot</em></p>
    """
    
    try:
        send_email_notification(subject, body)
        EMAIL_NOTIFICATIONS.labels(user_id=usuario.id).inc()
        logging.info(f"📧 Relatório de análise enviado para {usuario.nome} - {len(buy_signals)} compras, {len(sell_signals)} vendas, {len(all_analyses)} análises")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar relatório de análise para {usuario.nome}: {str(e)}")

def main():
    """Função principal do bot"""
    logging.info("🤖 Iniciando Trading Bot...")
    
    # Inicia servidor de métricas Prometheus
    start_http_server(8000)
    logging.info("📊 Servidor de métricas iniciado na porta 8000")
    
    # Agenda análise a cada hora
    schedule.every().hour.do(analyze_all_stocks)
    logging.info("⏰ Análise agendada para executar a cada hora")
    
    # Executa análise inicial
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