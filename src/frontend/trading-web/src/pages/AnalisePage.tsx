import React, { useState, useEffect } from 'react';
import { Stock } from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface CacheStats {
  cache_active: boolean;
  cache_size: number;
  last_update: string | null;
  cache_age_seconds: number;
  total_users_affected: number;
  message: string;
}

const AnalisePage: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newStockCode, setNewStockCode] = useState('');
  const [addingStock, setAddingStock] = useState(false);
  const [updatingStock, setUpdatingStock] = useState<string | null>(null);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [loadingCache, setLoadingCache] = useState(false);
  const [forcingAnalysis, setForcingAnalysis] = useState(false);

  useEffect(() => {
    loadStocks();
  }, []);

  const loadStocks = async () => {
    try {
      setLoading(true);
      const data = await apiService.getStocks();
      setStocks(data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar ações');
      console.error('Erro ao carregar ações:', err);
    } finally {
      setLoading(false);
    }
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

  const handleAddStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStockCode.trim()) return;

    // Valida o código antes de enviar
    const validationError = validateStockCode(newStockCode);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setAddingStock(true);
      // Remove .SA se presente e normaliza
      const normalizedCode = newStockCode.trim().toUpperCase().replace('.SA', '');
      await apiService.addStock(normalizedCode);
      setNewStockCode('');
      setShowAddModal(false);
      await loadStocks();
    } catch (err: any) {
      // Exibe erro mais específico se disponível
      const errorMessage = err.response?.data?.detail || 'Erro ao adicionar ação';
      setError(errorMessage);
      console.error('Erro ao adicionar ação:', err);
    } finally {
      setAddingStock(false);
    }
  };

  const handleDeleteStock = async (codigo: string) => {
    if (!window.confirm(`Tem certeza que deseja excluir a ação ${codigo}?`)) {
      return;
    }

    try {
      await apiService.deleteStock(codigo);
      await loadStocks();
    } catch (err) {
      setError('Erro ao excluir ação');
      console.error('Erro ao excluir ação:', err);
    }
  };

  const handleToggleStockStatus = async (codigo: string, ativo: boolean) => {
    try {
      setUpdatingStock(codigo);
      if (ativo) {
        await apiService.deactivateStock(codigo);
      } else {
        await apiService.activateStock(codigo);
      }
      await loadStocks();
    } catch (err) {
      setError(`Erro ao ${ativo ? 'desativar' : 'ativar'} ação`);
      console.error(`Erro ao ${ativo ? 'desativar' : 'ativar'} ação:`, err);
    } finally {
      setUpdatingStock(null);
    }
  };

  const fetchCacheStats = async () => {
    try {
      setLoadingCache(true);
      const response = await apiService.get<CacheStats>('/api/system/cache/status');
      setCacheStats(response);
    } catch (error) {
      console.error('Erro ao buscar estatísticas do cache:', error);
    } finally {
      setLoadingCache(false);
    }
  };

  const forceAnalysis = async () => {
    try {
      setForcingAnalysis(true);
      await apiService.post('/api/system/cache/force-analysis');
      // Atualiza as estatísticas após 5 segundos
      setTimeout(() => {
        fetchCacheStats();
      }, 5000);
    } catch (error) {
      console.error('Erro ao forçar análise:', error);
      setError('Erro ao forçar análise. Tente novamente.');
    } finally {
      setForcingAnalysis(false);
    }
  };

  useEffect(() => {
    fetchCacheStats();
    // Atualiza as estatísticas a cada 30 segundos
    const interval = setInterval(fetchCacheStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="main-content">
        <div className="loading">Carregando ações...</div>
      </div>
    );
  }

  return (
    <div className="analise-page">
      <div className="page-header">
        <h1>🤖 Análise de Ações</h1>
        <p>Sistema inteligente de análise técnica com cache otimizado</p>
      </div>

      {/* Seção de estatísticas do cache */}
      <div className="cache-stats-section">
        <div className="cache-stats-header">
          <h2>📊 Sistema de Cache Otimizado</h2>
          <button 
            onClick={forceAnalysis} 
            disabled={forcingAnalysis}
            className="force-analysis-btn"
          >
            {forcingAnalysis ? '🔄 Analisando...' : '🚀 Forçar Análise'}
          </button>
        </div>
        
        {loadingCache ? (
          <div className="loading">🔄 Carregando estatísticas...</div>
        ) : cacheStats ? (
          <div className="cache-stats-grid">
            <div className="cache-stat-card">
              <div className="stat-icon">🎯</div>
              <div className="stat-content">
                <div className="stat-value">{cacheStats.cache_size}</div>
                <div className="stat-label">Ações no Cache</div>
              </div>
            </div>
            
            <div className="cache-stat-card">
              <div className="stat-icon">👥</div>
              <div className="stat-content">
                <div className="stat-value">{cacheStats.total_users_affected}</div>
                <div className="stat-label">Usuários Afetados</div>
              </div>
            </div>
            
            <div className="cache-stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-value">
                  {cacheStats.cache_age_seconds ? `${Math.floor(cacheStats.cache_age_seconds / 60)}m` : 'N/A'}
                </div>
                <div className="stat-label">Idade do Cache</div>
              </div>
            </div>
            
            <div className="cache-stat-card">
              <div className="stat-icon">{cacheStats.cache_active ? '✅' : '❌'}</div>
              <div className="stat-content">
                <div className="stat-value">{cacheStats.cache_active ? 'Ativo' : 'Inativo'}</div>
                <div className="stat-label">Status do Cache</div>
              </div>
            </div>
          </div>
        ) : null}
        
        <div className="cache-info">
          <h3>🚀 Como funciona o sistema otimizado:</h3>
          <ul>
            <li>📈 <strong>Uma análise por ação:</strong> Cada ação é analisada apenas uma vez por ciclo</li>
            <li>👥 <strong>Compartilhamento:</strong> O resultado é compartilhado entre todos os usuários que possuem a ação</li>
            <li>⚡ <strong>Eficiência:</strong> Reduz drasticamente o tempo de análise e uso de recursos</li>
            <li>🔄 <strong>Atualização automática:</strong> Cache renovado a cada hora durante horário de mercado</li>
          </ul>
        </div>
      </div>

      <div className="main-content">
        <div className="page-header">
          <h1 className="page-title">Ações em Análise</h1>
          <button 
            className="btn btn-primary"
            onClick={() => setShowAddModal(true)}
          >
            Adicionar Ação
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="table-container">
          {stocks.length === 0 ? (
            <div className="empty-state">
              <h3>Nenhuma ação em análise</h3>
              <p>Adicione ações para começar a monitorar</p>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Status</th>
                  <th>Data de Criação</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {stocks.map((stock) => (
                  <tr key={stock.codigo}>
                    <td>
                      <span className="stock-code">{stock.codigo}</span>
                    </td>
                    <td>
                      <span className={stock.ativo ? 'status-active' : 'status-inactive'}>
                        {stock.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td>
                      {stock.created_at ? new Date(stock.created_at).toLocaleDateString('pt-BR') : '-'}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className={`btn ${stock.ativo ? 'btn-warning' : 'btn-success'}`}
                          onClick={() => handleToggleStockStatus(stock.codigo, stock.ativo)}
                          disabled={updatingStock === stock.codigo}
                        >
                          {updatingStock === stock.codigo 
                            ? 'Atualizando...' 
                            : stock.ativo ? 'Desativar' : 'Ativar'
                          }
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleDeleteStock(stock.codigo)}
                          disabled={updatingStock === stock.codigo}
                        >
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Modal para adicionar ação */}
        {showAddModal && (
          <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="modal-title">Adicionar Ação</h2>
                <button 
                  className="modal-close" 
                  onClick={() => setShowAddModal(false)}
                >
                  ×
                </button>
              </div>
              <form onSubmit={handleAddStock}>
                <div className="form-group">
                  <label className="form-label">Código da Ação</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newStockCode}
                    onChange={(e) => setNewStockCode(e.target.value)}
                    placeholder="Ex: PETR4, VALE3F, MGLU3.SA"
                    required
                  />
                  <small className="form-help">
                    Formatos aceitos: PETR4, VALE3F (fracionária), MGLU3.SA
                  </small>
                </div>
                <div className="form-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowAddModal(false)}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={addingStock}
                  >
                    {addingStock ? 'Adicionando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalisePage; 