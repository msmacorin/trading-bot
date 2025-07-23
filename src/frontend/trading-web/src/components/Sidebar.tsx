import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  open: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ open }) => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className={`sidebar${open ? '' : ' sidebar-collapsed'}`}>
      <div className="sidebar-header">
        <h1>🤖 Trading Bot</h1>
        {user && (
          <div className="user-info">
            <div className="user-avatar">
              👤
            </div>
            <div className="user-details">
              <div className="user-name">{user.nome}</div>
              <div className="user-email">{user.email}</div>
            </div>
          </div>
        )}
      </div>
      
      <nav className="sidebar-nav">
        <ul>
          <li>
            <NavLink to="/analise" className={({ isActive }) => isActive ? 'active' : ''}>
              📊 Em Análise
            </NavLink>
          </li>
          <li>
            <NavLink to="/carteira" className={({ isActive }) => isActive ? 'active' : ''}>
              💼 Carteira
            </NavLink>
          </li>
          <li>
            <NavLink to="/transacoes" className={({ isActive }) => isActive ? 'active' : ''}>
              💰 Ordens Executadas
            </NavLink>
          </li>
          <li>
            <NavLink to="/analise-individual" className={({ isActive }) => isActive ? 'active' : ''}>
              🔍 Análise Individual
            </NavLink>
          </li>
        </ul>
      </nav>
      
      <div className="sidebar-footer">
        <button onClick={handleLogout} className="logout-button">
          🚪 Sair
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 