import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { StockAnalysis } from '../types';
import { apiService } from '../services/api';

const AnaliseIndividualPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stockCode, setStockCode] = useState(searchParams.get('codigo') || '');
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stockCode.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const result = await apiService.getStockAnalysis(stockCode.trim().toUpperCase());
      setAnalysis(result);
      setSearchParams({ codigo: stockCode.trim().toUpperCase() });
    } catch (err) {
      setError('Erro ao analisar ação. Verifique o código e tente novamente.');
      console.error('Erro na análise:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPositionColor = (position: string) => {
    switch (position) {
      case 'BUY': return 'text-green-600';
      case 'SELL': return 'text-red-600';
      case 'HOLD': return 'text-yellow-600';
      case 'WAIT': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getPositionText = (position: string) => {
    switch (position) {
      case 'BUY': return 'COMPRAR';
      case 'SELL': return 'VENDER';
      case 'HOLD': return 'MANTER';
      case 'WAIT': return 'AGUARDAR';
      default: return position;
    }
  };

  const getRSIColor = (rsi: number) => {
    if (rsi < 30) return 'text-green-600';
    if (rsi > 70) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getRSIStatus = (rsi: number) => {
    if (rsi < 30) return 'Sobrevenda';
    if (rsi > 70) return 'Sobrecompra';
    return 'Neutro';
  };

  const getTrendColor = (trend: string) => {
    return trend === 'UP' ? 'text-green-600' : 'text-red-600';
  };

  const getMACDColor = (macd: number) => {
    return macd > 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="main-content">
      <div className="page-header">
        <h1 className="page-title">Análise Individual</h1>
      </div>

      {/* Formulário de análise */}
      <div className="analysis-form">
        <form onSubmit={handleAnalyze} className="form-container">
          <div className="form-group">
            <label className="form-label">Código da Ação</label>
            <div className="input-group">
              <input
                type="text"
                className="form-input"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                placeholder="Ex: PETR4.SA"
                required
              />
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !stockCode.trim()}
              >
                {loading ? 'Analisando...' : 'Analisar'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Resultados da análise */}
      {analysis && (
        <div className="analysis-results">
          <div className="results-header">
            <h2 className="results-title">Análise de {analysis.codigo}</h2>
            <div className="price-display">
              <span className="price-label">Preço Atual:</span>
              <span className="price-value">R$ {analysis.price.toFixed(2)}</span>
            </div>
          </div>

          {/* Recomendações */}
          <div className="recommendations-section">
            <h3>📊 Recomendações</h3>
            <div className="recommendations-grid">
              <div className="recommendation-card">
                <h4>Para quem já tem a ação:</h4>
                <div className={`recommendation-value ${getPositionColor(analysis.current_position)}`}>
                  {getPositionText(analysis.current_position)}
                </div>
              </div>
              <div className="recommendation-card">
                <h4>Para quem está avaliando comprar:</h4>
                <div className={`recommendation-value ${getPositionColor(analysis.new_position)}`}>
                  {getPositionText(analysis.new_position)}
                </div>
              </div>
            </div>
          </div>

          {/* Indicadores Técnicos */}
          <div className="indicators-section">
            <h3>📈 Indicadores Técnicos</h3>
            <div className="indicators-grid">
              <div className="indicator-card">
                <h4>RSI (14)</h4>
                <div className={`indicator-value ${getRSIColor(analysis.rsi)}`}>
                  {analysis.rsi.toFixed(2)}
                </div>
                <div className="indicator-status">{getRSIStatus(analysis.rsi)}</div>
              </div>
              <div className="indicator-card">
                <h4>MACD</h4>
                <div className={`indicator-value ${getMACDColor(analysis.macd)}`}>
                  {analysis.macd.toFixed(4)}
                </div>
                <div className="indicator-status">
                  {analysis.macd > 0 ? 'Positivo' : 'Negativo'}
                </div>
              </div>
              <div className="indicator-card">
                <h4>Tendência</h4>
                <div className={`indicator-value ${getTrendColor(analysis.trend)}`}>
                  {analysis.trend}
                </div>
                <div className="indicator-status">
                  {analysis.trend === 'UP' ? 'Alta' : 'Baixa'}
                </div>
              </div>
              <div className="indicator-card">
                <h4>Variação no Período</h4>
                <div className={`indicator-value ${analysis.profit_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {analysis.profit_pct >= 0 ? '+' : ''}{analysis.profit_pct.toFixed(2)}%
                </div>
                <div className="indicator-status">
                  {analysis.profit_pct >= 0 ? 'Lucro' : 'Prejuízo'}
                </div>
              </div>
            </div>
          </div>

          {/* Sugestões de Preço */}
          <div className="price-suggestions-section">
            <h3>💰 Sugestões de Preço</h3>
            <div className="price-suggestions-grid">
              <div className="price-suggestion-card">
                <h4>Stop Loss</h4>
                <div className="price-suggestion-value text-red-600">
                  R$ {analysis.stop_loss.toFixed(2)}
                </div>
                <div className="price-suggestion-desc">
                  Preço para limitar perdas (-3%)
                </div>
              </div>
              <div className="price-suggestion-card">
                <h4>Take Profit</h4>
                <div className="price-suggestion-value text-green-600">
                  R$ {analysis.take_profit.toFixed(2)}
                </div>
                <div className="price-suggestion-desc">
                  Preço para realizar lucros (+5%)
                </div>
              </div>
            </div>
          </div>

          {/* Condições Identificadas */}
          <div className="conditions-section">
            <h3>🔍 Condições Identificadas</h3>
            <div className="conditions-list">
              {analysis.conditions.map((condition, index) => (
                <div key={index} className="condition-item">
                  <span className="condition-bullet">•</span>
                  <span className="condition-text">{condition}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Aviso Legal */}
          <div className="legal-warning">
            <h3>⚠️ Aviso Importante</h3>
            <p>
              Esta é uma análise automatizada baseada em indicadores técnicos. 
              Sempre faça sua própria análise fundamental e técnica antes de tomar 
              decisões de investimento. O passado não garante resultados futuros.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnaliseIndividualPage; 