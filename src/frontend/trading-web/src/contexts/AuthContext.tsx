import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  email: string;
  nome: string;
  ativo: boolean;
  data_criacao: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, senha: string) => Promise<boolean>;
  register: (nome: string, email: string, senha: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Verifica se há token salvo no localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem('trading_token');
    const savedUser = localStorage.getItem('trading_user');
    
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Erro ao carregar dados de autenticação:', error);
        localStorage.removeItem('trading_token');
        localStorage.removeItem('trading_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, senha: string): Promise<boolean> => {
    try {
      console.log('🔐 Tentando fazer login...');
      
      // Detecta a URL da API baseada no ambiente
      let apiUrl = 'http://localhost:8000';
      if (window.location.hostname !== 'localhost') {
        apiUrl = `http://${window.location.hostname}:8000`;
      }
      
      const response = await fetch(`${apiUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, senha }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Login bem-sucedido:', data);
        setToken(data.access_token);
        setUser(data.usuario);
        
        // Salva no localStorage
        localStorage.setItem('trading_token', data.access_token);
        localStorage.setItem('trading_user', JSON.stringify(data.usuario));
        
        console.log('💾 Dados salvos no localStorage');
        return true;
      } else {
        const errorData = await response.json();
        console.error('❌ Erro no login:', errorData.detail);
        return false;
      }
    } catch (error) {
      console.error('❌ Erro ao fazer login:', error);
      return false;
    }
  };

  const register = async (nome: string, email: string, senha: string): Promise<boolean> => {
    try {
      // Detecta a URL da API baseada no ambiente
      let apiUrl = 'http://localhost:8000';
      if (window.location.hostname !== 'localhost') {
        apiUrl = `http://${window.location.hostname}:8000`;
      }
      
      const response = await fetch(`${apiUrl}/auth/registro`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ nome, email, senha }),
      });

      if (response.ok) {
        return true;
      } else {
        const errorData = await response.json();
        console.error('Erro no registro:', errorData.detail);
        return false;
      }
    } catch (error) {
      console.error('Erro ao fazer registro:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('trading_token');
    localStorage.removeItem('trading_user');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 