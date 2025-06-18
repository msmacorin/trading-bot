import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import bcrypt

# Configuração do banco de dados
DATABASE_URL = "sqlite:///config/trading.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Usuario(Base):
    """Modelo para a tabela de usuários"""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    senha_hash = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    acoes = relationship("Acao", back_populates="usuario")
    carteira = relationship("Carteira", back_populates="usuario")
    
    def set_senha(self, senha):
        """Hash da senha usando bcrypt"""
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verificar_senha(self, senha):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email})>"

class Acao(Base):
    """Modelo para a tabela de ações monitoradas"""
    __tablename__ = "acoes"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    ativo = Column(Boolean, default=True)  # Para poder desativar sem deletar
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relacionamento
    usuario = relationship("Usuario", back_populates="acoes")
    
    def __repr__(self):
        return f"<Acao(id={self.id}, codigo={self.codigo}, usuario_id={self.usuario_id})>"

class Carteira(Base):
    """Modelo para a tabela da carteira de investimentos"""
    __tablename__ = "carteira"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    quantidade = Column(Integer)
    preco_medio = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relacionamento
    usuario = relationship("Usuario", back_populates="carteira")
    
    def __repr__(self):
        return f"<Carteira(id={self.id}, codigo={self.codigo}, quantidade={self.quantidade}, usuario_id={self.usuario_id})>"

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

def get_acoes_ativas(usuario_id):
    """Retorna todas as ações ativas de um usuário"""
    db = SessionLocal()
    try:
        return db.query(Acao).filter(Acao.ativo == True, Acao.usuario_id == usuario_id).all()
    finally:
        db.close()

def get_carteira(usuario_id):
    """Retorna todas as posições da carteira de um usuário"""
    db = SessionLocal()
    try:
        return db.query(Carteira).filter(Carteira.usuario_id == usuario_id).all()
    finally:
        db.close()

def criar_usuario(email, nome, senha):
    """Cria um novo usuário"""
    db = SessionLocal()
    try:
        # Verifica se o email já existe
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            return None, "Email já cadastrado"
        
        usuario = Usuario(email=email, nome=nome)
        usuario.set_senha(senha)
        
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        
        return usuario, None
    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()

def autenticar_usuario(email, senha):
    """Autentica um usuário"""
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()
        if usuario and usuario.verificar_senha(senha):
            return usuario
        return None
    finally:
        db.close()

def get_usuario_por_id(usuario_id):
    """Retorna um usuário por ID"""
    db = SessionLocal()
    try:
        return db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.ativo == True).first()
    finally:
        db.close()

# Inicializa o banco de dados na importação do módulo
init_db() 