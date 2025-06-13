import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração do banco de dados
DATABASE_URL = "sqlite:///config/trading.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Acao(Base):
    """Modelo para a tabela de ações monitoradas"""
    __tablename__ = "acoes"
    
    codigo = Column(String, primary_key=True, index=True)
    ativo = Column(Boolean, default=True)  # Para poder desativar sem deletar
    
    def __repr__(self):
        return f"<Acao(codigo={self.codigo})>"

class Carteira(Base):
    """Modelo para a tabela da carteira de investimentos"""
    __tablename__ = "carteira"
    
    codigo = Column(String, primary_key=True, index=True)
    quantidade = Column(Integer)
    preco_medio = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    
    def __repr__(self):
        return f"<Carteira(codigo={self.codigo}, quantidade={self.quantidade})>"

def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    # Garante que o diretório config existe
    os.makedirs('config', exist_ok=True)
    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_acoes_ativas():
    """Retorna todas as ações ativas"""
    db = SessionLocal()
    try:
        return db.query(Acao).filter(Acao.ativo == True).all()
    finally:
        db.close()

def get_carteira():
    """Retorna todas as posições da carteira"""
    db = SessionLocal()
    try:
        return db.query(Carteira).all()
    finally:
        db.close()

# Inicializa o banco de dados na importação do módulo
init_db() 