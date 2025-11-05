import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

/**
 * 侧边栏组件
 * 功能：渲染应用左侧导航菜单并处理移动端展开/收起逻辑
 * 说明：根据需求，已临时注释掉“食堂服务”和“生活服务”两个菜单项，便于日后随时恢复。
 */

const Sidebar: React.FC = () => {
  const location = useLocation();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const menuItems = [
    { path: '/app/', icon: '🏠', text: '首页' },
    { path: '/app/chat', icon: '🤖', text: 'AI助手' },
    { path: '/app/profile', icon: '👤', text: '用户信息' },
    // 校园地图功能已被注释掉
    // { path: '/app/map', icon: '🗺️', text: '校园地图' },
    // 按需隐藏：食堂服务
    // { path: '/app/dining', icon: '🍽️', text: '食堂服务' },
    { path: '/app/study', icon: '📚', text: '学习资源' },
    // 按需隐藏：生活服务
    // { path: '/app/life', icon: '🏠', text: '生活服务' },
    { path: '/app/other', icon: '⚙️', text: '其他功能' },
  ];

  const toggleMobileMenu = () => {
    setIsMobileOpen(!isMobileOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileOpen(false);
  };

  return (
    <>
      {/* 移动端菜单按钮 */}
      <button className="mobile-menu-btn" onClick={toggleMobileMenu}>
        {isMobileOpen ? '✕' : '☰'}
      </button>

      {/* 移动端遮罩层 */}
      <div 
        className={`sidebar-overlay ${isMobileOpen ? 'active' : ''}`}
        onClick={closeMobileMenu}
      />

      {/* 侧边栏 */}
      <div className={`sidebar ${isMobileOpen ? 'open' : ''}`}>
        {/* 侧边栏头部 */}
        <div className="sidebar-header">
          <h1>WePlus</h1>
          <p>校园智能助手</p>
        </div>

        {/* 导航菜单 */}
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <div key={item.path} className="nav-item">
              <Link
                to={item.path}
                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                onClick={closeMobileMenu}
              >
                <span className="icon">{item.icon}</span>
                <span className="text">{item.text}</span>
              </Link>
            </div>
          ))}
        </nav>

        {/* 侧边栏底部 */}
        <div className="sidebar-footer">
          <div className="footer-info">
            <p>© 2025 WePlus研发团队版权所有 | 让校园生活更智能</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
