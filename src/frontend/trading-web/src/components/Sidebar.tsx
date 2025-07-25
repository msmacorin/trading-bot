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
        {(user && open) && (
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
              <span>📊</span>
              <span>Em Análise</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/carteira" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>💼</span>
              <span>Carteira</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/transacoes" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>💰</span>
              <span>Ordens Executadas</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/analise-individual" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>🔍</span>
              <span>Análise Individual</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/login" className={({ isActive }) => isActive ? 'active' : ''} onClick={handleLogout}>
              <span>🚪</span>
              <span>Sair</span>
            </NavLink>
          </li>
        </ul>
      </nav>
      
    </div>
  );
};

export default Sidebar; 