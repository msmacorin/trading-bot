from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session
import sys
import os

# Adiciona o diretório pai ao path para importar módulos do backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from src.backend.database import SessionLocal, Acao, Carteira, criar_usuario
from analyzer import analyze_stock
from auth import obter_usuario_atual, autenticar_e_criar_token

app = FastAPI(
    title="Trading Bot API",
    description="API para gerenciar ações e carteira do Trading Bot",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para validação de dados
class UsuarioBase(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    nome: str = Field(..., description="Nome completo do usuário")

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., description="Senha do usuário", min_length=6)

class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    data_criacao: str
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

class AcaoBase(BaseModel):
    codigo: str = Field(..., description="Código da ação (ex: PETR4.SA)")
    ativo: bool = Field(True, description="Se a ação está ativa para monitoramento")

class AcaoCreate(AcaoBase):
    pass

class AcaoResponse(AcaoBase):
    id: int
    usuario_id: int
    
    class Config:
        from_attributes = True

class CarteiraBase(BaseModel):
    codigo: str = Field(..., description="Código da ação (ex: PETR4.SA)")
    quantidade: int = Field(..., description="Quantidade de ações")
    preco_medio: float = Field(..., description="Preço médio de compra")
    stop_loss: float = Field(..., description="Preço para stop loss")
    take_profit: float = Field(..., description="Preço para take profit")

class CarteiraCreate(CarteiraBase):
    pass

class CarteiraResponse(CarteiraBase):
    id: int
    usuario_id: int
    
    class Config:
        from_attributes = True

class AnaliseResponse(BaseModel):
    codigo: str = Field(..., description="Código da ação analisada")
    current_position: str = Field(..., description="Recomendação para quem já tem a ação (SELL, HOLD)")
    new_position: str = Field(..., description="Recomendação para quem não tem a ação (BUY, WAIT)")
    price: float = Field(..., description="Preço atual")
    stop_loss: float = Field(..., description="Stop loss sugerido (-3%)")
    take_profit: float = Field(..., description="Take profit sugerido (+5%)")
    profit_pct: float = Field(..., description="Variação percentual no período")
    rsi: float = Field(..., description="Índice de Força Relativa")
    macd: float = Field(..., description="MACD (Moving Average Convergence Divergence)")
    trend: str = Field(..., description="Tendência (UP, DOWN)")
    conditions: List[str] = Field(..., description="Condições identificadas na análise")

# Dependência para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints de Autenticação
@app.post("/auth/registro", response_model=UsuarioResponse, tags=["Autenticação"])
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário"""
    novo_usuario, erro = criar_usuario(usuario.email, usuario.nome, usuario.senha)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    return novo_usuario

@app.post("/auth/login", response_model=LoginResponse, tags=["Autenticação"])
def login_usuario(login: LoginRequest):
    """Faz login do usuário e retorna token JWT"""
    resultado, erro = autenticar_e_criar_token(login.email, login.senha)
    if erro:
        raise HTTPException(status_code=401, detail=erro)
    return resultado

@app.get("/auth/me", response_model=UsuarioResponse, tags=["Autenticação"])
def obter_usuario_logado(usuario_atual = Depends(obter_usuario_atual)):
    """Retorna informações do usuário logado"""
    return usuario_atual

# Endpoints para Ações (agora vinculados ao usuário)
@app.get("/acoes/", response_model=List[AcaoResponse], tags=["Ações"])
def listar_acoes(usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Lista todas as ações do usuário logado"""
    return db.query(Acao).filter(Acao.usuario_id == usuario_atual.id).all()

@app.get("/acoes/ativas/", response_model=List[AcaoResponse], tags=["Ações"])
def listar_acoes_ativas(usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Lista apenas as ações ativas do usuário logado"""
    return db.query(Acao).filter(Acao.ativo == True, Acao.usuario_id == usuario_atual.id).all()

@app.post("/acoes/", response_model=AcaoResponse, tags=["Ações"])
def adicionar_acao(acao: AcaoCreate, usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Adiciona uma nova ação para monitoramento do usuário logado"""
    # Verifica se a ação já existe para este usuário
    db_acao = db.query(Acao).filter(Acao.codigo == acao.codigo, Acao.usuario_id == usuario_atual.id).first()
    if db_acao:
        raise HTTPException(status_code=400, detail="Ação já cadastrada para este usuário")
    
    db_acao = Acao(**acao.model_dump(), usuario_id=usuario_atual.id)
    db.add(db_acao)
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.delete("/acoes/{codigo}", tags=["Ações"])
def remover_acao(codigo: str, usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Remove uma ação do monitoramento do usuário logado"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo, Acao.usuario_id == usuario_atual.id).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db.delete(db_acao)
    db.commit()
    return {"message": f"Ação {codigo} removida com sucesso"}

@app.patch("/acoes/{codigo}/ativar", response_model=AcaoResponse, tags=["Ações"])
def ativar_acao(codigo: str, usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Ativa uma ação para monitoramento do usuário logado"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo, Acao.usuario_id == usuario_atual.id).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db_acao.ativo = True
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.patch("/acoes/{codigo}/desativar", response_model=AcaoResponse, tags=["Ações"])
def desativar_acao(codigo: str, usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Desativa uma ação do monitoramento do usuário logado"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo, Acao.usuario_id == usuario_atual.id).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db_acao.ativo = False
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.get("/acoes/{codigo}/analise", response_model=AnaliseResponse, tags=["Análise"])
def analisar_acao(codigo: str):
    """
    Realiza análise técnica de uma ação específica.
    
    Retorna:
    - Recomendações para posições existentes e novas
    - Preço atual e sugestões de stop loss/take profit
    - Indicadores técnicos (RSI, MACD, tendência)
    - Condições identificadas
    """
    try:
        analysis = analyze_stock(codigo)
        # Adiciona o código da ação ao resultado
        analysis['codigo'] = codigo
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints para Carteira (agora vinculados ao usuário)
@app.get("/carteira/", response_model=List[CarteiraResponse], tags=["Carteira"])
def listar_carteira(usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Lista todas as posições da carteira do usuário logado"""
    return db.query(Carteira).filter(Carteira.usuario_id == usuario_atual.id).all()

@app.post("/carteira/", response_model=CarteiraResponse, tags=["Carteira"])
def adicionar_posicao(posicao: CarteiraCreate, usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Adiciona uma nova posição na carteira do usuário logado"""
    # Verifica se a ação existe para este usuário
    db_acao = db.query(Acao).filter(Acao.codigo == posicao.codigo, Acao.usuario_id == usuario_atual.id).first()
    if not db_acao:
        raise HTTPException(status_code=400, detail="Ação não cadastrada no sistema para este usuário")
    
    # Verifica se já existe posição para este usuário
    db_posicao = db.query(Carteira).filter(Carteira.codigo == posicao.codigo, Carteira.usuario_id == usuario_atual.id).first()
    if db_posicao:
        raise HTTPException(status_code=400, detail="Posição já existe na carteira")
    
    db_posicao = Carteira(**posicao.model_dump(), usuario_id=usuario_atual.id)
    db.add(db_posicao)
    db.commit()
    db.refresh(db_posicao)
    return db_posicao

@app.delete("/carteira/{codigo}", tags=["Carteira"])
def remover_posicao(codigo: str, usuario_atual = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Remove uma posição da carteira do usuário logado"""
    db_posicao = db.query(Carteira).filter(Carteira.codigo == codigo, Carteira.usuario_id == usuario_atual.id).first()
    if not db_posicao:
        raise HTTPException(status_code=404, detail="Posição não encontrada")
    
    db.delete(db_posicao)
    db.commit()
    return {"message": f"Posição {codigo} removida com sucesso"}

@app.patch("/carteira/{codigo}", response_model=CarteiraResponse, tags=["Carteira"])
def atualizar_posicao(
    codigo: str,
    quantidade: Optional[int] = None,
    preco_medio: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    usuario_atual = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Atualiza os dados de uma posição na carteira do usuário logado"""
    db_posicao = db.query(Carteira).filter(Carteira.codigo == codigo, Carteira.usuario_id == usuario_atual.id).first()
    if not db_posicao:
        raise HTTPException(status_code=404, detail="Posição não encontrada")
    
    if quantidade is not None:
        db_posicao.quantidade = quantidade
    if preco_medio is not None:
        db_posicao.preco_medio = preco_medio
    if stop_loss is not None:
        db_posicao.stop_loss = stop_loss
    if take_profit is not None:
        db_posicao.take_profit = take_profit
    
    db.commit()
    db.refresh(db_posicao)
    return db_posicao 