/**
 * 认证工具函数
 * 处理用户登录状态、token管理等
 */

import type { User, AuthTokens } from '../types/auth';
import { clearUserData } from './userDataManager';

// 存储键名
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

/**
 * 检查用户是否已登录
 */
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  const userInfo = localStorage.getItem(USER_INFO_KEY);
  return !!(token && userInfo);
};

/**
 * 获取访问令牌
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

/**
 * 获取刷新令牌
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * 获取用户信息
 */
export const getUserInfo = (): User | null => {
  const userInfo = localStorage.getItem(USER_INFO_KEY);
  if (userInfo) {
    try {
      return JSON.parse(userInfo);
    } catch (error) {
      console.error('解析用户信息失败:', error);
      return null;
    }
  }
  return null;
};

/**
 * 保存认证信息
 */
export const saveAuthTokens = (authData: AuthTokens): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, authData.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, authData.refresh_token);
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(authData.user));
};

/**
 * 清除认证信息
 */
export const clearAuthTokens = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_INFO_KEY);
};

/**
 * 用户注销
 */
export const logout = (): void => {
  // 清除用户特定数据
  clearUserData();
  
  // 清除认证信息
  clearAuthTokens();
  
  // 重定向到HelloPage（现在是根路径）
  window.location.href = '/';
};

/**
 * 获取带认证头的请求配置
 */
export const getAuthHeaders = (): Record<string, string> => {
  const token = getAccessToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }
  return {
    'Content-Type': 'application/json',
  };
};