import uvicorn
import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    print("🚀 Iniciando API do Trading Bot...")
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8001,  # Porta diferente do Prometheus (8000)
        reload=True
    ) 