import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import AnalisePage from './pages/AnalisePage';
import CarteiraPage from './pages/CarteiraPage';
import AnaliseIndividualPage from './pages/AnaliseIndividualPage';
import './styles/global.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <Routes>
          <Route path="/" element={<Navigate to="/analise" replace />} />
          <Route path="/analise" element={<AnalisePage />} />
          <Route path="/carteira" element={<CarteiraPage />} />
          <Route path="/analise-individual" element={<AnaliseIndividualPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App; 