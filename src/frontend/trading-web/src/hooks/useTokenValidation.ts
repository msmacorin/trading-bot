import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Hook para verificar periodicamente a validade do token JWT
 * Verifica a cada 5 minutos se o token ainda é válido
 */
export const useTokenValidation = () => {
  const { checkTokenValidity, user, logout } = useAuth();

  useEffect(() => {
    // Só verifica se o usuário está logado
    if (!user) return;

    // Função para verificar o token
    const validateToken = async () => {
      try {
        const isValid = await checkTokenValidity();
        if (!isValid) {
          console.warn('🔐 Token expirou, fazendo logout...');
          logout();
        }
      } catch (error) {
        console.error('❌ Erro ao verificar token:', error);
        logout();
      }
    };

    // Verifica imediatamente
    validateToken();

    // Configura verificação periódica a cada 5 minutos
    const interval = setInterval(validateToken, 5 * 60 * 1000);

    // Cleanup
    return () => clearInterval(interval);
  }, [user, checkTokenValidity, logout]);

  // Também verifica quando a página fica visível novamente (usuário volta da aba)
  useEffect(() => {
    if (!user) return;

    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible') {
        try {
          const isValid = await checkTokenValidity();
          if (!isValid) {
            console.warn('🔐 Token expirou durante inatividade, fazendo logout...');
            logout();
          }
        } catch (error) {
          console.error('❌ Erro ao verificar token na volta da aba:', error);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [user, checkTokenValidity, logout]);
}; 