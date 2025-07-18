import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface TokenExpirationAlertProps {
  showAlert?: boolean;
  daysBeforeExpiration?: number;
}

const TokenExpirationAlert: React.FC<TokenExpirationAlertProps> = ({ 
  showAlert = true, 
  daysBeforeExpiration = 7 
}) => {
  const { token, user } = useAuth();
  const [showWarning, setShowWarning] = useState(false);
  const [daysRemaining, setDaysRemaining] = useState<number | null>(null);

  useEffect(() => {
    if (!token || !user || !showAlert) return;

    const checkTokenExpiration = () => {
      try {
        // Decodifica o token JWT para obter a data de expiração
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) return;

        const payload = JSON.parse(atob(tokenParts[1]));
        const expiration = payload.exp;
        
        if (!expiration) return;

        const expirationDate = new Date(expiration * 1000);
        const now = new Date();
        const timeUntilExpiration = expirationDate.getTime() - now.getTime();
        const daysUntilExpiration = Math.ceil(timeUntilExpiration / (1000 * 60 * 60 * 24));

        setDaysRemaining(daysUntilExpiration);

        // Mostra aviso se faltam menos dias que o limite configurado
        if (daysUntilExpiration <= daysBeforeExpiration && daysUntilExpiration > 0) {
          setShowWarning(true);
        } else {
          setShowWarning(false);
        }
      } catch (error) {
        console.error('❌ Erro ao verificar expiração do token:', error);
      }
    };

    // Verifica imediatamente
    checkTokenExpiration();

    // Verifica a cada hora
    const interval = setInterval(checkTokenExpiration, 60 * 60 * 1000);

    return () => clearInterval(interval);
  }, [token, user, showAlert, daysBeforeExpiration]);

  if (!showWarning || !daysRemaining) return null;

  const getAlertClass = () => {
    if (daysRemaining <= 1) return 'token-alert token-alert-danger';
    if (daysRemaining <= 3) return 'token-alert token-alert-warning';
    return 'token-alert token-alert-info';
  };

  const getAlertIcon = () => {
    if (daysRemaining <= 1) return '🚨';
    if (daysRemaining <= 3) return '⚠️';
    return '💡';
  };

  const getAlertMessage = () => {
    if (daysRemaining <= 1) {
      return `Sua sessão expira em ${daysRemaining} dia! Faça login novamente em breve.`;
    }
    return `Sua sessão expira em ${daysRemaining} dias. Considere fazer login novamente.`;
  };

  return (
    <div className={getAlertClass()}>
      <div className="token-alert-content">
        <span className="token-alert-icon">{getAlertIcon()}</span>
        <span className="token-alert-message">{getAlertMessage()}</span>
        <button 
          className="token-alert-close" 
          onClick={() => setShowWarning(false)}
          title="Dispensar aviso"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default TokenExpirationAlert; 