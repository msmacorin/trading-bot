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
    transacoes = relationship("Transacao", back_populates="usuario")
    
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

class Transacao(Base):
    """Modelo para a tabela de transações (vendas executadas)"""
    __tablename__ = "transacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True, nullable=False)
    data_transacao = Column(DateTime, default=datetime.utcnow, nullable=False)
    quantidade_vendida = Column(Integer, nullable=False)
    preco_compra = Column(Float, nullable=False)  # Preço médio de compra original
    preco_venda = Column(Float, nullable=False)   # Preço de venda
    stop_loss_original = Column(Float, default=0.0)
    take_profit_original = Column(Float, default=0.0)
    valor_total = Column(Float, nullable=False)   # quantidade_vendida * preco_venda
    lucro_prejuizo = Column(Float, nullable=False)  # (preco_venda - preco_compra) * quantidade_vendida
    percentual_resultado = Column(Float, nullable=False)  # ((preco_venda - preco_compra) / preco_compra) * 100
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relacionamento
    usuario = relationship("Usuario", back_populates="transacoes")
    
    def __repr__(self):
        return f"<Transacao(id={self.id}, codigo={self.codigo}, quantidade={self.quantidade_vendida}, resultado={self.lucro_prejuizo:.2f})>"

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

def get_acao_by_codigo(codigo: str, usuario_id: int):
    """Busca uma ação por código normalizado"""
    from src.backend.utils import normalize_stock_code
    
    db = SessionLocal()
    try:
        normalized_code = normalize_stock_code(codigo)
        return db.query(Acao).filter(
            Acao.codigo == normalized_code, 
            Acao.usuario_id == usuario_id
        ).first()
    except ValueError:
        return None
    finally:
        db.close()

def get_carteira(usuario_id):
    """Retorna todas as posições da carteira de um usuário"""
    db = SessionLocal()
    try:
        return db.query(Carteira).filter(Carteira.usuario_id == usuario_id).all()
    finally:
        db.close()

def get_posicao_by_codigo(codigo: str, usuario_id: int):
    """Busca uma posição na carteira por código normalizado"""
    from src.backend.utils import normalize_stock_code
    
    db = SessionLocal()
    try:
        normalized_code = normalize_stock_code(codigo)
        return db.query(Carteira).filter(
            Carteira.codigo == normalized_code, 
            Carteira.usuario_id == usuario_id
        ).first()
    except ValueError:
        return None
    finally:
        db.close()

def get_transacoes(usuario_id: int):
    """Retorna todas as transações de um usuário"""
    db = SessionLocal()
    try:
        return db.query(Transacao).filter(
            Transacao.usuario_id == usuario_id
        ).order_by(Transacao.data_transacao.desc()).all()
    finally:
        db.close()

def get_transacoes_by_codigo(codigo: str, usuario_id: int):
    """Retorna transações de uma ação específica"""
    from src.backend.utils import normalize_stock_code
    
    db = SessionLocal()
    try:
        normalized_code = normalize_stock_code(codigo)
        return db.query(Transacao).filter(
            Transacao.codigo == normalized_code,
            Transacao.usuario_id == usuario_id
        ).order_by(Transacao.data_transacao.desc()).all()
    except ValueError:
        return []
    finally:
        db.close()

def criar_transacao(codigo: str, quantidade_vendida: int, preco_compra: float, 
                   preco_venda: float, stop_loss_original: float, 
                   take_profit_original: float, usuario_id: int):
    """Cria uma nova transação de venda"""
    from src.backend.utils import normalize_stock_code
    
    db = SessionLocal()
    try:
        normalized_code = normalize_stock_code(codigo)
        
        # Calcula valores
        valor_total = quantidade_vendida * preco_venda
        lucro_prejuizo = (preco_venda - preco_compra) * quantidade_vendida
        percentual_resultado = ((preco_venda - preco_compra) / preco_compra) * 100
        
        transacao = Transacao(
            codigo=normalized_code,
            quantidade_vendida=quantidade_vendida,
            preco_compra=preco_compra,
            preco_venda=preco_venda,
            stop_loss_original=stop_loss_original,
            take_profit_original=take_profit_original,
            valor_total=valor_total,
            lucro_prejuizo=lucro_prejuizo,
            percentual_resultado=percentual_resultado,
            usuario_id=usuario_id
        )
        
        db.add(transacao)
        db.commit()
        db.refresh(transacao)
        return transacao
        
    except Exception as e:
        db.rollback()
        raise e
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