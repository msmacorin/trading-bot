import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/LoginPage.css';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const { login, user } = useAuth();
  const navigate = useNavigate();

  // Se o usuário já estiver logado, redireciona para a página principal
  useEffect(() => {
    if (user) {
      navigate('/analise', { replace: true });
    }
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const success = await login(email, senha);
      if (success) {
        navigate('/analise', { replace: true });
      } else {
        setError('Email ou senha incorretos');
      }
    } catch (err) {
      setError('Erro ao fazer login. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  // Se o usuário já estiver logado, não renderiza nada
  if (user) {
    return null;
  }

  return (
    <div className="login-container">
      <div className="login-wrapper">
        {/* Seção lateral esquerda com informações do sistema */}
        <div className="login-info-section">
          <div className="info-content">
            <h2>🤖 Trading Bot</h2>
            <h3>Sistema Inteligente de Análise de Ações</h3>
            
            <div className="features-list">
              <div className="feature-item">
                <span className="feature-icon">📊</span>
                <div className="feature-text">
                  <strong>Análise Técnica Automatizada</strong>
                  <p>Indicadores como RSI, Médias Móveis e Bollinger Bands para identificar oportunidades</p>
                </div>
              </div>

              <div className="feature-item">
                <span className="feature-icon">💼</span>
                <div className="feature-text">
                  <strong>Gestão de Carteira</strong>
                  <p>Acompanhe suas posições, registre vendas e controle stop loss e take profit</p>
                </div>
              </div>

              <div className="feature-item">
                <span className="feature-icon">📈</span>
                <div className="feature-text">
                  <strong>Suporte a Ações Fracionárias</strong>
                  <p>Negocie frações de ações com códigos como PETR4F, VALE3F, ITUB4F</p>
                </div>
              </div>

              <div className="feature-item">
                <span className="feature-icon">💰</span>
                <div className="feature-text">
                  <strong>Histórico de Transações</strong>
                  <p>Visualize todas suas operações e acompanhe a performance de seus investimentos</p>
                </div>
              </div>

              <div className="feature-item">
                <span className="feature-icon">🎯</span>
                <div className="feature-text">
                  <strong>Estratégias Inteligentes</strong>
                  <p>Algoritmos que analisam padrões e sugerem pontos de entrada e saída</p>
                </div>
              </div>
            </div>

            <div className="info-footer">
              <p><strong>Transforme dados em decisões inteligentes</strong></p>
              <p>Maximize seus lucros com análises precisas e automação inteligente</p>
            </div>
          </div>
        </div>

        {/* Seção direita com formulário de login */}
        <div className="login-form-section">
          <div className="login-card">
            <div className="login-header">
              <h1>Entrar na Conta</h1>
              <p>Acesse sua plataforma de trading</p>
            </div>

            <form onSubmit={handleSubmit} className="login-form">
              {error && (
                <div className="error-message">
                  ❌ {error}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="senha">Senha</label>
                <div className="password-input">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="senha"
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    placeholder="Sua senha"
                    required
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isLoading}
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="login-button"
                disabled={isLoading || !email || !senha}
              >
                {isLoading ? '🔄 Entrando...' : '🚀 Entrar'}
              </button>
            </form>

            <div className="login-footer">
              <p>
                Não tem uma conta?{' '}
                <Link to="/register" className="register-link">
                  Cadastre-se aqui
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 