import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface Transacao {
  id: number;
  codigo: string;
  data_transacao: string;
  quantidade_vendida: number;
  preco_compra: number;
  preco_venda: number;
  stop_loss_original: number;
  take_profit_original: number;
  valor_total: number;
  lucro_prejuizo: number;
  percentual_resultado: number;
  usuario_id: number;
}

interface ResumoTransacoes {
  total_transacoes: number;
  valor_total_vendido: number;
  lucro_prejuizo_total: number;
  percentual_medio: number;
  transacoes: Transacao[];
}

const TransacoesPage: React.FC = () => {
  const [dados, setDados] = useState<ResumoTransacoes | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTransacoes();
  }, []);

  const loadTransacoes = async () => {
    try {
      setLoading(true);
      const data = await apiService.getTransactions();
      setDados(data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar transações');
      console.error('Erro ao carregar transações:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getResultClass = (valor: number) => {
    if (valor > 0) return 'text-green-600';
    if (valor < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return <div className="main-content"><div className="loading">Carregando transações...</div></div>;
  }

  return (
    <div className="main-content">
      <div className="page-header">
        <h1 className="page-title">Ordens Executadas</h1>
      </div>

      {error && <div className="error">{error}</div>}

      {dados && (
        <>
          {/* Resumo Geral */}
          <div className="summary-cards">
            <div className="summary-card">
              <h3>Total de Transações</h3>
              <p className="summary-value">{dados.total_transacoes}</p>
            </div>
            
            <div className="summary-card">
              <h3>Valor Total Vendido</h3>
              <p className="summary-value">{formatCurrency(dados.valor_total_vendido)}</p>
            </div>
            
            <div className="summary-card">
              <h3>Lucro/Prejuízo Total</h3>
              <p className={`summary-value ${getResultClass(dados.lucro_prejuizo_total)}`}>
                {formatCurrency(dados.lucro_prejuizo_total)}
              </p>
            </div>
            
            <div className="summary-card">
              <h3>Percentual Médio</h3>
              <p className={`summary-value ${getResultClass(dados.percentual_medio)}`}>
                {formatPercent(dados.percentual_medio)}
              </p>
            </div>
          </div>

          {/* Lista de Transações */}
          <div className="table-container">
            {dados.transacoes.length === 0 ? (
              <div className="empty-state">
                <h3>Nenhuma transação encontrada</h3>
                <p>Suas vendas aparecerão aqui</p>
              </div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Data</th>
                    <th>Qtd Vendida</th>
                    <th>Preço Compra</th>
                    <th>Preço Venda</th>
                    <th>Valor Total</th>
                    <th>Stop Loss</th>
                    <th>Take Profit</th>
                    <th>Resultado (R$)</th>
                    <th>Resultado (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.transacoes.map((transacao) => (
                    <tr key={transacao.id}>
                      <td>
                        <span className="stock-code">{transacao.codigo}</span>
                      </td>
                      <td>{formatDate(transacao.data_transacao)}</td>
                      <td>{transacao.quantidade_vendida}</td>
                      <td>{formatCurrency(transacao.preco_compra)}</td>
                      <td>{formatCurrency(transacao.preco_venda)}</td>
                      <td>{formatCurrency(transacao.valor_total)}</td>
                      <td>{formatCurrency(transacao.stop_loss_original)}</td>
                      <td>{formatCurrency(transacao.take_profit_original)}</td>
                      <td className={getResultClass(transacao.lucro_prejuizo)}>
                        {formatCurrency(transacao.lucro_prejuizo)}
                      </td>
                      <td className={getResultClass(transacao.percentual_resultado)}>
                        {formatPercent(transacao.percentual_resultado)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default TransacoesPage; 