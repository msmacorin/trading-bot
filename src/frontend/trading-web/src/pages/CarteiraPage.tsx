import React, { useState, useEffect } from 'react';
import { Portfolio, StockAnalysis } from '../types';
import { apiService } from '../services/api';

interface CacheData {
  analysis: StockAnalysis & { data_source?: string };
  user_ids: number[];
  analyzed_at: string;
}

interface CacheStats {
  cache_active: boolean;
  cache_size: number;
  last_update: string | null;
  cache_age_seconds: number;
  total_users_affected: number;
  stocks_analysis?: { [key: string]: CacheData };
}

const CarteiraPage: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newStock, setNewStock] = useState({ codigo: '', quantidade: '', preco_medio: '', stop_loss: '', take_profit: '' });
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<null | Portfolio>(null);
  const [updating, setUpdating] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);
  const [sellStock, setSellStock] = useState<Portfolio | null>(null);
  const [sellData, setSellData] = useState({ quantidade_vendida: '', preco_venda: '' });
  const [selling, setSelling] = useState(false);
  
  // Estados para análise
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisStock, setAnalysisStock] = useState<Portfolio | null>(null);
  const [analysisData, setAnalysisData] = useState<(StockAnalysis & { data_source?: string }) | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const data = await apiService.getPortfolio();
      setPortfolio(data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar carteira');
      console.error('Erro ao carregar carteira:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStockAnalysis = async (codigo: string) => {
    try {
      setLoadingAnalysis(true);
      
      // Primeiro tenta buscar do cache
      const cacheStats = await apiService.get<CacheStats>('/api/system/cache/stats');
      
      if (cacheStats.cache_active && cacheStats.stocks_analysis && cacheStats.stocks_analysis[codigo]) {
        // Usa dados do cache
        const cacheData = cacheStats.stocks_analysis[codigo];
        setAnalysisData(cacheData.analysis);
      } else {
        // Se não há no cache, faz análise individual
        const analysis = await apiService.getStockAnalysis(codigo);
        setAnalysisData(analysis);
      }
    } catch (error) {
      console.error('Erro ao buscar análise:', error);
      setError('Erro ao buscar análise da ação');
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleShowAnalysis = async (item: Portfolio) => {
    setAnalysisStock(item);
    setShowAnalysisModal(true);
    await getStockAnalysis(item.codigo);
  };

  const closeAnalysisModal = () => {
    setShowAnalysisModal(false);
    setAnalysisStock(null);
    setAnalysisData(null);
  };

  const validateStockCode = (code: string): string | null => {
    const cleaned = code.trim().toUpperCase();
    
    // Remove .SA se presente
    const normalized = cleaned.replace('.SA', '');
    
    // Valida formato básico: 4 letras + 1-2 números + F opcional
    const regex = /^[A-Z]{4}\d{1,2}F?$/;
    if (!regex.test(normalized)) {
      return 'Formato inválido. Use formato como PETR4, VALE3F, MGLU3, etc.';
    }
    
    return null;
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStock.codigo.trim() || !newStock.quantidade || !newStock.preco_medio) return;
    
    // Valida o código antes de enviar
    const validationError = validateStockCode(newStock.codigo);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    try {
      setAdding(true);
      // Remove .SA se presente e normaliza
      const normalizedCode = newStock.codigo.trim().toUpperCase().replace('.SA', '');
      await apiService.addToPortfolio({
        codigo: normalizedCode,
        quantidade: Number(newStock.quantidade),
        preco_medio: Number(newStock.preco_medio),
        stop_loss: newStock.stop_loss ? Number(newStock.stop_loss) : 0,
        take_profit: newStock.take_profit ? Number(newStock.take_profit) : 0,
      });
      setShowAddModal(false);
      setNewStock({ codigo: '', quantidade: '', preco_medio: '', stop_loss: '', take_profit: '' });
      await loadPortfolio();
    } catch (err: any) {
      // Exibe erro mais específico se disponível
      const errorMessage = err.response?.data?.detail || 'Erro ao adicionar ativo na carteira';
      setError(errorMessage);
      console.error('Erro ao adicionar ativo:', err);
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (codigo: string) => {
    if (!window.confirm(`Tem certeza que deseja remover ${codigo} da carteira?`)) return;
    try {
      await apiService.removeFromPortfolio(codigo);
      await loadPortfolio();
    } catch (err) {
      setError('Erro ao remover ativo da carteira');
      console.error('Erro ao remover ativo:', err);
    }
  };

  const handleEdit = (item: Portfolio) => {
    setEditing(item);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    try {
      setUpdating(true);
      await apiService.updatePortfolio(editing.codigo, {
        quantidade: editing.quantidade,
        preco_medio: editing.preco_medio,
        stop_loss: editing.stop_loss,
        take_profit: editing.take_profit,
      });
      setEditing(null);
      await loadPortfolio();
    } catch (err) {
      setError('Erro ao atualizar ativo da carteira');
      console.error('Erro ao atualizar ativo:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleSell = (stock: Portfolio) => {
    setSellStock(stock);
    setSellData({ quantidade_vendida: '', preco_venda: '' });
    setShowSellModal(true);
  };

  const handleSellSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sellStock || !sellData.quantidade_vendida || !sellData.preco_venda) return;

    try {
      setSelling(true);
      await apiService.sellStock(sellStock.codigo, {
        quantidade_vendida: Number(sellData.quantidade_vendida),
        preco_venda: Number(sellData.preco_venda)
      });
      setShowSellModal(false);
      setSellStock(null);
      setSellData({ quantidade_vendida: '', preco_venda: '' });
      await loadPortfolio();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao executar venda';
      setError(errorMessage);
      console.error('Erro ao vender ação:', err);
    } finally {
      setSelling(false);
    }
  };

  if (loading) {
    return <div className="main-content"><div className="loading">Carregando carteira...</div></div>;
  }

  return (
    <div className="main-content">
      <div className="page-header">
        <h1 className="page-title">Carteira</h1>
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>Adicionar Ativo</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="table-container">
        {portfolio.length === 0 ? (
          <div className="empty-state">
            <h3>Nenhum ativo na carteira</h3>
            <p>Adicione ativos para começar a acompanhar</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Quantidade</th>
                <th>Preço Médio</th>
                <th>Stop Loss</th>
                <th>Take Profit</th>
                <th>Data de Criação</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((item) => (
                <tr key={item.codigo}>
                  <td><span className="stock-code">{item.codigo}</span></td>
                  <td>{item.quantidade}</td>
                  <td>R$ {item.preco_medio.toFixed(2)}</td>
                  <td>R$ {item.stop_loss.toFixed(2)}</td>
                  <td>R$ {item.take_profit.toFixed(2)}</td>
                  <td>{item.created_at ? new Date(item.created_at).toLocaleDateString('pt-BR') : '-'}</td>
                  <td>
                    <div className="action-buttons">
                      <button className="btn btn-success" onClick={() => handleSell(item)}>Vender</button>
                      <button className="btn btn-warning" onClick={() => handleEdit(item)}>Editar</button>
                      <button className="btn btn-danger" onClick={() => handleDelete(item.codigo)}>Remover</button>
                      <button className="btn btn-info" onClick={() => handleShowAnalysis(item)}>Analisar</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {/* Modal para adicionar ativo */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Adicionar Ativo</h2>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            <form onSubmit={handleAdd}>
              <div className="form-group">
                <label className="form-label">Código</label>
                <input type="text" className="form-input" value={newStock.codigo} onChange={e => setNewStock({ ...newStock, codigo: e.target.value })} placeholder="Ex: PETR4.SA" required />
              </div>
              <div className="form-group">
                <label className="form-label">Quantidade</label>
                <input type="number" className="form-input" value={newStock.quantidade} onChange={e => setNewStock({ ...newStock, quantidade: e.target.value })} required min={1} />
              </div>
              <div className="form-group">
                <label className="form-label">Preço Médio</label>
                <input type="number" className="form-input" value={newStock.preco_medio} onChange={e => setNewStock({ ...newStock, preco_medio: e.target.value })} required min={0} step={0.01} />
              </div>
              <div className="form-group">
                <label className="form-label">Stop Loss</label>
                <input type="number" className="form-input" value={newStock.stop_loss} onChange={e => setNewStock({ ...newStock, stop_loss: e.target.value })} min={0} step={0.01} />
              </div>
              <div className="form-group">
                <label className="form-label">Take Profit</label>
                <input type="number" className="form-input" value={newStock.take_profit} onChange={e => setNewStock({ ...newStock, take_profit: e.target.value })} min={0} step={0.01} />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" disabled={adding}>{adding ? 'Adicionando...' : 'Adicionar'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Modal para editar ativo */}
      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Editar Ativo</h2>
              <button className="modal-close" onClick={() => setEditing(null)}>×</button>
            </div>
            <form onSubmit={handleUpdate}>
              <div className="form-group">
                <label className="form-label">Quantidade</label>
                <input type="number" className="form-input" value={editing.quantidade} onChange={e => setEditing({ ...editing, quantidade: Number(e.target.value) } as Portfolio)} required min={1} />
              </div>
              <div className="form-group">
                <label className="form-label">Preço Médio</label>
                <input type="number" className="form-input" value={editing.preco_medio} onChange={e => setEditing({ ...editing, preco_medio: Number(e.target.value) } as Portfolio)} required min={0} step={0.01} />
              </div>
              <div className="form-group">
                <label className="form-label">Stop Loss</label>
                <input type="number" className="form-input" value={editing.stop_loss} onChange={e => setEditing({ ...editing, stop_loss: Number(e.target.value) } as Portfolio)} min={0} step={0.01} />
              </div>
              <div className="form-group">
                <label className="form-label">Take Profit</label>
                <input type="number" className="form-input" value={editing.take_profit} onChange={e => setEditing({ ...editing, take_profit: Number(e.target.value) } as Portfolio)} min={0} step={0.01} />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setEditing(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" disabled={updating}>{updating ? 'Salvando...' : 'Salvar'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal para vender ação */}
      {showSellModal && sellStock && (
        <div className="modal-overlay" onClick={() => setShowSellModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Vender {sellStock.codigo}</h2>
              <button className="modal-close" onClick={() => setShowSellModal(false)}>×</button>
            </div>
            <form onSubmit={handleSellSubmit}>
              <div className="form-group">
                <label className="form-label">Quantidade Disponível</label>
                <input type="text" className="form-input" value={sellStock.quantidade} disabled />
              </div>
              
              <div className="form-group">
                <label className="form-label">Quantidade a Vender</label>
                <input
                  type="number"
                  className="form-input"
                  value={sellData.quantidade_vendida}
                  onChange={(e) => setSellData({...sellData, quantidade_vendida: e.target.value})}
                  placeholder="Digite a quantidade"
                  min="1"
                  max={sellStock.quantidade}
                  required
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Preço de Venda (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-input"
                  value={sellData.preco_venda}
                  onChange={(e) => setSellData({...sellData, preco_venda: e.target.value})}
                  placeholder="Digite o preço de venda"
                  min="0.01"
                  required
                />
              </div>
              
              <div className="form-group">
                <div className="sell-info">
                  <p><strong>Preço Médio de Compra:</strong> R$ {sellStock.preco_medio.toFixed(2)}</p>
                  <p><strong>Stop Loss Original:</strong> R$ {sellStock.stop_loss.toFixed(2)}</p>
                  <p><strong>Take Profit Original:</strong> R$ {sellStock.take_profit.toFixed(2)}</p>
                </div>
              </div>
              
              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowSellModal(false)}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn btn-success"
                  disabled={selling}
                >
                  {selling ? 'Vendendo...' : 'Confirmar Venda'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal para análise de ação */}
      {showAnalysisModal && analysisStock && (
        <div className="modal-overlay" onClick={closeAnalysisModal}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Análise de {analysisStock.codigo}</h2>
              <button className="modal-close" onClick={closeAnalysisModal}>×</button>
            </div>
            {loadingAnalysis ? (
              <div className="loading">Carregando análise...</div>
                         ) : analysisData ? (
               <div className="analysis-details">
                 <div className="analysis-header">
                   <h3>📊 Análise Técnica</h3>
                   <div className="analysis-badges">
                     <span className={`badge ${analysisData.current_position.toLowerCase()}`}>
                       {analysisData.current_position}
                     </span>
                     <span className={`badge ${analysisData.new_position.toLowerCase()}`}>
                       {analysisData.new_position}
                     </span>
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
                         <span className={`value ${analysisData.profit_pct >= 0 ? 'positive' : 'negative'}`}>
                           {analysisData.profit_pct.toFixed(2)}%
                         </span>
                       </div>
                     </div>
                   </div>

                   <div className="analysis-card">
                     <div className="card-header">📈 Indicadores</div>
                     <div className="card-content">
                       <div className="metric">
                         <span className="label">RSI:</span>
                         <span className={`value ${analysisData.rsi < 30 ? 'buy-signal' : analysisData.rsi > 70 ? 'sell-signal' : 'neutral'}`}>
                           {analysisData.rsi.toFixed(1)}
                         </span>
                       </div>
                       <div className="metric">
                         <span className="label">MACD:</span>
                         <span className={`value ${analysisData.macd > 0 ? 'positive' : 'negative'}`}>
                           {analysisData.macd.toFixed(3)}
                         </span>
                       </div>
                       <div className="metric">
                         <span className="label">Tendência:</span>
                         <span className={`value ${analysisData.trend.toLowerCase()}`}>
                           {analysisData.trend === 'UP' ? '⬆️ Alta' : '⬇️ Baixa'}
                         </span>
                       </div>
                     </div>
                   </div>

                   <div className="analysis-card">
                     <div className="card-header">🎯 Recomendações</div>
                     <div className="card-content">
                       <div className="recommendation">
                         <strong>Para quem possui:</strong>
                         <span className={`rec-value ${analysisData.current_position.toLowerCase()}`}>
                           {analysisData.current_position === 'BUY' ? '🟢 Comprar Mais' : 
                            analysisData.current_position === 'SELL' ? '🔴 Vender' : '⚪ Manter'}
                         </span>
                       </div>
                       <div className="recommendation">
                         <strong>Para quem não possui:</strong>
                         <span className={`rec-value ${analysisData.new_position.toLowerCase()}`}>
                           {analysisData.new_position === 'BUY' ? '🟢 Comprar' : 
                            analysisData.new_position === 'WAIT' ? '⏳ Aguardar' : '❌ Evitar'}
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
                         <div key={index} className="condition-item">
                           {condition}
                         </div>
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
                <h3>Nenhuma análise disponível para {analysisStock.codigo}</h3>
                <p>Faça uma análise manual para obter detalhes.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CarteiraPage; 