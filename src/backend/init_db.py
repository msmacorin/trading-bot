import logging

from database import init_db, criar_usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Inicializa o banco de dados e cria um usuário admin"""
    try:
        # Inicializa o banco de dados
        logger.info("🔄 Inicializando banco de dados...")
        init_db()
        logger.info("✅ Banco de dados inicializado com sucesso!")

        # Cria usuário admin
        logger.info("👤 Criando usuário admin...")
        usuario, error = criar_usuario(
            email="admin@tradingbot.com",
            nome="Administrador",
            senha="admin123"  # Em produção, use uma senha mais segura
        )

        if error:
            if "Email já cadastrado" in error:
                logger.info("ℹ️ Usuário admin já existe")
            else:
                logger.error(f"❌ Erro ao criar usuário admin: {error}")
        else:
            logger.info("✅ Usuário admin criado com sucesso!")

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        raise

if __name__ == "__main__":
    main() 