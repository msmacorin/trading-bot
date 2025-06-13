FROM python:3.10-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY src/ src/
COPY config/ config/
COPY .env .

# Define as variáveis de ambiente padrão (podem ser sobrescritas no docker-compose)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expõe as portas
EXPOSE 8000
EXPOSE 8001

# Executa o bot
CMD ["python", "src/backend/app.py"]