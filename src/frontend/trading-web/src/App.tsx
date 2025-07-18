import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { useTokenValidation } from './hooks/useTokenValidation';
import Sidebar from './components/Sidebar';
import TokenExpirationAlert from './components/TokenExpirationAlert';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AnalisePage from './pages/AnalisePage';
import CarteiraPage from './pages/CarteiraPage';
import TransacoesPage from './pages/TransacoesPage';
import AnaliseIndividualPage from './pages/AnaliseIndividualPage';
import './styles/global.css';

// Componente para rotas protegidas
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '1.2rem',
        color: '#666'
      }}>
        🔄 Carregando...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Componente principal da aplicação
const AppContent: React.FC = () => {
  const { user } = useAuth();
  
  // Hook para verificar validade do token periodicamente
  useTokenValidation();

  return (
    <div className="app">
      {user && <Sidebar />}
      <TokenExpirationAlert daysBeforeExpiration={7} />
      <Routes>
        {/* Rotas públicas */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Rotas protegidas */}
        <Route path="/" element={
          <ProtectedRoute>
            <Navigate to="/analise" replace />
          </ProtectedRoute>
        } />
        <Route path="/analise" element={
          <ProtectedRoute>
            <AnalisePage />
          </ProtectedRoute>
        } />
        <Route path="/carteira" element={
          <ProtectedRoute>
            <CarteiraPage />
          </ProtectedRoute>
        } />
        <Route path="/transacoes" element={
          <ProtectedRoute>
            <TransacoesPage />
          </ProtectedRoute>
        } />
        <Route path="/analise-individual" element={
          <ProtectedRoute>
            <AnaliseIndividualPage />
          </ProtectedRoute>
        } />
        
        {/* Redireciona para login se rota não encontrada */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
};

export default App; 