# Trading Bot

Sistema de análise de ações brasileiras com múltiplos provedores de dados.

## 🚀 Início Rápido

### Configuração das Chaves de API

O sistema utiliza múltiplos provedores de dados para garantir robustez. Configure suas chaves de API no arquivo `.env`:

1. **Copie o arquivo de exemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Edite o arquivo `.env` com suas chaves:**
   ```bash
   # Chaves de API para provedores de dados financeiros

   # HG Finance API Key (Recomendado)
   # Obtenha em: https://hgbrasil.com/status/finance
   HG_FINANCE_API_KEY=sua_chave_hg_finance_aqui

   # BrAPI Key (Recomendado)
   # Obtenha em: https://brapi.dev/
   BRAPI_API_KEY=sua_chave_brapi_aqui

   # Alpha Vantage API Key (Opcional)
   # Obtenha em: https://www.alphavantage.co/support/#api-key
   ALPHA_VANTAGE_API_KEY=sua_chave_alpha_vantage_aqui

   # Quandl API Key (Opcional)
   # Obtenha em: https://www.quandl.com/account/api
   QUANDL_API_KEY=sua_chave_quandl_aqui
   ```

### Provedores de Dados

O sistema utiliza os seguintes provedores em ordem de prioridade:

1. **🥇 MFinance** - Gratuito, dados reais brasileiros
2. **🥈 HG Finance** - Com chave de API, dados brasileiros
3. **🥉 BrAPI** - Com chave de API, dados históricos completos
4. **🏅 Yahoo Finance** - Gratuito (limitações no Docker)
5. **🏅 InvestPy** - Gratuito (rate limiting)
6. **🏅 Alpha Vantage** - Requer chave e plano premium
7. **🏅 Quandl** - Requer chave para uso ilimitado
8. **🏅 Smart Simulated** - Fallback inteligente

### Executar o Sistema

```bash
# Construir e executar
docker-compose up -d

# Verificar status dos provedores
curl http://localhost:8000/api/system/data-providers/status

# Testar análise
curl http://localhost:8000/api/acoes/PETR4/analise
```

### Endpoints da API

- **Frontend**: http://localhost:3000
- **API REST**: http://localhost:8000
- **Grafana**: http://localhost:3030
- **Prometheus**: http://localhost:9090

### Monitoramento

- **Status dos Provedores**: `GET /api/system/data-providers/status`
- **Teste de Conectividade**: `GET /api/system/data-providers/test`
- **Estatísticas de Uso**: `GET /api/system/data-providers/stats`

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
trading-bot/
├── src/
│   ├── backend/          # API e lógica de negócio
│   │   ├── api.py       # Endpoints REST
│   │   ├── analyzer.py  # Análise técnica
│   │   ├── data_providers.py  # Provedores de dados
│   │   └── config.py    # Configurações
│   └── frontend/        # Interface React
├── docker-compose.yml   # Orquestração de containers
├── .env                 # Variáveis de ambiente (não commitado)
└── .env.example        # Exemplo de configuração
```

### Segurança

- ✅ Arquivo `.env` está no `.gitignore`
- ✅ Chaves de API não são expostas no código
- ✅ Variáveis de ambiente isoladas por container

## 📊 Funcionalidades

- ✅ Análise técnica (RSI, MACD, Médias Móveis)
- ✅ Múltiplos provedores de dados com fallback
- ✅ Interface web responsiva
- ✅ Monitoramento com Grafana/Prometheus
- ✅ Logs centralizados com Loki
- ✅ Dados reais e simulados inteligentes

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Erro "connection refused"**: Verifique se os containers estão rodando
2. **Dados simulados**: Configure as chaves de API no arquivo `.env`
3. **Rate limiting**: As APIs têm limites, aguarde ou use chave premium

### Verificar Configuração

```bash
# Verificar variáveis de ambiente
docker exec trading-api env | grep API_KEY

# Verificar logs
docker logs trading-api --tail 20

# Testar provedores individualmente
curl http://localhost:8000/api/system/data-providers/test?symbol=PETR4
``` 