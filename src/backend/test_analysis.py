from analyzer import analyze_stock

# Teste com uma ação específica
ticker = "PRIO3.SA"
result = analyze_stock(ticker)

print(f"\nAnálise Detalhada para {ticker}:")
print("\nRecomendações:")
print(f"- Para quem já tem a ação: {result['current_position']}")
print(f"- Para quem está avaliando comprar: {result['new_position']}")

print(f"\nPreço Atual: R$ {result['price']:.2f}")
print(f"Stop Loss: R$ {result['stop_loss']:.2f}")
print(f"Take Profit: R$ {result['take_profit']:.2f}")
print(f"Variação no Período: {result['profit_pct']:.2f}%")

print(f"\nIndicadores Técnicos:")
print(f"RSI: {result['rsi']:.2f}")
print(f"MACD: {result['macd']:.2f}")
print(f"Tendência: {result['trend']}")

print("\nCondições Identificadas:")
for condition in result['conditions']:
    print(f"- {condition}") 