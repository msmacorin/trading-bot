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
    from src.backend.database import (criar_usuario, get_acoes_ativas, get_carteira, SessionLocal, 
                                     Acao, Carteira, Transacao, get_transacoes, criar_transacao, 
                                     get_posicao_by_codigo)
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

class VendaRequest(BaseModel):
    codigo: str
    quantidade_vendida: int
    preco_venda: float

class TransacaoResponse(BaseModel):
    id: int
    codigo: str
    data_transacao: str
    quantidade_vendida: int
    preco_compra: float
    preco_venda: float
    stop_loss_original: float
    take_profit_original: float
    valor_total: float
    lucro_prejuizo: float
    percentual_resultado: float
    usuario_id: int
    
    class Config:
        from_attributes = True

class ResumoTransacoesResponse(BaseModel):
    total_transacoes: int
    valor_total_vendido: float
    lucro_prejuizo_total: float
    percentual_medio: float
    transacoes: List[TransacaoResponse]

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
    # Importa e usa normalização
    from src.backend.utils import normalize_stock_code, validate_stock_code
    
    try:
        # Normaliza e valida o código da ação
        normalized_code = normalize_stock_code(acao.codigo)
        stock_info = validate_stock_code(acao.codigo)
        
        # Verifica se a ação já existe para este usuário (usando código normalizado)
        db_acao = db.query(Acao).filter(Acao.codigo == normalized_code, Acao.usuario_id == usuario.id).first()
        if db_acao:
            raise HTTPException(
                status_code=400, 
                detail=f"Ação {stock_info['display_name']} já cadastrada para este usuário"
            )
        
        db_acao = Acao(codigo=normalized_code, usuario_id=usuario.id, ativo=True)
        db.add(db_acao)
        db.commit()
        db.refresh(db_acao)
        return db_acao
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/acoes/{codigo}")
async def remover_acao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Remove uma ação do monitoramento"""
    # Importa e usa normalização
    from src.backend.utils import normalize_stock_code
    
    try:
        # Normaliza o código para busca
        normalized_code = normalize_stock_code(codigo)
        
        db_acao = db.query(Acao).filter(Acao.codigo == normalized_code, Acao.usuario_id == usuario.id).first()
        if not db_acao:
            raise HTTPException(status_code=404, detail="Ação não encontrada")
        
        db.delete(db_acao)
        db.commit()
        return {"message": f"Ação {normalized_code} removida com sucesso"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/acoes/{codigo}/ativar", response_model=AcaoResponse)
async def ativar_acao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Ativa uma ação para monitoramento"""
    # Importa e usa normalização
    from src.backend.utils import normalize_stock_code
    
    try:
        # Normaliza o código para busca
        normalized_code = normalize_stock_code(codigo)
        
        db_acao = db.query(Acao).filter(Acao.codigo == normalized_code, Acao.usuario_id == usuario.id).first()
        if not db_acao:
            raise HTTPException(status_code=404, detail="Ação não encontrada")
        
        db_acao.ativo = True
        db.commit()
        db.refresh(db_acao)
        return db_acao
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/acoes/{codigo}/desativar", response_model=AcaoResponse)
async def desativar_acao(codigo: str, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Desativa uma ação do monitoramento"""
    # Importa e usa normalização
    from src.backend.utils import normalize_stock_code
    
    try:
        # Normaliza o código para busca
        normalized_code = normalize_stock_code(codigo)
        
        db_acao = db.query(Acao).filter(Acao.codigo == normalized_code, Acao.usuario_id == usuario.id).first()
        if not db_acao:
            raise HTTPException(status_code=404, detail="Ação não encontrada")
        
        db_acao.ativo = False
        db.commit()
        db.refresh(db_acao)
        return db_acao
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Rotas protegidas - Carteira
@app.get("/api/carteira", response_model=List[CarteiraResponse])
async def listar_carteira(usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Lista a carteira do usuário"""
    return db.query(Carteira).filter(Carteira.usuario_id == usuario.id).all()

@app.post("/api/carteira", response_model=CarteiraResponse)
async def adicionar_posicao(posicao: CarteiraCreate, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Adiciona uma nova posição na carteira"""
    # Importa e usa normalização
    from src.backend.utils import normalize_stock_code
    
    try:
        # Normaliza o código para busca e armazenamento
        normalized_code = normalize_stock_code(posicao.codigo)
        
        # Verifica se a ação existe para este usuário
        db_acao = db.query(Acao).filter(Acao.codigo == normalized_code, Acao.usuario_id == usuario.id).first()
        if not db_acao:
            raise HTTPException(status_code=400, detail="Ação não cadastrada no sistema para este usuário")
        
        # Verifica se já existe posição para este usuário
        db_posicao = db.query(Carteira).filter(Carteira.codigo == normalized_code, Carteira.usuario_id == usuario.id).first()
        if db_posicao:
            raise HTTPException(status_code=400, detail="Posição já existe na carteira")
        
        # Cria nova posição com código normalizado
        posicao_data = posicao.model_dump()
        posicao_data['codigo'] = normalized_code
        db_posicao = Carteira(**posicao_data, usuario_id=usuario.id)
        db.add(db_posicao)
        db.commit()
        db.refresh(db_posicao)
        return db_posicao
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    # Importa e usa normalização
    from src.backend.utils import normalize_stock_code
    
    try:
        # Normaliza o código para busca
        normalized_code = normalize_stock_code(codigo)
        
        db_posicao = db.query(Carteira).filter(Carteira.codigo == normalized_code, Carteira.usuario_id == usuario.id).first()
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
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Rotas de vendas e transações
@app.post("/api/carteira/{codigo}/vender")
async def vender_acao(codigo: str, venda: VendaRequest, usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    """Executa venda de ação da carteira"""
    from src.backend.utils import normalize_stock_code
    
    try:
        # Normaliza o código
        normalized_code = normalize_stock_code(codigo)
        
        # Busca a posição na carteira
        posicao = db.query(Carteira).filter(
            Carteira.codigo == normalized_code, 
            Carteira.usuario_id == usuario.id
        ).first()
        
        if not posicao:
            raise HTTPException(status_code=404, detail="Posição não encontrada na carteira")
        
        # Valida quantidade
        if venda.quantidade_vendida <= 0:
            raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero")
        
        if venda.quantidade_vendida > posicao.quantidade:
            raise HTTPException(
                status_code=400, 
                detail=f"Quantidade vendida ({venda.quantidade_vendida}) maior que disponível ({posicao.quantidade})"
            )
        
        # Valida preço
        if venda.preco_venda <= 0:
            raise HTTPException(status_code=400, detail="Preço de venda deve ser maior que zero")
        
        # Cria a transação
        transacao = criar_transacao(
            codigo=normalized_code,
            quantidade_vendida=venda.quantidade_vendida,
            preco_compra=posicao.preco_medio,
            preco_venda=venda.preco_venda,
            stop_loss_original=posicao.stop_loss,
            take_profit_original=posicao.take_profit,
            usuario_id=usuario.id
        )
        
        # Atualiza ou remove a posição
        if venda.quantidade_vendida == posicao.quantidade:
            # Venda total - remove da carteira
            db.delete(posicao)
        else:
            # Venda parcial - reduz quantidade
            posicao.quantidade -= venda.quantidade_vendida
        
        db.commit()
        
        # Prepara resposta
        transacao_response = TransacaoResponse(
            id=transacao.id,
            codigo=transacao.codigo,
            data_transacao=transacao.data_transacao.isoformat(),
            quantidade_vendida=transacao.quantidade_vendida,
            preco_compra=transacao.preco_compra,
            preco_venda=transacao.preco_venda,
            stop_loss_original=transacao.stop_loss_original,
            take_profit_original=transacao.take_profit_original,
            valor_total=transacao.valor_total,
            lucro_prejuizo=transacao.lucro_prejuizo,
            percentual_resultado=transacao.percentual_resultado,
            usuario_id=transacao.usuario_id
        )
        
        return {
            "message": f"Venda executada com sucesso",
            "transacao": transacao_response,
            "posicao_removida": venda.quantidade_vendida == posicao.quantidade
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/transacoes", response_model=ResumoTransacoesResponse)
async def listar_transacoes(usuario = Depends(obter_usuario_atual)):
    """Lista todas as transações do usuário com resumo"""
    try:
        transacoes = get_transacoes(usuario.id)
        
        # Calcula resumo
        if transacoes:
            total_transacoes = len(transacoes)
            valor_total_vendido = sum(t.valor_total for t in transacoes)
            lucro_prejuizo_total = sum(t.lucro_prejuizo for t in transacoes)
            percentual_medio = sum(t.percentual_resultado for t in transacoes) / total_transacoes
        else:
            total_transacoes = 0
            valor_total_vendido = 0.0
            lucro_prejuizo_total = 0.0
            percentual_medio = 0.0
        
        # Converte transações para response
        transacoes_response = [
            TransacaoResponse(
                id=t.id,
                codigo=t.codigo,
                data_transacao=t.data_transacao.isoformat(),
                quantidade_vendida=t.quantidade_vendida,
                preco_compra=t.preco_compra,
                preco_venda=t.preco_venda,
                stop_loss_original=t.stop_loss_original,
                take_profit_original=t.take_profit_original,
                valor_total=t.valor_total,
                lucro_prejuizo=t.lucro_prejuizo,
                percentual_resultado=t.percentual_resultado,
                usuario_id=t.usuario_id
            ) for t in transacoes
        ]
        
        return ResumoTransacoesResponse(
            total_transacoes=total_transacoes,
            valor_total_vendido=valor_total_vendido,
            lucro_prejuizo_total=lucro_prejuizo_total,
            percentual_medio=percentual_medio,
            transacoes=transacoes_response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/usuario/atual")
async def usuario_atual(usuario = Depends(obter_usuario_atual)):
    """Retorna dados do usuário atual"""
    return usuario

# Endpoint de análise
@app.get("/api/acoes/{codigo}/analise")
async def analisar_acao(codigo: str):
    """Realiza análise técnica de uma ação específica usando múltiplos provedores, com lock e cache on-demand"""
    try:
        from src.backend.app import analyze_stock_on_demand
        analysis = analyze_stock_on_demand(codigo)
        analysis['codigo'] = codigo
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints do sistema de cache otimizado
@app.get("/api/system/cache/stats")
async def get_cache_statistics():
    """Retorna estatísticas do cache compartilhado de análises"""
    try:
        from src.backend.app import get_cache_stats
        return get_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@app.post("/api/system/cache/force-analysis")
async def force_cache_analysis(usuario = Depends(obter_usuario_atual)):
    """Força uma nova análise e atualização do cache (apenas para usuários autenticados)"""
    try:
        from src.backend.app import analyze_all_stocks
        import asyncio
        
        # Executa a análise em background
        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(None, analyze_all_stocks)
        
        return {
            "message": "Análise forçada iniciada em background",
            "status": "running",
            "usuario": usuario.nome
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao forçar análise: {str(e)}")

@app.get("/api/system/cache/status")
async def get_cache_status():
    """Retorna status básico do cache"""
    try:
        from src.backend.app import analysis_cache, cache_timestamp
        from datetime import datetime
        
        if not analysis_cache:
            return {
                "cache_active": False,
                "cache_size": 0,
                "last_update": None,
                "message": "Cache vazio - nenhuma análise executada ainda"
            }
        
        cache_age = (datetime.now() - cache_timestamp).total_seconds() if cache_timestamp else 0
        total_users = sum(len(data['user_ids']) for data in analysis_cache.values())
        
        return {
            "cache_active": True,
            "cache_size": len(analysis_cache),
            "last_update": cache_timestamp,
            "cache_age_seconds": cache_age,
            "total_users_affected": total_users,
            "message": f"Cache ativo com {len(analysis_cache)} ações analisadas"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")

# Endpoint para testar provedores de dados
@app.get("/api/system/data-providers/test")
async def testar_provedores(symbols: str = "PETR4,VALE3,ITUB4"):
    """
    Testa todos os provedores de dados disponíveis
    
    Args:
        symbols: Símbolos para teste separados por vírgula (ex: PETR4,VALE3)
    """
    try:
        from src.backend.analyzer import test_data_providers
        symbol_list = [s.strip() for s in symbols.split(',')]
        results = test_data_providers(symbol_list)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao testar provedores: {str(e)}")

# Endpoint para obter informações do sistema de dados
@app.get("/api/system/data-providers/status")
async def status_provedores():
    """Retorna o status atual dos provedores de dados"""
    try:
        from src.backend.data_providers import data_manager
        from src.backend.config import DataProviderConfig
        import pandas as pd
        
        # Informações básicas dos provedores
        providers_info = []
        for provider in data_manager.providers:
            providers_info.append({
                "name": provider.get_provider_name(),
                "available": getattr(provider, 'available', True),
                "priority": data_manager.providers.index(provider) + 1
            })
        
        # Status das configurações
        enabled_providers = DataProviderConfig.get_enabled_providers()
        api_keys_status = DataProviderConfig.get_api_keys_status()
        
        return {
            "total_providers": len(data_manager.providers),
            "providers": providers_info,
            "enabled_providers": enabled_providers,
            "api_keys_status": api_keys_status,
            "fallback_enabled": True,
            "last_check": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

# Endpoint para instruções de configuração
@app.get("/api/system/data-providers/setup")
async def instrucoes_setup():
    """Retorna instruções para configurar provedores de dados"""
    try:
        from src.backend.config import API_SETUP_INSTRUCTIONS, DataProviderConfig
        
        return {
            "instructions": API_SETUP_INSTRUCTIONS,
            "current_config": {
                "enabled_providers": DataProviderConfig.get_enabled_providers(),
                "api_keys_status": DataProviderConfig.get_api_keys_status(),
                "provider_priority": DataProviderConfig.get_provider_priority()
            },
            "docker_setup": {
                "description": "Para configurar em Docker, adicione as variáveis ao docker-compose.yml",
                "example": {
                    "environment": [
                        "- ALPHA_VANTAGE_API_KEY=your_key_here",
                        "- QUANDL_API_KEY=your_key_here"
                    ]
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter instruções: {str(e)}")

# Endpoint para estatísticas dos provedores
@app.get("/api/system/data-providers/stats")
async def estatisticas_provedores():
    """Retorna estatísticas detalhadas dos provedores"""
    try:
        from src.backend.data_providers import data_manager
        
        stats = data_manager.get_provider_statistics()
        
        return {
            "provider_statistics": stats,
            "total_active_providers": len(data_manager.providers),
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}") 