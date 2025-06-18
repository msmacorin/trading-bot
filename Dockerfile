FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de dependências
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY . .

# Cria diretórios necessários
RUN mkdir -p config logs

# Inicializa o banco de dados
RUN python src/backend/init_db.py

# Expõe as portas necessárias
EXPOSE 8000 8001

# Comando padrão (será sobrescrito pelo docker-compose)
CMD ["python", "src/backend/app.py"]