"""
Utilitários para normalização e validação de códigos de ações
"""

import re
from typing import Dict, Set, Optional

# Conjunto de códigos de ações válidos conhecidos (para validação)
KNOWN_STOCK_CODES: Set[str] = {
    'PETR4', 'PETR3', 'VALE3', 'ITUB4', 'BBDC4', 'MGLU3', 'WEGE3',
    'ABEV3', 'AZUL4', 'B3SA3', 'BBAS3', 'BPAC11', 'BRDT3', 'BRKM5',
    'CCRO3', 'CIEL3', 'CMIG4', 'COGN3', 'CPFE3', 'CRFB3', 'CSAN3',
    'CSNA3', 'CVCB3', 'CYRE3', 'ELET3', 'ELET6', 'EMBR3', 'ENBR3',
    'EQTL3', 'FLRY3', 'GGBR4', 'GNDI3', 'GOAU4', 'GOLL4', 'HAPV3',
    'HYPE3', 'IGTA3', 'IRBR3', 'JBSS3', 'JHSF3', 'KLBN11', 'LAME4',
    'LREN3', 'LWSA3', 'MDIA3', 'MEAL3', 'MRFG3', 'MRVE3', 'MULT3',
    'NTCO3', 'PCAR3', 'PRIO3', 'QUAL3', 'RADL3', 'RAIL3', 'RDOR3',
    'RENT3', 'SANB11', 'SBSP3', 'SULA11', 'SUZB3', 'TAEE11', 'TOTS3',
    'UGPA3', 'USIM5', 'VIVT3', 'VVAR3', 'YDUQ3'
}

def normalize_stock_code(code: str) -> str:
    """
    Normaliza o código de uma ação removendo sufixos desnecessários e formatando corretamente.
    
    Args:
        code: Código da ação (ex: "PETR4.SA", "petr4", "PETR4F", etc.)
    
    Returns:
        Código normalizado (ex: "PETR4", "PETR4F")
    
    Examples:
        >>> normalize_stock_code("PETR4.SA")
        "PETR4"
        >>> normalize_stock_code("petr4f")
        "PETR4F"
        >>> normalize_stock_code("MGLU3.sa")
        "MGLU3"
        >>> normalize_stock_code("VALE3F.SA")
        "VALE3F"
    """
    if not code or not isinstance(code, str):
        raise ValueError("Código da ação deve ser uma string não vazia")
    
    # Remove espaços e converte para maiúsculo
    normalized = code.strip().upper()
    
    # Remove o sufixo .SA (case insensitive)
    if normalized.endswith('.SA'):
        normalized = normalized[:-3]
    
    # Valida formato básico (letras seguidas de números, opcionalmente com F no final)
    if not re.match(r'^[A-Z]{4}\d{1,2}F?$', normalized):
        raise ValueError(f"Formato de código inválido: {code}. Use formato como PETR4, VALE3F, etc.")
    
    return normalized

def is_fractional_stock(code: str) -> bool:
    """
    Verifica se o código representa uma ação fracionária.
    
    Args:
        code: Código da ação (normalizado ou não)
    
    Returns:
        True se for ação fracionária (termina com F)
    
    Examples:
        >>> is_fractional_stock("PETR4F")
        True
        >>> is_fractional_stock("PETR4")
        False
        >>> is_fractional_stock("VALE3F.SA")
        True
    """
    try:
        normalized = normalize_stock_code(code)
        return normalized.endswith('F')
    except ValueError:
        return False

def get_base_stock_code(code: str) -> str:
    """
    Obtém o código base da ação (sem o sufixo F das fracionárias).
    
    Args:
        code: Código da ação (normalizado ou não)
    
    Returns:
        Código base (ex: "PETR4" para "PETR4F")
    
    Examples:
        >>> get_base_stock_code("PETR4F.SA")
        "PETR4"
        >>> get_base_stock_code("MGLU3")
        "MGLU3"
    """
    normalized = normalize_stock_code(code)
    if normalized.endswith('F'):
        return normalized[:-1]
    return normalized

def validate_stock_code(code: str, allow_unknown: bool = True) -> Dict[str, any]:
    """
    Valida um código de ação e retorna informações sobre ele.
    
    Args:
        code: Código da ação
        allow_unknown: Se deve permitir códigos não conhecidos
    
    Returns:
        Dict com informações sobre o código validado
    
    Raises:
        ValueError: Se o código for inválido
    """
    try:
        normalized = normalize_stock_code(code)
        base_code = get_base_stock_code(normalized)
        is_fractional = is_fractional_stock(normalized)
        is_known = base_code in KNOWN_STOCK_CODES
        
        if not allow_unknown and not is_known:
            raise ValueError(f"Código {base_code} não é reconhecido como uma ação válida")
        
        return {
            'original': code,
            'normalized': normalized,
            'base_code': base_code,
            'is_fractional': is_fractional,
            'is_known': is_known,
            'display_name': f"{base_code}{'F' if is_fractional else ''}",
            'api_codes': {
                'yahoo': f"{normalized}.SA",
                'investing': normalized,
                'alphavantage': f"{normalized}.SA",
                'brapi': normalized
            }
        }
        
    except ValueError as e:
        raise ValueError(f"Erro na validação do código {code}: {str(e)}")

def format_stock_code_for_provider(code: str, provider: str) -> str:
    """
    Formata o código da ação para um provedor específico de dados.
    
    Args:
        code: Código da ação
        provider: Nome do provedor ('yahoo', 'investing', 'alphavantage', etc.)
    
    Returns:
        Código formatado para o provedor
    """
    validation = validate_stock_code(code)
    normalized = validation['normalized']
    
    # Mapeamento de formatos por provedor
    provider_formats = {
        'yahoo': f"{normalized}.SA",
        'yahoofinance': f"{normalized}.SA",
        'investing': normalized,
        'investpy': normalized,
        'alphavantage': f"{normalized}.SA",
        'brapi': normalized,
        'hgfinance': normalized,
        'mfinance': normalized,
        'tiingo': f"{normalized}.SA",
        'quandl': normalized
    }
    
    return provider_formats.get(provider.lower(), normalized)

def get_stock_display_info(code: str) -> Dict[str, str]:
    """
    Obtém informações de exibição para uma ação.
    
    Args:
        code: Código da ação
    
    Returns:
        Dict com informações de exibição
    """
    validation = validate_stock_code(code)
    
    fractional_text = " (Fracionária)" if validation['is_fractional'] else ""
    known_text = "✅" if validation['is_known'] else "⚠️"
    
    return {
        'display_code': validation['display_name'],
        'full_display': f"{validation['display_name']}{fractional_text}",
        'status_icon': known_text,
        'description': f"Ação {validation['base_code']}{fractional_text}",
        'tooltip': f"Código: {validation['normalized']} | Base: {validation['base_code']} | Fracionária: {'Sim' if validation['is_fractional'] else 'Não'}"
    }

# Função para migração de dados existentes
def migrate_existing_stock_codes(codes_list: list) -> Dict[str, str]:
    """
    Migra uma lista de códigos existentes para o formato normalizado.
    
    Args:
        codes_list: Lista de códigos a serem migrados
    
    Returns:
        Dict mapeando código original para código normalizado
    """
    migration_map = {}
    
    for code in codes_list:
        try:
            normalized = normalize_stock_code(code)
            migration_map[code] = normalized
        except ValueError as e:
            # Log do erro, mas continua processamento
            print(f"Erro ao migrar código {code}: {e}")
            migration_map[code] = code  # Mantém original se não conseguir normalizar
    
    return migration_map 