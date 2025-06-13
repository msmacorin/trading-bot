import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar: React.FC = () => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>Trading Bot</h1>
      </div>
      <nav>
        <ul className="sidebar-nav">
          <li>
            <NavLink 
              to="/analise" 
              className={({ isActive }) => isActive ? 'active' : ''}
            >
              Em Análise
            </NavLink>
          </li>
          <li>
            <NavLink 
              to="/carteira" 
              className={({ isActive }) => isActive ? 'active' : ''}
            >
              Carteira
            </NavLink>
          </li>
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar; 