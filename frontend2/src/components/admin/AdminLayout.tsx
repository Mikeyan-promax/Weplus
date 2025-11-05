import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './AdminLayout.css';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const menuItems = [
    { path: '/admin/dashboard', icon: '📊', text: '仪表板', description: '系统概览' },
    { path: '/admin/users', icon: '👥', text: '用户管理', description: '用户信息管理' },
    { path: '/admin/files', icon: '📁', text: '文件管理', description: '文件上传管理' },
    { path: '/admin/knowledge', icon: '🧠', text: '知识库', description: 'RAG数据管理' },
    { path: '/admin/logs', icon: '📋', text: '日志管理', description: '系统日志查看' },
    { path: '/admin/settings', icon: '⚙️', text: '系统设置', description: '配置管理' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    navigate('/admin/login');
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <div className="admin-layout">
      {/* 移动端顶部导航栏 */}
      <div className="admin-mobile-header">
        <button className="mobile-menu-toggle" onClick={toggleMobileMenu}>
          <span className="hamburger"></span>
        </button>
        <h1 className="admin-title">WePlus 管理后台</h1>
        <button className="mobile-logout" onClick={handleLogout}>
          退出
        </button>
      </div>

      {/* 侧边栏 */}
      <aside className={`admin-sidebar ${isSidebarCollapsed ? 'collapsed' : ''} ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
        {/* 侧边栏头部 */}
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">🎓</span>
            {!isSidebarCollapsed && <span className="logo-text">WePlus Admin</span>}
          </div>
          <button className="sidebar-toggle" onClick={toggleSidebar}>
            <span className={`toggle-icon ${isSidebarCollapsed ? 'collapsed' : ''}`}>
              ←
            </span>
          </button>
        </div>

        {/* 导航菜单 */}
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              {!isSidebarCollapsed && (
                <div className="nav-content">
                  <span className="nav-text">{item.text}</span>
                  <span className="nav-description">{item.description}</span>
                </div>
              )}
            </Link>
          ))}
        </nav>

        {/* 侧边栏底部 */}
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <span className="logout-icon">🚪</span>
            {!isSidebarCollapsed && <span className="logout-text">退出登录</span>}
          </button>
        </div>
      </aside>

      {/* 移动端遮罩层 */}
      <div 
        className={`mobile-overlay ${isMobileMenuOpen ? 'active' : ''}`}
        onClick={() => setIsMobileMenuOpen(false)}
      />

      {/* 主内容区域 */}
      <main className={`admin-main ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="admin-content">
          {children}
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;