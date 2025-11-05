/**
 * 用户认证上下文
 * 提供全局用户状态管理和认证相关功能
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User, AuthContextType } from '../types/auth';
import { isAuthenticated, getUserInfo, logout as authLogout } from '../utils/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化用户状态
  useEffect(() => {
    const initializeAuth = () => {
      try {
        if (isAuthenticated()) {
          const userInfo = getUserInfo();
          if (userInfo) {
            setUser(userInfo);
          }
        }
      } catch (error) {
        console.error('初始化认证状态失败:', error);
        clearAuthTokens();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = (userData: User) => {
    setUser(userData);
  };

  const logout = () => {
    setUser(null);
    authLogout(); // 调用auth.ts中的logout函数，会清除用户数据和认证信息
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      // 更新localStorage中的用户信息
      localStorage.setItem('user_info', JSON.stringify(updatedUser));
    }
  };

  const value: AuthContextType = {
    user,
    isLoggedIn: !!user,
    isLoading,
    login,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;