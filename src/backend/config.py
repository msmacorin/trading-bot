"""
Configurações para provedores de dados de ações
"""

import os
from typing import Optional

class DataProviderConfig:
    """Configurações para provedores de dados"""
    
    # Alpha Vantage
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.environ.get('ALPHA_VANTAGE_API_KEY')
    ALPHA_VANTAGE_ENABLED: bool = ALPHA_VANTAGE_API_KEY is not None
    
    # Quandl
    QUANDL_API_KEY: Optional[str] = os.environ.get('QUANDL_API_KEY')
    QUANDL_ENABLED: bool = True  # Funciona sem API key com limitações
    
    # HG Finance
    HG_FINANCE_API_KEY: Optional[str] = os.environ.get('HG_FINANCE_API_KEY')
    HG_FINANCE_ENABLED: bool = True  # Funciona com e sem API key
    
    # BrAPI
    BRAPI_API_KEY: Optional[str] = os.environ.get('BRAPI_API_KEY')
    BRAPI_ENABLED: bool = True  # Funciona com e sem API key
    
    # Yahoo Finance
    YAHOO_ENABLED: bool = True  # Gratuito
    
    # InvestPy
    INVESTPY_ENABLED: bool = True  # Gratuito
    
    # MFinance
    MFINANCE_ENABLED: bool = True  # Gratuito
    
    # Configurações gerais
    DEFAULT_TIMEOUT: int = 10  # segundos
    MAX_RETRIES: int = 3
    CACHE_DURATION: int = 300  # 5 minutos em segundos
    
    @classmethod
    def get_provider_priority(cls) -> list:
        """Retorna a ordem de prioridade dos provedores"""
        return [
            'MFinance',        # 1º - API brasileira gratuita e confiável
            'HG Finance',      # 2º - API brasileira com chave
            'BrAPI',           # 3º - API brasileira com chave
            'Yahoo Finance',   # 4º - Confiável e gratuito
            'InvestPy',        # 5º - Especializado em dados brasileiros
            'Alpha Vantage',   # 6º - Boa qualidade mas requer API key
            'Quandl',          # 7º - Datasets variados mas nem sempre atualizados
        ]
    
    @classmethod
    def get_enabled_providers(cls) -> dict:
        """Retorna status dos provedores habilitados"""
        return {
            'MFinance': cls.MFINANCE_ENABLED,
            'HG Finance': cls.HG_FINANCE_ENABLED,
            'BrAPI': cls.BRAPI_ENABLED,
            'Yahoo Finance': cls.YAHOO_ENABLED,
            'InvestPy': cls.INVESTPY_ENABLED,
            'Alpha Vantage': cls.ALPHA_VANTAGE_ENABLED,
            'Quandl': cls.QUANDL_ENABLED,
        }
    
    @classmethod
    def get_api_keys_status(cls) -> dict:
        """Retorna status das API keys"""
        return {
            'HG Finance': 'Configurada' if cls.HG_FINANCE_API_KEY else 'Não configurada (funciona com limitações)',
            'BrAPI': 'Configurada' if cls.BRAPI_API_KEY else 'Não configurada (funciona com limitações)',
            'Alpha Vantage': 'Configurada' if cls.ALPHA_VANTAGE_API_KEY else 'Não configurada',
            'Quandl': 'Configurada' if cls.QUANDL_API_KEY else 'Não configurada (funciona com limitações)',
        }

# Instruções para configurar API keys
API_SETUP_INSTRUCTIONS = {
    'HG Finance': {
        'url': 'https://hgbrasil.com/status/finance',
        'free_tier': 'Limitado sem chave, mais requisições com chave',
        'env_var': 'HG_FINANCE_API_KEY',
        'setup': 'export HG_FINANCE_API_KEY=your_api_key_here'
    },
    'BrAPI': {
        'url': 'https://brapi.dev/',
        'free_tier': 'Limitado sem chave, mais requisições com chave',
        'env_var': 'BRAPI_API_KEY',
        'setup': 'export BRAPI_API_KEY=your_api_key_here'
    },
    'Alpha Vantage': {
        'url': 'https://www.alphavantage.co/support/#api-key',
        'free_tier': '5 calls per minute, 500 calls per day',
        'env_var': 'ALPHA_VANTAGE_API_KEY',
        'setup': 'export ALPHA_VANTAGE_API_KEY=your_api_key_here'
    },
    'Quandl': {
        'url': 'https://www.quandl.com/account/api',
        'free_tier': '50 calls per day without key, unlimited with key',
        'env_var': 'QUANDL_API_KEY',
        'setup': 'export QUANDL_API_KEY=your_api_key_here'
    }
} 