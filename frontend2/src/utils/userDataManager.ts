/**
 * 用户数据管理工具
 * 实现用户数据隔离，确保每个用户的数据相互独立
 */

import { getUserInfo } from './auth';

// 用户数据存储键前缀
const USER_DATA_PREFIX = 'user_data_';

// 用户数据类型常量

/**
 * 获取当前用户的数据存储键
 */
const getUserDataKey = (dataType: string): string => {
  const user = getUserInfo();
  if (!user) {
    throw new Error('用户未登录');
  }
  return `${USER_DATA_PREFIX}${user.id}_${dataType}`;
};

/**
 * 存储用户特定数据
 */
export const setUserData = (dataType: string, data: any): void => {
  try {
    const key = getUserDataKey(dataType);
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error('存储用户数据失败:', error);
  }
};

/**
 * 获取用户特定数据
 */
export const getUserData = <T>(dataType: string, defaultValue: T | null = null): T | null => {
  try {
    const key = getUserDataKey(dataType);
    const data = localStorage.getItem(key);
    if (data) {
      return JSON.parse(data) as T;
    }
    return defaultValue;
  } catch (error) {
    console.error('获取用户数据失败:', error);
    return defaultValue;
  }
};

/**
 * 删除用户特定数据
 */
export const removeUserData = (dataType: string): void => {
  try {
    const key = getUserDataKey(dataType);
    localStorage.removeItem(key);
  } catch (error) {
    console.error('删除用户数据失败:', error);
  }
};

/**
 * 清除当前用户的所有数据
 */
export const clearUserData = (): void => {
  try {
    const user = getUserInfo();
    if (!user) return;

    const userPrefix = `${USER_DATA_PREFIX}${user.id}_`;
    const keysToRemove: string[] = [];

    // 查找所有属于当前用户的数据键
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(userPrefix)) {
        keysToRemove.push(key);
      }
    }

    // 删除所有找到的键
    keysToRemove.forEach(key => localStorage.removeItem(key));
  } catch (error) {
    console.error('清除用户数据失败:', error);
  }
};

/**
 * 获取用户数据统计信息
 */
export const getUserDataStats = (): { totalKeys: number; totalSize: number } => {
  try {
    const user = getUserInfo();
    if (!user) return { totalKeys: 0, totalSize: 0 };

    const userPrefix = `${USER_DATA_PREFIX}${user.id}_`;
    let totalKeys = 0;
    let totalSize = 0;

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(userPrefix)) {
        totalKeys++;
        const value = localStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }
    }

    return { totalKeys, totalSize };
  } catch (error) {
    console.error('获取用户数据统计失败:', error);
    return { totalKeys: 0, totalSize: 0 };
  }
};

// 预定义的数据类型常量
export const USER_DATA_TYPES = {
  CHAT_HISTORY: 'chat_history',
  USER_PREFERENCES: 'user_preferences',
  STUDY_PROGRESS: 'study_progress',
  CAMPUS_FAVORITES: 'campus_favorites',
  NOTIFICATION_SETTINGS: 'notification_settings',
  THEME_SETTINGS: 'theme_settings',
  SEARCH_HISTORY: 'search_history',
  BOOKMARKS: 'bookmarks',
  USER_PROFILE: 'user_profile',
} as const;

export type UserDataType = typeof USER_DATA_TYPES[keyof typeof USER_DATA_TYPES];