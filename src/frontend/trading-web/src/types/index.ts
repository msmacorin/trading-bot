export interface Stock {
  id?: number;
  codigo: string;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Portfolio {
  id?: number;
  codigo: string;
  quantidade: number;
  preco_medio: number;
  stop_loss: number;
  take_profit: number;
  created_at?: string;
  updated_at?: string;
}

export interface StockAnalysis {
  codigo: string;
  current_position: 'BUY' | 'SELL' | 'HOLD';
  new_position: 'BUY' | 'SELL' | 'WAIT';
  price: number;
  stop_loss: number;
  take_profit: number;
  profit_pct: number;
  rsi: number;
  macd: number;
  trend: 'UP' | 'DOWN';
  conditions: string[];
} 