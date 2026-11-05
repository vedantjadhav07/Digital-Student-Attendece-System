import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => authService.getStoredUser());
  const [loading, setLoading] = useState(() => !authService.getStoredUser());

  const fetchCurrentUser = async () => {
    try {
      const data = await authService.getMe();
      if (data?.authenticated && data?.user) {
        setUser(data.user);
        localStorage.setItem('lab_user', JSON.stringify(data.user));
      } else {
        // Attempt token refresh if refresh token is available
        const refreshToken = localStorage.getItem('lab_refresh_token');
        if (refreshToken) {
          try {
            const refreshRes = await authService.refreshToken();
            if (refreshRes?.user) {
              setUser(refreshRes.user);
              return;
            }
          } catch {
            setUser(null);
          }
        } else {
          setUser(null);
        }
      }
    } catch {
      // If error occurs, check if refresh token works
      const refreshToken = localStorage.getItem('lab_refresh_token');
      if (refreshToken) {
        try {
          const refreshRes = await authService.refreshToken();
          if (refreshRes?.user) {
            setUser(refreshRes.user);
            return;
          }
        } catch {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const login = async (username, password, remember = false) => {
    const data = await authService.login(username, password, remember);
    if (data?.success && data?.user) {
      setUser(data.user);
      return data.user;
    }
    throw new Error(data?.message || 'Invalid credentials');
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        loading,
        isLoading: loading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser: fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

