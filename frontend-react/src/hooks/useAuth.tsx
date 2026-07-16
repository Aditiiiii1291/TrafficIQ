import React, { createContext, useContext, useState, useEffect } from 'react';
import { ApiService } from '../services/apiService';
import type { UserResponse, UserLogin, UserCreate, UserUpdate, UserPasswordChange } from '../types';

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  login: (credentials: UserLogin) => Promise<void>;
  register: (user: UserCreate) => Promise<void>;
  logout: () => void;
  updateProfile: (profile: UserUpdate) => Promise<void>;
  changePassword: (pwd: UserPasswordChange) => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      
      if (token && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          // Refresh user profile in background
          const freshUser = await ApiService.getMe();
          setUser(freshUser);
          localStorage.setItem('user', JSON.stringify(freshUser));
        } catch (error) {
          console.error("Session initialize failed: ", error);
          // Token expired or invalid
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
        }
      }
      setLoading(false);
    };
    
    initializeAuth();
  }, []);

  const login = async (credentials: UserLogin) => {
    const response = await ApiService.login(credentials);
    localStorage.setItem('token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    setUser(response.user);
  };

  const register = async (userIn: UserCreate) => {
    await ApiService.register(userIn);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    ApiService.logout().catch(() => {});
  };

  const updateProfile = async (profileData: UserUpdate) => {
    const updated = await ApiService.updateProfile(profileData);
    localStorage.setItem('user', JSON.stringify(updated));
    setUser(updated);
  };

  const changePassword = async (pwdData: UserPasswordChange) => {
    await ApiService.changePassword(pwdData);
  };

  const deleteAccount = async () => {
    await ApiService.deleteAccount();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateProfile, changePassword, deleteAccount }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
