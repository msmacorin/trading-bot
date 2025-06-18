import { Stock, Portfolio, StockAnalysis } from '../types';

// URL da API - detecta automaticamente o ambiente
const getApiUrl = () => {
  // Se estamos rodando no Docker (container), usa o nome do container
  if (window.location.hostname === 'localhost' && window.location.port === '3000') {
    // Acessado de fora do Docker, usa localhost
    return 'http://localhost:8000';
  }
  // Se estamos rodando dentro do Docker, usa o nome do container
  if (window.location.hostname === 'trading-web') {
    return 'http://trading-api:8001';
  }
  // Se estamos acessando de outra máquina, usa o IP/hostname da máquina atual
  return `http://${window.location.hostname}:8000`;
};

const API_BASE_URL = getApiUrl();

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log('API Request:', url); // Debug log
    
    // Adiciona o token de autenticação se existir
    const token = localStorage.getItem('trading_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
      headers,
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Stocks endpoints
  async getStocks(): Promise<Stock[]> {
    return this.request<Stock[]>('/api/acoes');
  }

  async addStock(codigo: string): Promise<Stock> {
    return this.request<Stock>('/api/acoes', {
      method: 'POST',
      body: JSON.stringify({ codigo }),
    });
  }

  async deleteStock(codigo: string): Promise<void> {
    return this.request<void>(`/api/acoes/${codigo}`, {
      method: 'DELETE',
    });
  }

  async activateStock(codigo: string): Promise<Stock> {
    return this.request<Stock>(`/api/acoes/${codigo}/ativar`, {
      method: 'PATCH',
    });
  }

  async deactivateStock(codigo: string): Promise<Stock> {
    return this.request<Stock>(`/api/acoes/${codigo}/desativar`, {
      method: 'PATCH',
    });
  }

  // Portfolio endpoints
  async getPortfolio(): Promise<Portfolio[]> {
    return this.request<Portfolio[]>('/api/carteira');
  }

  async addToPortfolio(portfolio: Omit<Portfolio, 'id' | 'created_at' | 'updated_at'>): Promise<Portfolio> {
    return this.request<Portfolio>('/api/carteira', {
      method: 'POST',
      body: JSON.stringify(portfolio),
    });
  }

  async updatePortfolio(codigo: string, updates: Partial<Portfolio>): Promise<Portfolio> {
    const params = new URLSearchParams();
    Object.keys(updates).forEach((key) => {
      const value = updates[key as keyof Portfolio];
      if (value !== undefined) {
        params.append(key, value.toString());
      }
    });

    return this.request<Portfolio>(`/api/carteira/${codigo}?${params}`, {
      method: 'PATCH',
    });
  }

  async removeFromPortfolio(codigo: string): Promise<void> {
    return this.request<void>(`/api/carteira/${codigo}`, {
      method: 'DELETE',
    });
  }

  // Analysis endpoint
  async getStockAnalysis(codigo: string): Promise<StockAnalysis> {
    return this.request<StockAnalysis>(`/api/acoes/${codigo}/analise`);
  }
}

export const apiService = new ApiService(); 