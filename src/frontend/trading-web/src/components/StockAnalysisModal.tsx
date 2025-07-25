import React, { useEffect, useState } from 'react';
import { StockAnalysis } from '../types';
import { apiService } from '../services/api';

interface StockAnalysisModalProps {
  open: boolean;
  onClose: () => void;
  codigo: string | null;
}

const StockAnalysisModal: React.FC<StockAnalysisModalProps> = ({ open, onClose, codigo }) => {
  const [analysisData, setAnalysisData] = useState<(StockAnalysis & { data_source?: string }) | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && codigo) {
      fetchAnalysis();
    } else {
      setAnalysisData(null);
      setError(null);
    }
    // eslint-disable-next-line
  }, [open, codigo]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      if (!codigo) return;
      // Primeiro tenta buscar do cache
      const cacheStats = await apiService.get<any>('/api/system/cache/stats');
      if (cacheStats.cache_active && cacheStats.stocks_analysis && codigo && cacheStats.stocks_analysis[codigo]) {
        setAnalysisData(cacheStats.stocks_analysis[codigo].analysis);
      } else {
        // Se não há no cache, faz análise individual
        const analysis = await apiService.getStockAnalysis(codigo);
        setAnalysisData(analysis);
      }
    } catch (err) {
      setError('Erro ao buscar análise da ação');
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  if (!open || !codigo) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Análise de {codigo}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        {loading ? (
          <div className="loading">Carregando análise...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : analysisData ? (
          <div className="analysis-details">
            <div className="analysis-header">
              <h3>📊 Análise Técnica</h3>
              <div className="analysis-badges">
                <span className={`badge ${analysisData.current_position.toLowerCase()}`}>{analysisData.current_position}</span>
                <span className={`badge ${analysisData.new_position.toLowerCase()}`}>{analysisData.new_position}</span>
              </div>
            </div>
            <div className="analysis-grid">
              <div className="analysis-card">
                <div className="card-header">💰 Preços</div>
                <div className="card-content">
                  <div className="metric">
                    <span className="label">Preço Atual:</span>
                    <span className="value">R$ {analysisData.price.toFixed(2)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Stop Loss:</span>
                    <span className="value">R$ {analysisData.stop_loss.toFixed(2)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Take Profit:</span>
                    <span className="value">R$ {analysisData.take_profit.toFixed(2)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Variação:</span>
                    <span className={`value ${analysisData.profit_pct >= 0 ? 'positive' : 'negative'}`}>{analysisData.profit_pct.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
              <div className="analysis-card">
                <div className="card-header">📈 Indicadores</div>
                <div className="card-content">
                  <div className="metric">
                    <span className="label">RSI:</span>
                    <span className={`value ${analysisData.rsi < 30 ? 'buy-signal' : analysisData.rsi > 70 ? 'sell-signal' : 'neutral'}`}>{analysisData.rsi.toFixed(1)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">MACD:</span>
                    <span className={`value ${analysisData.macd > 0 ? 'positive' : 'negative'}`}>{analysisData.macd.toFixed(3)}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Tendência:</span>
                    <span className={`value ${analysisData.trend.toLowerCase()}`}>{analysisData.trend === 'UP' ? '⬆️ Alta' : '⬇️ Baixa'}</span>
                  </div>
                </div>
              </div>
              <div className="analysis-card">
                <div className="card-header">🎯 Recomendações</div>
                <div className="card-content">
                  <div className="recommendation">
                    <strong>Para quem possui:</strong>
                    <span className={`rec-value ${analysisData.current_position.toLowerCase()}`}>
                      {analysisData.current_position === 'BUY' ? '🟢 Comprar Mais' : analysisData.current_position === 'SELL' ? '🔴 Vender' : '⚪ Manter'}
                    </span>
                  </div>
                  <div className="recommendation">
                    <strong>Para quem não possui:</strong>
                    <span className={`rec-value ${analysisData.new_position.toLowerCase()}`}>
                      {analysisData.new_position === 'BUY' ? '🟢 Comprar' : analysisData.new_position === 'WAIT' ? '⏳ Aguardar' : '❌ Evitar'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            {analysisData.conditions && analysisData.conditions.length > 0 && (
              <div className="analysis-conditions">
                <h4>🔍 Condições Identificadas</h4>
                <div className="conditions-list">
                  {analysisData.conditions.map((condition, index) => (
                    <div key={index} className="condition-item">{condition}</div>
                  ))}
                </div>
              </div>
            )}
            {analysisData.data_source && (
              <div className="analysis-footer">
                <small>📡 Fonte dos dados: {analysisData.data_source}</small>
              </div>
            )}
          </div>
        ) : (
          <div className="empty-state">
            <h3>Nenhuma análise disponível para {codigo}</h3>
            <p>Faça uma análise manual para obter detalhes.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockAnalysisModal; 