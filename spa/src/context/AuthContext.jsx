import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  // Handle system-wide theme toggling
  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      return next;
    });
  };

  const checkAuth = async () => {
    try {
      const data = await authService.getMe();
      setUser(data);
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const data = await authService.login(email, password);
    await checkAuth();
    return data;
  };

  const adminLogin = async (email, password) => {
    const data = await authService.adminLogin(email, password);
    await checkAuth();
    return data;
  };

  const register = async (username, email, password, gender) => {
    const data = await authService.register(username, email, password, gender);
    await checkAuth();
    return data;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout request failed', err);
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, adminLogin, register, logout, checkAuth, theme, toggleTheme }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
