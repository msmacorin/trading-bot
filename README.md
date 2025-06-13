# 🤖 Trading Bot

Sistema completo de trading automatizado com análise técnica, monitoramento e interface web.

## 🚀 Funcionalidades

- **Análise Técnica**: RSI, MACD, tendências e recomendações de compra/venda
- **Monitoramento**: Prometheus + Grafana para métricas em tempo real
- **Notificações**: Email automático para sinais de trading
- **Interface Web**: React para gerenciar ações e carteira
- **Containerização**: Docker para fácil deploy e gerenciamento

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trading Web   │    │   Trading API   │    │   Trading Bot   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Python)      │
│   Porta 3000    │    │   Porta 8001    │    │   Porta 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Prometheus    │
                    │   Porta 9090    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Grafana     │
                    │   Porta 3030    │
                    └─────────────────┘
```

## 🛠️ Tecnologias

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: React, TypeScript, CSS
- **Banco de Dados**: SQLite
- **Monitoramento**: Prometheus, Grafana, Loki
- **Containerização**: Docker, Docker Compose
- **Análise Técnica**: Pandas, NumPy, yfinance

## 📦 Instalação e Uso

### Pré-requisitos

- Docker e Docker Compose
- Git

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd trading-bot
```

### 2. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Configurações de Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-de-app

# Configurações do Grafana
GRAFANA_PASSWORD=admin

# Configurações do Trading Bot
ANALYSIS_INTERVAL=3600  # 1 hora em segundos
```

### 3. Inicie todos os serviços

```bash
docker-compose up -d
```

### 4. Acesse as interfaces

- **Frontend Web**: http://localhost:3000
- **API REST**: http://localhost:8001/docs
- **Grafana**: http://localhost:3030 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🎯 Como Usar

### Interface Web (React)

1. **Acesse**: http://localhost:3000
2. **Menu "Em Análise"**:
   - Visualize ações sendo monitoradas
   - Adicione novas ações para análise
   - Ative/desative análises
   - Remova ações do monitoramento

3. **Menu "Carteira"** (em desenvolvimento):
   - Gerencie suas posições
   - Configure stop loss e take profit
   - Acompanhe performance

### API REST

Documentação completa: http://localhost:8001/docs

**Endpoints principais**:
- `GET /acoes/` - Lista todas as ações
- `POST /acoes/` - Adiciona nova ação
- `PATCH /acoes/{codigo}/ativar` - Ativa análise
- `PATCH /acoes/{codigo}/desativar` - Desativa análise
- `DELETE /acoes/{codigo}` - Remove ação
- `GET /acoes/{codigo}/analise` - Análise técnica
- `GET /carteira/` - Lista carteira
- `POST /carteira/` - Adiciona posição

### Monitoramento (Grafana)

1. **Acesse**: http://localhost:3030
2. **Login**: admin/admin
3. **Dashboard**: "Trading Bot Metrics"
   - Recomendações por hora
   - Performance dos indicadores
   - Status das análises
   - Logs e erros

## 📊 Indicadores Técnicos

O bot analisa:

- **RSI (Índice de Força Relativa)**: Sobrecompra/sobrevenda
- **MACD**: Convergência/divergência de médias móveis
- **Tendência**: Média móvel de 20 períodos
- **Stop Loss**: -3% do preço atual
- **Take Profit**: +5% do preço atual

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
trading-bot/
├── src/
│   ├── api/                    # API FastAPI
│   │   ├── api.py             # Endpoints da API
│   │   └── run_api.py         # Script de execução
│   ├── backend/               # Bot principal
│   │   ├── app.py             # Aplicação principal
│   │   ├── analyzer.py        # Análise técnica
│   │   ├── database.py        # Modelos SQLAlchemy
│   │   ├── notifier.py        # Sistema de notificações
│   │   └── monitoring/        # Configurações Prometheus/Grafana
│   └── frontend/              # Interface web
│       └── trading-web/       # Aplicação React
│           ├── src/
│           │   ├── components/    # Componentes React
│           │   ├── pages/         # Páginas
│           │   ├── services/      # Serviços de API
│           │   └── types/         # Tipos TypeScript
│           ├── Dockerfile         # Container do frontend
│           └── nginx.conf         # Configuração nginx
├── config/                    # Arquivos de configuração
├── logs/                      # Logs do sistema
├── docker-compose.yml         # Orquestração Docker
└── Dockerfile                 # Container do backend
```

### Comandos Úteis

```bash
# Ver logs de um serviço específico
docker-compose logs trading-bot
docker-compose logs trading-api
docker-compose logs trading-web

# Reconstruir um serviço
docker-compose build trading-api
docker-compose build trading-web

# Parar todos os serviços
docker-compose down

# Ver status dos containers
docker-compose ps

# Acessar shell de um container
docker-compose exec trading-api bash
docker-compose exec trading-web sh

# Desenvolvimento local do frontend
cd src/frontend/trading-web
npm install
npm start

# Desenvolvimento local do backend
cd src/backend
python app.py
```

## 📈 Métricas Monitoradas

- **Trading Metrics**:
  - Recomendações por hora (BUY/SELL/HOLD)
  - Duração das análises
  - Erros de análise

- **Indicadores Técnicos**:
  - Valores de RSI
  - Valores de MACD
  - Tendências identificadas

- **Sistema**:
  - Notificações enviadas
  - Status dos serviços
  - Logs de erro

## 🔒 Segurança

- **Email**: Use senhas de aplicativo (não senha principal)
- **Grafana**: Altere a senha padrão
- **API**: Configure CORS adequadamente para produção
- **Docker**: Use secrets para senhas em produção

## 🚨 Troubleshooting

### Problemas Comuns

1. **Container não inicia**:
   ```bash
   docker-compose logs <nome-do-servico>
   ```

2. **API não responde**:
   - Verifique se o trading-api está rodando
   - Teste: `curl http://localhost:8001/acoes/`

3. **Frontend não carrega**:
   - Verifique se o trading-web está rodando
   - Teste: `curl http://localhost:3000`

4. **Grafana sem dados**:
   - Verifique se Prometheus está coletando métricas
   - Teste: `curl http://localhost:9090/api/v1/targets`

### Logs Importantes

```bash
# Logs do bot principal
docker-compose logs -f trading-bot

# Logs da API
docker-compose logs -f trading-api

# Logs do frontend
docker-compose logs -f trading-web

# Logs do Prometheus
docker-compose logs -f prometheus
```

## 📝 Licença

Este projeto é para fins educacionais. Use por sua conta e risco.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

**⚠️ Aviso**: Este bot é para fins educacionais. Trading envolve riscos significativos. Sempre faça sua própria análise antes de investir. 