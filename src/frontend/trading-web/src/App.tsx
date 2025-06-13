import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import AnalisePage from './pages/AnalisePage';
import './styles/global.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <Routes>
          <Route path="/" element={<Navigate to="/analise" replace />} />
          <Route path="/analise" element={<AnalisePage />} />
          <Route path="/carteira" element={<div className="main-content"><h1>Carteira</h1><p>Em desenvolvimento...</p></div>} />
        </Routes>
      </div>
    </Router>
  );
};

export default App; 