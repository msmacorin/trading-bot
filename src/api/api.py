from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
import sys
import os

# Adiciona o diretório pai ao path para importar módulos do backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import SessionLocal, Acao, Carteira
from analyzer import analyze_stock

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
class AcaoBase(BaseModel):
    codigo: str = Field(..., description="Código da ação (ex: PETR4.SA)")
    ativo: bool = Field(True, description="Se a ação está ativa para monitoramento")

class AcaoCreate(AcaoBase):
    pass

class AcaoResponse(AcaoBase):
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
    class Config:
        from_attributes = True

class AnaliseResponse(BaseModel):
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

# Endpoints para Ações
@app.get("/acoes/", response_model=List[AcaoResponse], tags=["Ações"])
def listar_acoes(db: Session = Depends(get_db)):
    """Lista todas as ações cadastradas"""
    return db.query(Acao).all()

@app.get("/acoes/ativas/", response_model=List[AcaoResponse], tags=["Ações"])
def listar_acoes_ativas(db: Session = Depends(get_db)):
    """Lista apenas as ações ativas"""
    return db.query(Acao).filter(Acao.ativo == True).all()

@app.post("/acoes/", response_model=AcaoResponse, tags=["Ações"])
def adicionar_acao(acao: AcaoCreate, db: Session = Depends(get_db)):
    """Adiciona uma nova ação para monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == acao.codigo).first()
    if db_acao:
        raise HTTPException(status_code=400, detail="Ação já cadastrada")
    
    db_acao = Acao(**acao.model_dump())
    db.add(db_acao)
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.delete("/acoes/{codigo}", tags=["Ações"])
def remover_acao(codigo: str, db: Session = Depends(get_db)):
    """Remove uma ação do monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db.delete(db_acao)
    db.commit()
    return {"message": f"Ação {codigo} removida com sucesso"}

@app.patch("/acoes/{codigo}/ativar", response_model=AcaoResponse, tags=["Ações"])
def ativar_acao(codigo: str, db: Session = Depends(get_db)):
    """Ativa uma ação para monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo).first()
    if not db_acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    
    db_acao.ativo = True
    db.commit()
    db.refresh(db_acao)
    return db_acao

@app.patch("/acoes/{codigo}/desativar", response_model=AcaoResponse, tags=["Ações"])
def desativar_acao(codigo: str, db: Session = Depends(get_db)):
    """Desativa uma ação do monitoramento"""
    db_acao = db.query(Acao).filter(Acao.codigo == codigo).first()
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
        return analyze_stock(codigo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints para Carteira
@app.get("/carteira/", response_model=List[CarteiraResponse], tags=["Carteira"])
def listar_carteira(db: Session = Depends(get_db)):
    """Lista todas as posições da carteira"""
    return db.query(Carteira).all()

@app.post("/carteira/", response_model=CarteiraResponse, tags=["Carteira"])
def adicionar_posicao(posicao: CarteiraCreate, db: Session = Depends(get_db)):
    """Adiciona uma nova posição na carteira"""
    # Verifica se a ação existe
    db_acao = db.query(Acao).filter(Acao.codigo == posicao.codigo).first()
    if not db_acao:
        raise HTTPException(status_code=400, detail="Ação não cadastrada no sistema")
    
    # Verifica se já existe posição
    db_posicao = db.query(Carteira).filter(Carteira.codigo == posicao.codigo).first()
    if db_posicao:
        raise HTTPException(status_code=400, detail="Posição já existe na carteira")
    
    db_posicao = Carteira(**posicao.model_dump())
    db.add(db_posicao)
    db.commit()
    db.refresh(db_posicao)
    return db_posicao

@app.delete("/carteira/{codigo}", tags=["Carteira"])
def remover_posicao(codigo: str, db: Session = Depends(get_db)):
    """Remove uma posição da carteira"""
    db_posicao = db.query(Carteira).filter(Carteira.codigo == codigo).first()
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
    db: Session = Depends(get_db)
):
    """Atualiza os dados de uma posição na carteira"""
    db_posicao = db.query(Carteira).filter(Carteira.codigo == codigo).first()
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