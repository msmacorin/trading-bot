import sys
import os
print("PYTHONPATH:", sys.path)
print("Current directory:", os.getcwd())
print("Files in current directory:", os.listdir("."))
print("Files in src directory:", os.listdir("src"))
print("Files in src/backend directory:", os.listdir("src/backend"))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

try:
    from src.backend.database import criar_usuario, get_acoes_ativas, get_carteira, SessionLocal, Acao, Carteira
    print("✅ Successfully imported src.backend.database")
except ImportError as e:
    print("❌ Error importing src.backend.database:", str(e))
    raise

try:
    from src.backend.auth import autenticar_e_criar_token, obter_usuario_atual
    print("✅ Successfully imported src.backend.auth")
except ImportError as e:
    print("❌ Error importing src.backend.auth:", str(e))
    raise

from sqlalchemy.orm import Session

app = FastAPI(title="Trading Bot API")

# Configuração CORS
origins = [
    "http://localhost:3000",     # Frontend local
    "http://127.0.0.1:3000",     # Frontend local (alternativo)
    "http://trading-web:3000",   # Frontend no Docker
    "http://localhost:8080",     # Grafana
    "http://127.0.0.1:8080",     # Grafana (alternativo)
    # Adiciona suporte para IPs locais (192.168.x.x, 10.x.x.x, etc)
    "http://192.168.0.0/16",     # Rede 192.168.x.x
    "http://10.0.0.0/8",         # Rede 10.x.x.x
    "http://172.16.0.0/12",      # Rede 172.16.x.x - 172.31.x.x
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens em desenvolvimento
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["Content-Length", "Content-Range"],
    max_age=3600,  # Cache das respostas OPTIONS por 1 hora
)

# Dependência para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos Pydantic
class LoginRequest(BaseModel):
    email: str
    senha: str

class RegisterRequest(BaseModel):
    nome: str
    email: str
    senha: str

class UsuarioResponse(BaseModel):
    id: int
    email: str
    nome: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

class AcaoCreate(BaseModel):
    codigo: str

class AcaoResponse(BaseModel):
    id: int
    codigo: str
    ativo: bool
    usuario_id: int
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class CarteiraCreate(BaseModel):
    codigo: str
    quantidade: int
    preco_medio: float
    stop_loss: float
    take_profit: float

class CarteiraResponse(BaseModel):
    id: int
    codigo: str
    quantidade: int
    preco_medio: float
    stop_loss: float
    take_profit: float
    usuario_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

# Rotas de autenticação
@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Endpoint para login de usuário"""
    result, error = autenticar_e_criar_token(request.email, request.senha)
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    return result

@app.post("/auth/registro", response_model=UsuarioResponse)
async def registro(request: RegisterRequest):
    """Endpoint para registro de novo usuário"""
    usuario, error = criar_usuario(request.email, request.nome, request.senha)
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    return usuario

# Rotas protegidas - Ações
@app.get("/api/acoes", response_model=List[AcaoResponse])
async def listar_acoes(usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Lista todas as ações do usuário"""
    return db.query(Acao).filter(Acao.usuario_id == usuario.id).all()

@app.post("/api/acoes", response_model=AcaoResponse)
async def adicionar_acao(acao: AcaoCreate, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Adiciona uma nova ação para monitoramento"""
    # Verifica se a ação já existe para este usuário
    db_acao = db.query(Acao).filter(Acao.codigo == acao.codigo, Acao.usuario_id == usuario.id).first()
    if db_acao:
        raise HTTPException(status_code=400, detail="Ação já cadastrada para este usuário")
    
    db_acao = Acao(codigo=acao.codigo, usuario_id=usuario.id, ativo=True)
    db.add(db_acao)
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.delete("/api/acoes/{codigo}")
async def remover_acao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Remove uma ação do monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo, Acao.usuario_id == usuario.id).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db.delete(db_acao)
    db.commit()
    return {"message": f"Ação {codigo} removida com sucesso"}

@app.patch("/api/acoes/{codigo}/ativar", response_model=AcaoResponse)
async def ativar_acao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Ativa uma ação para monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo, Acao.usuario_id == usuario.id).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db_acao.ativo = True
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.patch("/api/acoes/{codigo}/desativar", response_model=AcaoResponse)
async def desativar_acao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Desativa uma ação do monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo, Acao.usuario_id == usuario.id).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db_acao.ativo = False
    db.commit()
    db.refresh(db_acao)
    return db_acao

# Rotas protegidas - Carteira
@app.get("/api/carteira", response_model=List[CarteiraResponse])
async def listar_carteira(usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Lista a carteira do usuário"""
    return db.query(Carteira).filter(Carteira.usuario_id == usuario.id).all()

@app.post("/api/carteira", response_model=CarteiraResponse)
async def adicionar_posicao(posicao: CarteiraCreate, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Adiciona uma nova posição na carteira"""
    # Verifica se a ação existe para este usuário
    db_acao = db.query(Acao).filter(Acao.codigo == posicao.codigo, Acao.usuario_id == usuario.id).first()
    if not db_acao:
        raise HTTPException(status_code=400, detail="Ação não cadastrada no sistema para este usuário")
    
    # Verifica se já existe posição para este usuário
    db_posicao = db.query(Carteira).filter(Carteira.codigo == posicao.codigo, Carteira.usuario_id == usuario.id).first()
    if db_posicao:
        raise HTTPException(status_code=400, detail="Posição já existe na carteira")
    
    db_posicao = Carteira(**posicao.model_dump(), usuario_id=usuario.id)
    db.add(db_posicao)
    db.commit()
    db.refresh(db_posicao)
    return db_posicao

@app.delete("/api/carteira/{codigo}")
async def remover_posicao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Remove uma posição da carteira"""
    db_posicao = db.query(Carteira).filter(Carteira.codigo == codigo, Carteira.usuario_id == usuario.id).first()
    if not db_posicao:
        raise HTTPException(status_code=404, detail="Posição não encontrada")
    
    db.delete(db_posicao)
    db.commit()
    return {"message": f"Posição {codigo} removida com sucesso"}

@app.patch("/api/carteira/{codigo}", response_model=CarteiraResponse)
async def atualizar_posicao(
    codigo: str,
    quantidade: Optional[int] = None,
    preco_medio: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Atualiza os dados de uma posição na carteira"""
    db_posicao = db.query(Carteira).filter(Carteira.codigo == codigo, Carteira.usuario_id == usuario.id).first()
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

@app.get("/api/usuario/atual")
async def usuario_atual(usuario = Depends(obter_usuario_atual)):
    """Retorna dados do usuário atual"""
    return usuario 