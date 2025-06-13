import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List
import logging

def calculate_rsi(data: pd.Series, period: int = 14) -> float:
    """Calcula o RSI (Relative Strength Index)"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
    """Calcula o MACD (Moving Average Convergence Divergence)"""
    ema_fast = data.ewm(span=fast).mean()
    ema_slow = data.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    return macd_line.iloc[-1] - signal_line.iloc[-1]

def analyze_stock(stock_code: str) -> Dict:
    """
    Analisa uma ação usando indicadores técnicos
    
    Args:
        stock_code: Código da ação (ex: PETR4.SA)
    
    Returns:
        Dict com análise completa incluindo recomendações
    """
    try:
        # Busca dados históricos
        stock = yf.Ticker(stock_code)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            raise ValueError(f"Não foi possível obter dados para {stock_code}")
        
        # Preço atual
        current_price = hist['Close'].iloc[-1]
        
        # Calcula indicadores
        rsi = calculate_rsi(hist['Close'])
        macd = calculate_macd(hist['Close'])
        
        # Tendência (média móvel de 20 períodos)
        ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        trend = "UP" if current_price > ma_20 else "DOWN"
        
        # Variação percentual no período
        first_price = hist['Close'].iloc[0]
        profit_pct = ((current_price - first_price) / first_price) * 100
        
        # Stop loss e take profit
        stop_loss = current_price * 0.97  # -3%
        take_profit = current_price * 1.05  # +5%
        
        # Lógica de recomendações
        conditions = []
        
        # RSI
        if rsi < 30:
            conditions.append("RSI indica sobrevenda (< 30)")
        elif rsi > 70:
            conditions.append("RSI indica sobrecompra (> 70)")
        
        # MACD
        if macd > 0:
            conditions.append("MACD positivo (momentum de alta)")
        else:
            conditions.append("MACD negativo (momentum de baixa)")
        
        # Tendência
        if trend == "UP":
            conditions.append("Preço acima da média móvel de 20 períodos")
        else:
            conditions.append("Preço abaixo da média móvel de 20 períodos")
        
        # Recomendações
        current_position = "HOLD"
        new_position = "WAIT"
        
        # Para quem já tem a ação
        if rsi > 70 or (macd < 0 and trend == "DOWN"):
            current_position = "SELL"
            conditions.append("Sinal de venda para posições existentes")
        
        # Para quem não tem a ação
        if rsi < 30 and macd > 0 and trend == "UP":
            new_position = "BUY"
            conditions.append("Oportunidade de compra identificada")
        
        return {
            "current_position": current_position,
            "new_position": new_position,
            "price": round(current_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "profit_pct": round(profit_pct, 2),
            "rsi": round(rsi, 2),
            "macd": round(macd, 4),
            "trend": trend,
            "conditions": conditions
        }
        
    except Exception as e:
        logging.error(f"Erro ao analisar {stock_code}: {str(e)}")
        raise ValueError(f"Erro na análise de {stock_code}: {str(e)}")

if __name__ == "__main__":
    # Teste da função
    test_stocks = ["PETR4.SA", "VALE3.SA", "ITUB4.SA"]
    
    for stock in test_stocks:
        try:
            print(f"\n=== Análise de {stock} ===")
            result = analyze_stock(stock)
            for key, value in result.items():
                print(f"{key}: {value}")
        except Exception as e:
            print(f"Erro ao analisar {stock}: {e}")