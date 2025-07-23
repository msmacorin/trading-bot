import sys
from backend.data_providers import BrApiProvider, YahooFinanceProvider, MFinanceProvider

# Argumentos de linha de comando
symbol = sys.argv[1] if len(sys.argv) > 1 else "PETR4"
provider_key = sys.argv[2].lower() if len(sys.argv) > 2 else "brapi"

# Mapeamento simplificado
providers = {
    "brapi": BrApiProvider,
    "yahoo": YahooFinanceProvider,
    "mfinance": MFinanceProvider,
}

if provider_key not in providers:
    print(f"Provider '{provider_key}' não suportado. Use um destes: {list(providers.keys())}")
    sys.exit(1)

provider = providers[provider_key]()
df = provider.get_historical_data(symbol, days=30)

print(df)
if df is not None and not df.empty:
    print("Sucesso! Últimos preços:")
    print(df[['Close']].tail())
else:
    print("Nenhum dado retornado.")