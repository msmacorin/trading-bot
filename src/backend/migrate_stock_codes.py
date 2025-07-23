#!/usr/bin/env python3
"""
Script de migração para normalizar códigos de ações existentes no banco de dados.
Este script deve ser executado uma vez após a implementação da normalização.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.database import SessionLocal, Acao, Carteira
from backend.utils import normalize_stock_code, validate_stock_code
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_acoes():
    """Migra códigos na tabela de ações"""
    db = SessionLocal()
    try:
        logger.info("🔄 Iniciando migração da tabela 'acoes'...")
        
        # Busca todas as ações
        acoes = db.query(Acao).all()
        logger.info(f"📊 Encontradas {len(acoes)} ações para processar")
        
        migrated_count = 0
        error_count = 0
        
        for acao in acoes:
            try:
                original_code = acao.codigo
                
                # Tenta normalizar o código
                normalized_code = normalize_stock_code(original_code)
                
                # Se o código mudou, atualiza
                if normalized_code != original_code:
                    logger.info(f"🔄 Migrando ação ID {acao.id}: {original_code} → {normalized_code}")
                    
                    # Verifica se já existe uma ação com o código normalizado para o mesmo usuário
                    existing = db.query(Acao).filter(
                        Acao.codigo == normalized_code,
                        Acao.usuario_id == acao.usuario_id,
                        Acao.id != acao.id
                    ).first()
                    
                    if existing:
                        logger.warning(f"⚠️ Conflito encontrado: {normalized_code} já existe para usuário {acao.usuario_id}")
                        logger.warning(f"   Removendo duplicata (ID {acao.id})")
                        db.delete(acao)
                    else:
                        acao.codigo = normalized_code
                    
                    migrated_count += 1
                else:
                    logger.debug(f"✅ Ação ID {acao.id}: {original_code} já está normalizada")
                    
            except ValueError as e:
                logger.error(f"❌ Erro ao processar ação ID {acao.id} ({acao.codigo}): {e}")
                error_count += 1
                continue
        
        # Commit das mudanças
        db.commit()
        logger.info(f"✅ Migração da tabela 'acoes' concluída:")
        logger.info(f"   - {migrated_count} códigos migrados")
        logger.info(f"   - {error_count} erros encontrados")
        
    except Exception as e:
        logger.error(f"💥 Erro na migração da tabela 'acoes': {e}")
        db.rollback()
        raise
    finally:
        db.close()

def migrate_carteira():
    """Migra códigos na tabela de carteira"""
    db = SessionLocal()
    try:
        logger.info("🔄 Iniciando migração da tabela 'carteira'...")
        
        # Busca todas as posições da carteira
        posicoes = db.query(Carteira).all()
        logger.info(f"📊 Encontradas {len(posicoes)} posições para processar")
        
        migrated_count = 0
        error_count = 0
        
        for posicao in posicoes:
            try:
                original_code = posicao.codigo
                
                # Tenta normalizar o código
                normalized_code = normalize_stock_code(original_code)
                
                # Se o código mudou, atualiza
                if normalized_code != original_code:
                    logger.info(f"🔄 Migrando posição ID {posicao.id}: {original_code} → {normalized_code}")
                    
                    # Verifica se já existe uma posição com o código normalizado para o mesmo usuário
                    existing = db.query(Carteira).filter(
                        Carteira.codigo == normalized_code,
                        Carteira.usuario_id == posicao.usuario_id,
                        Carteira.id != posicao.id
                    ).first()
                    
                    if existing:
                        logger.warning(f"⚠️ Conflito encontrado: {normalized_code} já existe na carteira do usuário {posicao.usuario_id}")
                        logger.warning(f"   Somando quantidades e removendo duplicata (ID {posicao.id})")
                        
                        # Soma as quantidades (mantém preço médio da posição existente)
                        existing.quantidade += posicao.quantidade
                        db.delete(posicao)
                    else:
                        posicao.codigo = normalized_code
                    
                    migrated_count += 1
                else:
                    logger.debug(f"✅ Posição ID {posicao.id}: {original_code} já está normalizada")
                    
            except ValueError as e:
                logger.error(f"❌ Erro ao processar posição ID {posicao.id} ({posicao.codigo}): {e}")
                error_count += 1
                continue
        
        # Commit das mudanças
        db.commit()
        logger.info(f"✅ Migração da tabela 'carteira' concluída:")
        logger.info(f"   - {migrated_count} códigos migrados")
        logger.info(f"   - {error_count} erros encontrados")
        
    except Exception as e:
        logger.error(f"💥 Erro na migração da tabela 'carteira': {e}")
        db.rollback()
        raise
    finally:
        db.close()

def validate_migration():
    """Valida se a migração foi bem-sucedida"""
    db = SessionLocal()
    try:
        logger.info("🔍 Validando migração...")
        
        # Valida ações
        acoes = db.query(Acao).all()
        invalid_acoes = []
        
        for acao in acoes:
            try:
                validate_stock_code(acao.codigo)
            except ValueError as e:
                invalid_acoes.append((acao.id, acao.codigo, str(e)))
        
        # Valida carteira
        posicoes = db.query(Carteira).all()
        invalid_posicoes = []
        
        for posicao in posicoes:
            try:
                validate_stock_code(posicao.codigo)
            except ValueError as e:
                invalid_posicoes.append((posicao.id, posicao.codigo, str(e)))
        
        # Relatório de validação
        if not invalid_acoes and not invalid_posicoes:
            logger.info("✅ Validação concluída: Todos os códigos estão válidos!")
        else:
            logger.warning(f"⚠️ Validação encontrou problemas:")
            
            if invalid_acoes:
                logger.warning(f"   Ações inválidas ({len(invalid_acoes)}):")
                for id_, codigo, erro in invalid_acoes:
                    logger.warning(f"     - ID {id_}: {codigo} ({erro})")
            
            if invalid_posicoes:
                logger.warning(f"   Posições inválidas ({len(invalid_posicoes)}):")
                for id_, codigo, erro in invalid_posicoes:
                    logger.warning(f"     - ID {id_}: {codigo} ({erro})")
        
    except Exception as e:
        logger.error(f"💥 Erro na validação: {e}")
        raise
    finally:
        db.close()

def main():
    """Função principal da migração"""
    logger.info("🚀 Iniciando migração de códigos de ações...")
    
    try:
        # Executa as migrações
        migrate_acoes()
        migrate_carteira()
        
        # Valida os resultados
        validate_migration()
        
        logger.info("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"💥 Erro fatal na migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 