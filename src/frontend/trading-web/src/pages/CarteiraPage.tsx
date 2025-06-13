import React, { useState, useEffect } from 'react';
import { Portfolio } from '../types';
import { apiService } from '../services/api';

const CarteiraPage: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newStock, setNewStock] = useState({ codigo: '', quantidade: '', preco_medio: '', stop_loss: '', take_profit: '' });
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<null | Portfolio>(null);
  const [updating, setUpdating] = useState(false);

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

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStock.codigo.trim() || !newStock.quantidade || !newStock.preco_medio) return;
    try {
      setAdding(true);
      await apiService.addToPortfolio({
        codigo: newStock.codigo.trim().toUpperCase(),
        quantidade: Number(newStock.quantidade),
        preco_medio: Number(newStock.preco_medio),
        stop_loss: newStock.stop_loss ? Number(newStock.stop_loss) : 0,
        take_profit: newStock.take_profit ? Number(newStock.take_profit) : 0,
      });
      setShowAddModal(false);
      setNewStock({ codigo: '', quantidade: '', preco_medio: '', stop_loss: '', take_profit: '' });
      await loadPortfolio();
    } catch (err) {
      setError('Erro ao adicionar ativo na carteira');
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
                      <button className="btn btn-warning" onClick={() => handleEdit(item)}>Editar</button>
                      <button className="btn btn-danger" onClick={() => handleDelete(item.codigo)}>Remover</button>
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
    </div>
  );
};

export default CarteiraPage; 