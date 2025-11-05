/**
 * 用户认证上下文
 * 提供全局用户状态管理和认证相关功能
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User, AuthContextType } from '../types/auth';
import { isAuthenticated, getUserInfo, logout as authLogout, clearAuthTokens } from '../utils/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化用户状态
  /**
   * initializeAuth
   * 功能：在应用启动时从 localStorage 恢复用户登录状态与基本信息。
   * 过程：
   * - 检查是否已认证（存在 token 与 user_info）；
   * - 若存在则解析并设置到全局 user 状态；
   * - 异常时清理认证信息以避免脏数据；
   */
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

  /**
   * login
   * 功能：在登录成功后将后端返回的用户对象写入全局状态，供各页面使用。
   * 注意：网络请求与 token 写入由 Login 组件完成，此处只负责状态同步。
   */
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
