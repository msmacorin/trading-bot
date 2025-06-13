import schedule
import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import yfinance as yf
import pandas as pd
import numpy as np
from database import SessionLocal, Acao, Carteira
from analyzer import analyze_stock
from notifier import send_email_notification

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
RECOMMENDATIONS_COUNTER = Counter('trading_recommendations_total', 'Total de recomendações', ['action', 'stock'])
ANALYSIS_DURATION = Histogram('analysis_duration_seconds', 'Duração da análise em segundos')
RSI_GAUGE = Gauge('stock_rsi', 'RSI da ação', ['stock'])
MACD_GAUGE = Gauge('stock_macd', 'MACD da ação', ['stock'])
PRICE_GAUGE = Gauge('stock_price', 'Preço atual da ação', ['stock'])
TREND_GAUGE = Gauge('stock_trend', 'Tendência da ação (1=UP, 0=DOWN)', ['stock'])
EMAIL_NOTIFICATIONS = Counter('email_notifications_total', 'Total de notificações por email enviadas')
ANALYSIS_ERRORS = Counter('analysis_errors_total', 'Total de erros na análise', ['stock'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def analyze_all_stocks():
    """Analisa todas as ações cadastradas e envia notificações"""
    logging.info("🔄 Iniciando análise de todas as ações...")
    
    db = SessionLocal()
    try:
        # Busca todas as ações ativas
        stocks = db.query(Acao).filter(Acao.ativo == True).all()
        logging.info(f"📊 Analisando {len(stocks)} ações...")
        
        for stock in stocks:
            try:
                start_time = time.time()
                
                # Realiza a análise
                analysis = analyze_stock(stock.codigo)
                
                # Registra métricas
                duration = time.time() - start_time
                ANALYSIS_DURATION.observe(duration)
                
                RSI_GAUGE.labels(stock=stock.codigo).set(analysis['rsi'])
                MACD_GAUGE.labels(stock=stock.codigo).set(analysis['macd'])
                PRICE_GAUGE.labels(stock=stock.codigo).set(analysis['price'])
                TREND_GAUGE.labels(stock=stock.codigo).set(1 if analysis['trend'] == 'UP' else 0)
                
                # Verifica se há posição na carteira
                portfolio_position = db.query(Carteira).filter(Carteira.codigo == stock.codigo).first()
                
                # Lógica de notificação
                if portfolio_position:
                    # Tem a ação na carteira
                    if analysis['current_position'] == 'SELL':
                        RECOMMENDATIONS_COUNTER.labels(action='SELL', stock=stock.codigo).inc()
                        send_sell_notification(stock.codigo, analysis, portfolio_position)
                else:
                    # Não tem a ação na carteira
                    if analysis['new_position'] == 'BUY':
                        RECOMMENDATIONS_COUNTER.labels(action='BUY', stock=stock.codigo).inc()
                        send_buy_notification(stock.codigo, analysis)
                
                logging.info(f"✅ {stock.codigo}: {analysis['current_position']}/{analysis['new_position']} - RSI: {analysis['rsi']:.2f}, MACD: {analysis['macd']:.2f}")
                
            except Exception as e:
                ANALYSIS_ERRORS.labels(stock=stock.codigo).inc()
                logging.error(f"❌ Erro ao analisar {stock.codigo}: {str(e)}")
        
        logging.info("🎯 Análise concluída!")
        
    except Exception as e:
        logging.error(f"❌ Erro geral na análise: {str(e)}")
    finally:
        db.close()

def send_buy_notification(stock_code: str, analysis: dict):
    """Envia notificação de compra"""
    subject = f"🚀 SINAL DE COMPRA: {stock_code}"
    body = f"""
    <h2>📈 Sinal de Compra Detectado!</h2>
    
    <h3>🎯 Ação: {stock_code}</h3>
    
    <h4>💰 Informações de Preço:</h4>
    <ul>
        <li><strong>Preço Atual:</strong> R$ {analysis['price']:.2f}</li>
        <li><strong>Variação:</strong> {analysis['profit_pct']:.2f}%</li>
        <li><strong>Stop Loss Sugerido:</strong> R$ {analysis['stop_loss']:.2f}</li>
        <li><strong>Take Profit Sugerido:</strong> R$ {analysis['take_profit']:.2f}</li>
    </ul>
    
    <h4>📊 Indicadores Técnicos:</h4>
    <ul>
        <li><strong>RSI:</strong> {analysis['rsi']:.2f}</li>
        <li><strong>MACD:</strong> {analysis['macd']:.2f}</li>
        <li><strong>Tendência:</strong> {analysis['trend']}</li>
    </ul>
    
    <h4>🔍 Condições Identificadas:</h4>
    <ul>
        {''.join([f'<li>{condition}</li>' for condition in analysis['conditions']])}
    </ul>
    
    <p><em>⚠️ Esta é uma análise automatizada. Sempre faça sua própria análise antes de investir.</em></p>
    """
    
    try:
        send_email_notification(subject, body)
        EMAIL_NOTIFICATIONS.inc()
        logging.info(f"📧 Notificação de compra enviada para {stock_code}")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar notificação de compra para {stock_code}: {str(e)}")

def send_sell_notification(stock_code: str, analysis: dict, position: Carteira):
    """Envia notificação de venda"""
    # Calcula lucro/prejuízo
    current_value = position.quantidade * analysis['price']
    invested_value = position.quantidade * position.preco_medio
    profit_loss = current_value - invested_value
    profit_loss_pct = (profit_loss / invested_value) * 100
    
    subject = f"📉 SINAL DE VENDA: {stock_code}"
    body = f"""
    <h2>📉 Sinal de Venda Detectado!</h2>
    
    <h3>🎯 Ação: {stock_code}</h3>
    
    <h4>💰 Sua Posição:</h4>
    <ul>
        <li><strong>Quantidade:</strong> {position.quantidade} ações</li>
        <li><strong>Preço Médio:</strong> R$ {position.preco_medio:.2f}</li>
        <li><strong>Preço Atual:</strong> R$ {analysis['price']:.2f}</li>
        <li><strong>Valor Investido:</strong> R$ {invested_value:.2f}</li>
        <li><strong>Valor Atual:</strong> R$ {current_value:.2f}</li>
        <li><strong>Resultado:</strong> R$ {profit_loss:.2f} ({profit_loss_pct:+.2f}%)</li>
    </ul>
    
    <h4>📊 Indicadores Técnicos:</h4>
    <ul>
        <li><strong>RSI:</strong> {analysis['rsi']:.2f}</li>
        <li><strong>MACD:</strong> {analysis['macd']:.2f}</li>
        <li><strong>Tendência:</strong> {analysis['trend']}</li>
    </ul>
    
    <h4>🔍 Condições Identificadas:</h4>
    <ul>
        {''.join([f'<li>{condition}</li>' for condition in analysis['conditions']])}
    </ul>
    
    <p><em>⚠️ Esta é uma análise automatizada. Sempre faça sua própria análise antes de investir.</em></p>
    """
    
    try:
        send_email_notification(subject, body)
        EMAIL_NOTIFICATIONS.inc()
        logging.info(f"📧 Notificação de venda enviada para {stock_code}")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar notificação de venda para {stock_code}: {str(e)}")

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