/**
 * 用户认证上下文
 * 提供全局用户状态管理和认证相关功能
 */

import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User, AuthContextType, LoginCredentials } from '../types/auth';
import { isAuthenticated, getUserInfo, logout as authLogout, clearAuthTokens, saveAuthTokens } from '../utils/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider 组件：
 * - 初始化用户登录状态（从 localStorage 读取）
 * - 暴露 login/logout/updateUser 等方法给全局使用
 */
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化用户状态
  useEffect(() => {
    /**
     * 初始化认证状态：
     * - 如已认证，则读取并设置用户信息
     * - 异常时清理本地令牌，避免脏数据
     */
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
   * 登录函数：
   * - 参数：LoginCredentials（email、password）
   * - 行为：调用后端登录接口，保存令牌与用户信息到 localStorage，并更新上下文 user
   * - 返回：Promise<boolean> 表示登录是否成功
   */
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!res.ok) {
        return false;
      }

      const data = await res.json();
      // 兼容两种返回结构：{ data: { access_token, refresh_token, user, ... } } 或直接扁平结构
      const payload = data?.data ?? data;

      if (payload?.access_token && payload?.refresh_token && payload?.user) {
        // 保存令牌与用户信息
        saveAuthTokens({
          access_token: payload.access_token,
          refresh_token: payload.refresh_token,
          token_type: payload.token_type ?? 'Bearer',
          expires_in: payload.expires_in ?? 3600,
          user: payload.user as User,
        });
        // 更新上下文用户
        setUser(payload.user as User);
        return true;
      }

      return false;
    } catch (error) {
      console.error('登录失败:', error);
      return false;
    }
  };

  /**
   * 注销函数：
   * - 清空上下文 user
   * - 调用工具函数以清理令牌与用户本地数据，并重定向到首页
   */
  const logout = () => {
    setUser(null);
    authLogout(); // 调用auth.ts中的logout函数，会清除用户数据和认证信息
  };

  /**
   * 更新用户信息：
   * - 合并局部更新到当前 user
   * - 同步写入 localStorage（键：user_info）
   */
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
