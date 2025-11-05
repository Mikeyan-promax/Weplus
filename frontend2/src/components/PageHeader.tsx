import React from 'react';
import { useLocation } from 'react-router-dom';
import Breadcrumb from './Breadcrumb';
import AnimatedButton from './AnimatedButton';
import { useAuth } from '../contexts/AuthContext';
import { setUserData, USER_DATA_TYPES } from '../utils/userDataManager';
import './PageHeader.css';

interface PageHeaderProps {
  title?: string;
  subtitle?: string;
  showBreadcrumb?: boolean;
  actions?: React.ReactNode;
  className?: string;
  onClearChat?: () => void;
}

/**
 * 页面顶栏组件
 * 功能：
 * - 根据当前路由自动匹配页面标题与副标题
 * - 针对特定页面（如聊天）提供专属操作按钮
 * - 兼容 /app/* 路由前缀，避免标题回退为“页面”
 */
const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  showBreadcrumb = true,
  actions,
  className = '',
  onClearChat
}) => {
  const location = useLocation();
  const { user } = useAuth();

  /**
   * 规范化路由路径
   * 逻辑：将 /app/* 前缀去除后用于匹配标题映射；保持根路径一致性
   */
  const normalizePath = (path: string): string => {
    if (path === '/app' || path === '/app/') return '/';
    if (path.startsWith('/app/')) return path.replace('/app', '');
    return path;
  };

  const normalizedPath = normalizePath(location.pathname);

  // 页面标题映射（按规范化后的路径）
  const pageTitles: Record<string, { title: string; subtitle?: string }> = {
    '/': { title: '欢迎使用 WePlus', subtitle: '您的校园智能助手' },
    '/chat': { title: 'AI智能助手', subtitle: '基于RAG技术，为您提供准确的校园信息服务' },
    '/profile': { title: '用户信息', subtitle: '管理您的个人资料和系统设置' },
    '/map': { title: '校园地图', subtitle: '探索校园，找到您需要的地点' },
    '/dining': { title: '食堂服务', subtitle: '查看菜单、营业时间和用餐信息' },
    '/study': { title: '学习资源', subtitle: '发现学习资料和学术资源' },
    '/life': { title: '生活服务', subtitle: '校园生活相关服务和信息' },
    '/other': { title: '其他功能', subtitle: '更多实用功能等您探索' },
    '/chat-test': { title: '聊天UI测试', subtitle: '组件与交互演示' },
    '/settings': { title: '设置', subtitle: '系统偏好与个性化配置' },
    '/test-isolation': { title: '数据隔离测试', subtitle: '验证用户数据隔离效果' },
    '/math-test': { title: '数学测试', subtitle: '渲染与计算能力演示' }
  };

  /**
   * 动态路由处理：资源详情、其他可能的 /xxx/:id
   */
  let dynamicTitle: { title: string; subtitle?: string } | undefined;
  if (normalizedPath.startsWith('/resource/')) {
    dynamicTitle = { title: '资源详情', subtitle: '学习资源详细信息' };
  }

  const currentPage = dynamicTitle || pageTitles[normalizedPath];
  const displayTitle = title || currentPage?.title || '页面';
  const displaySubtitle = subtitle || currentPage?.subtitle;

  // 处理清空对话
  const handleClearChat = () => {
    if (onClearChat) {
      onClearChat();
    } else {
      // 默认清空对话逻辑
      const defaultMessage = {
        id: '1',
        content: '您好！我是校园智能AI助手，可以帮助您解答关于校园生活、学习资源、校区导航等各种问题。请问有什么可以帮助您的吗？',
        sender: 'assistant' as const,
        timestamp: new Date()
      };
      
      if (user) {
        setUserData(USER_DATA_TYPES.CHAT_HISTORY, [defaultMessage]);
      }
      
      // 刷新页面以应用更改
      window.location.reload();
    }
  };

  // 检查是否是聊天页面（兼容 /app/chat）
  const isChatPage = normalizedPath === '/chat';

  return (
    <div className={`page-header ${className}`}>
      {/* 导航区域 */}
      <div className="page-header-nav">
        {showBreadcrumb && <Breadcrumb />}
      </div>

      {/* 标题区域 */}
      <div className="page-header-content">
        <div className="page-header-text">
          <h1 className="page-title">{displayTitle}</h1>
          {displaySubtitle && (
            <p className="page-subtitle">{displaySubtitle}</p>
          )}
        </div>
        
        {/* 操作按钮区域 */}
        <div className="page-header-actions">
          {/* 聊天页面专用按钮 */}
          {isChatPage && (
            <>
              <AnimatedButton
                onClick={handleClearChat}
                variant="secondary"
                size="small"
              >
                清空对话
              </AnimatedButton>
            </>
          )}
          {/* 其他自定义操作按钮 */}
          {actions}
        </div>
      </div>
    </div>
  );
};

export default PageHeader;
