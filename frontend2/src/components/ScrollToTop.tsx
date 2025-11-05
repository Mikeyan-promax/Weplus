import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollToTop 组件
 * 功能：
 * - 监听路由变化，在页面加载或切换路由后自动将窗口滚动到顶部
 * - 兼容不同浏览器的滚动上下文（window、documentElement、body）
 * 使用方式：放置在 <Router> 内部且高于 <Routes>，全局生效
 */
const ScrollToTop: React.FC = () => {
  const location = useLocation();

  useEffect(() => {
    // 立即滚动到顶部（避免保留上一页滚动位置）
    try {
      window.scrollTo({ top: 0, behavior: 'auto' });
      // 兜底处理，确保各滚动上下文都归零
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    } catch (e) {
      // 忽略潜在异常（如在非浏览器环境）
    }

    // 某些移动端渲染时机较晚，使用微任务再次归零以确保有效
    setTimeout(() => {
      try {
        window.scrollTo({ top: 0, behavior: 'auto' });
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      } catch (e) {}
    }, 0);
  }, [location.pathname, location.search, location.hash]);

  return null;
};

export default ScrollToTop;

