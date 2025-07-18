"""
Módulo de análise técnica de ações
Usa múltiplos provedores de dados com fallback automático
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from .data_providers import data_manager, create_fallback_data

# Configurar logging
logger = logging.getLogger(__name__)

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
    Analisa uma ação usando indicadores técnicos com múltiplos provedores
    
    Args:
        stock_code: Código da ação (ex: PETR4.SA ou PETR4 ou PETR4F)
    
    Returns:
        Dict com análise completa incluindo recomendações
    """
    try:
        from src.backend.utils import normalize_stock_code, validate_stock_code, get_stock_display_info
        
        # Normaliza o código da ação
        try:
            normalized_code = normalize_stock_code(stock_code)
            stock_info = validate_stock_code(stock_code)
            display_info = get_stock_display_info(stock_code)
        except ValueError as e:
            logger.error(f"Código inválido {stock_code}: {e}")
            raise ValueError(f"Código de ação inválido: {e}")
        
        logger.info(f"Iniciando análise de {stock_info['display_name']} (código normalizado: {normalized_code})")
        
        # Tenta obter dados históricos usando múltiplos provedores
        # Para ações fracionárias, tenta primeiro o código fracionário, depois o código base
        if stock_info['is_fractional']:
            hist = data_manager.get_historical_data(normalized_code, days=30)
            if hist is None or hist.empty:
                # Se não encontrar dados para a fracionária, tenta a ação normal
                base_code = stock_info['base_code']
                logger.info(f"Dados não encontrados para {normalized_code}, tentando código base {base_code}")
                hist = data_manager.get_historical_data(base_code, days=30)
        else:
            hist = data_manager.get_historical_data(normalized_code, days=30)
        
        # Se todos os provedores falharam, usa dados simulados
        if hist is None or hist.empty:
            logger.warning(f"Todos os provedores falharam para {normalized_code}, usando dados simulados")
            hist = create_fallback_data(normalized_code)
            using_simulated_data = True
        else:
            using_simulated_data = False
        
        # Verifica se temos dados suficientes
        if len(hist) < 5:
            raise ValueError(f"Dados insuficientes para análise de {normalized_code}")
        
        # Preço atual (último preço de fechamento)
        current_price = hist['Close'].iloc[-1]
        
        # Calcula indicadores técnicos
        rsi = calculate_rsi(hist['Close'])
        macd = calculate_macd(hist['Close'])
        
        # Tendência baseada em média móvel
        if len(hist) >= 20:
            ma_period = 20
        elif len(hist) >= 10:
            ma_period = 10
        else:
            ma_period = min(5, len(hist))
        
        ma = hist['Close'].rolling(window=ma_period).mean().iloc[-1]
        trend = "UP" if current_price > ma else "DOWN"
        
        # Variação percentual no período
        first_price = hist['Close'].iloc[0]
        profit_pct = ((current_price - first_price) / first_price) * 100
        
        # Stop loss e take profit
        stop_loss = current_price * 0.97  # -3%
        take_profit = current_price * 1.05  # +5%
        
        # Análise de condições de mercado
        conditions = []
        
        # Adiciona informação sobre fonte dos dados e tipo de ação
        if stock_info['is_fractional']:
            conditions.append(f"📊 Ação fracionária ({display_info['display_code']})")
        
        if using_simulated_data:
            conditions.append("⚠️ Usando dados simulados (APIs indisponíveis)")
        else:
            conditions.append("✅ Dados obtidos de provedor externo")
            
        if not stock_info['is_known']:
            conditions.append("⚠️ Código não reconhecido na base de dados")
        
        # Análise RSI
        if rsi < 30:
            conditions.append(f"📉 RSI indica sobrevenda ({rsi:.1f})")
        elif rsi > 70:
            conditions.append(f"📈 RSI indica sobrecompra ({rsi:.1f})")
        else:
            conditions.append(f"📊 RSI neutro ({rsi:.1f})")
        
        # Análise MACD
        if macd > 0:
            conditions.append("🟢 MACD positivo (momentum de alta)")
        else:
            conditions.append("🔴 MACD negativo (momentum de baixa)")
        
        # Análise de tendência
        if trend == "UP":
            conditions.append(f"⬆️ Preço acima da média móvel ({ma_period} períodos)")
        else:
            conditions.append(f"⬇️ Preço abaixo da média móvel ({ma_period} períodos)")
        
        # Lógica de recomendações (VERSÃO CORRIGIDA E CLARA)
        current_position = "HOLD"
        new_position = "WAIT"
        
        # PRIMEIRO: Analisa sinais de VENDA para quem já tem a ação
        if rsi > 85:
            current_position = "SELL"
            conditions.append("🚨 Sinal de venda - sobrecompra extrema (RSI > 85)")
        elif rsi > 80 and macd < -0.1:
            current_position = "SELL"
            conditions.append("🚨 Sinal de venda - sobrecompra com momentum negativo")
        elif macd < -0.25 and trend == "DOWN":
            current_position = "SELL"
            conditions.append("🚨 Sinal de venda - momentum muito negativo")
        elif rsi < 45 and macd > 0:
            current_position = "HOLD"
            conditions.append("💎 Manter posição - possível reversão")
        
        # SEGUNDO: Analisa sinais de COMPRA para quem não tem a ação
        # Resetar new_position para garantir lógica limpa
        new_position = "WAIT"
        
        # BUY - Sinais FORTES de compra
        buy_signal = False
        if rsi < 35:
            buy_signal = True
            conditions.append("🎯 BUY: RSI muito baixo (< 35)")
        elif rsi < 45 and macd > 0 and trend == "UP":
            buy_signal = True  
            conditions.append("🎯 BUY: RSI baixo + MACD positivo + tendência alta")
        elif rsi < 50 and macd > 0.05 and trend == "UP":
            buy_signal = True
            conditions.append("🎯 BUY: Condições favoráveis múltiplas")
        elif macd > 0.1 and trend == "UP":
            buy_signal = True
            conditions.append("🎯 BUY: MACD muito positivo + tendência alta")
        
        if buy_signal:
            new_position = "BUY"
        
        # WATCH - Sinais BONS de compra (só se não for BUY)
        elif trend == "UP" and macd > 0.02:
            new_position = "WATCH"
            conditions.append("👀 WATCH: Tendência positiva + MACD bom")
        elif rsi < 60 and trend == "UP" and macd > -0.05:
            new_position = "WATCH"
            conditions.append("👀 WATCH: RSI moderado + tendência positiva")
        elif rsi < 55 and trend == "UP":
            new_position = "WATCH"
            conditions.append("👀 WATCH: RSI bom + tendência positiva")
        elif rsi < 70 and macd > 0.08:
            new_position = "WATCH"
            conditions.append("👀 WATCH: MACD forte")
        
        # CONSIDER - Sinais RAZOÁVEIS (só se não for BUY nem WATCH)
        elif rsi < 70 and trend == "UP":
            new_position = "CONSIDER"
            conditions.append("🤔 CONSIDER: Tendência positiva")
        elif rsi < 65 and macd > -0.02:
            new_position = "CONSIDER"
            conditions.append("🤔 CONSIDER: RSI moderado + MACD neutro")
        elif rsi < 75 and macd > 0.03:
            new_position = "CONSIDER"
            conditions.append("🤔 CONSIDER: Sinais mistos positivos")
        
        # Adiciona informações sobre volume se disponível
        if 'Volume' in hist.columns:
            avg_volume = hist['Volume'].tail(5).mean()
            last_volume = hist['Volume'].iloc[-1]
            if last_volume > avg_volume * 1.5:
                conditions.append("📊 Volume acima da média (atividade alta)")
            elif last_volume < avg_volume * 0.5:
                conditions.append("📊 Volume abaixo da média (atividade baixa)")
        
        return {
            "codigo": normalized_code,
            "codigo_original": stock_code,
            "display_name": display_info['display_code'],
            "is_fractional": stock_info['is_fractional'],
            "current_position": current_position,
            "new_position": new_position,
            "price": round(float(current_price), 2),
            "stop_loss": round(float(stop_loss), 2),
            "take_profit": round(float(take_profit), 2),
            "profit_pct": round(float(profit_pct), 2),
            "rsi": round(float(rsi), 2),
            "macd": round(float(macd), 4),
            "trend": trend,
            "conditions": conditions,
            "data_source": "simulated" if using_simulated_data else "external",
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro crítico na análise de {stock_code}: {str(e)}")
        
        # Fallback final com dados mínimos
        try:
            normalized_code = normalize_stock_code(stock_code)
            display_name = stock_code
        except:
            normalized_code = stock_code
            display_name = stock_code
            
        return {
            "codigo": normalized_code,
            "codigo_original": stock_code,
            "display_name": display_name,
            "is_fractional": False,
            "current_position": "HOLD",
            "new_position": "WAIT",
            "price": 25.00,
            "stop_loss": 24.25,
            "take_profit": 26.25,
            "profit_pct": 0.0,
            "rsi": 50.0,
            "macd": 0.0,
            "trend": "NEUTRAL",
            "conditions": [
                "❌ Erro na análise técnica",
                f"🔧 Detalhes: {str(e)}",
                "📋 Dados de fallback apresentados"
            ],
            "data_source": "fallback",
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }

def test_data_providers(symbols: List[str] = None) -> Dict:
    """
    Testa todos os provedores de dados disponíveis
    
    Args:
        symbols: Lista de símbolos para teste
        
    Returns:
        Relatório de testes dos provedores
    """
    if symbols is None:
        symbols = ['PETR4', 'VALE3', 'ITUB4']
    
    logger.info("Testando provedores de dados...")
    results = data_manager.test_providers(symbols)
    
    # Adiciona resumo
    total_providers = len(results)
    working_providers = sum(1 for p in results.values() 
                           if any(t['success'] for t in p['tests'].values()))
    
    results['summary'] = {
        'total_providers': total_providers,
        'working_providers': working_providers,
        'availability_rate': working_providers / total_providers if total_providers > 0 else 0
    }
    
    return results

if __name__ == "__main__":
    # Testa o sistema com algumas ações
    test_stocks = ["PETR4", "VALE3", "ITUB4"]
    
    print("=== Teste do Sistema de Análise ===\n")
    
    # Testa provedores
    print("1. Testando provedores de dados...")
    provider_results = test_data_providers()
    print(f"Provedores funcionais: {provider_results['summary']['working_providers']}/{provider_results['summary']['total_providers']}")
    print()
    
    # Testa análises
    print("2. Testando análises...")
    for stock in test_stocks:
        try:
            print(f"\n=== Análise de {stock} ===")
            result = analyze_stock(stock)
            
            print(f"Preço: R$ {result['price']}")
            print(f"Recomendação (posição atual): {result['current_position']}")
            print(f"Recomendação (nova posição): {result['new_position']}")
            print(f"RSI: {result['rsi']}")
            print(f"Fonte dos dados: {result['data_source']}")
            print(f"Condições: {result['conditions'][:3]}")  # Primeiras 3 condições
            
        except Exception as e:
            print(f"Erro ao analisar {stock}: {e}")