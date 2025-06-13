import { Stock, Portfolio, StockAnalysis } from '../types';

// URL da API - detecta automaticamente o ambiente
const getApiUrl = () => {
  // Se estamos rodando no Docker (container), usa o nome do container
  if (window.location.hostname === 'localhost' && window.location.port === '3000') {
    // Acessado de fora do Docker, usa localhost
    return 'http://localhost:8001';
  }
  // Se estamos rodando dentro do Docker, usa o nome do container
  return 'http://trading-api:8001';
};

const API_BASE_URL = getApiUrl();

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log('API Request:', url); // Debug log
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Stocks endpoints
  async getStocks(): Promise<Stock[]> {
    return this.request<Stock[]>('/acoes/');
  }

  async addStock(codigo: string): Promise<Stock> {
    return this.request<Stock>('/acoes/', {
      method: 'POST',
      body: JSON.stringify({ codigo }),
    });
  }

  async deleteStock(codigo: string): Promise<void> {
    return this.request<void>(`/acoes/${codigo}`, {
      method: 'DELETE',
    });
  }

  async activateStock(codigo: string): Promise<Stock> {
    return this.request<Stock>(`/acoes/${codigo}/ativar`, {
      method: 'PATCH',
    });
  }

  async deactivateStock(codigo: string): Promise<Stock> {
    return this.request<Stock>(`/acoes/${codigo}/desativar`, {
      method: 'PATCH',
    });
  }

  // Portfolio endpoints
  async getPortfolio(): Promise<Portfolio[]> {
    return this.request<Portfolio[]>('/carteira/');
  }

  async addToPortfolio(portfolio: Omit<Portfolio, 'id' | 'created_at' | 'updated_at'>): Promise<Portfolio> {
    return this.request<Portfolio>('/carteira/', {
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

    return this.request<Portfolio>(`/carteira/${codigo}?${params}`, {
      method: 'PATCH',
    });
  }

  async removeFromPortfolio(codigo: string): Promise<void> {
    return this.request<void>(`/carteira/${codigo}`, {
      method: 'DELETE',
    });
  }

  // Analysis endpoint
  async getStockAnalysis(codigo: string): Promise<StockAnalysis> {
    return this.request<StockAnalysis>(`/acoes/${codigo}/analise`);
  }
}

export const apiService = new ApiService(); 