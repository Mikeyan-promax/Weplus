import React from 'react';
import { Link } from 'react-router-dom';
import './HelloPage.css';

const HelloPage: React.FC = () => {
  return (
    <div className="hello-page">
      {/* 导航栏 */}
      <nav className="hello-nav">
        <div className="nav-brand">
          <h2>WePlus 校园助手</h2>
        </div>
        <div className="nav-buttons">
          <Link to="/login" className="nav-btn login-btn">
            登录
          </Link>
          <Link to="/register" className="nav-btn register-btn">
            注册
          </Link>
        </div>
      </nav>

      {/* 主要内容区域 */}
      <main className="hello-main">
        {/* 英雄区域 */}
        <section className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">
              欢迎使用 <span className="brand-highlight">WePlus</span> 校园助手
            </h1>
            <p className="hero-subtitle">
              智能化校园生活服务平台，让您的校园生活更加便捷高效
            </p>
            <div className="hero-buttons">
              <Link to="/register" className="cta-button primary">
                立即开始
              </Link>
              <Link to="/login" className="cta-button secondary">
                已有账户？登录
              </Link>
            </div>
          </div>
          <div className="hero-visual">
            <div className="floating-card">
              <div className="card-icon">🎓</div>
              <div className="card-text">智能校园</div>
            </div>
            <div className="floating-card delay-1">
              <div className="card-icon">💬</div>
              <div className="card-text">AI助手</div>
            </div>
            <div className="floating-card delay-2">
              <div className="card-icon">📚</div>
              <div className="card-text">学习资源</div>
            </div>
          </div>
        </section>

        {/* 功能特色区域 */}
        <section className="features-section">
          <div className="container">
            <h2 className="section-title">核心功能</h2>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🤖</div>
                <h3>智能RAG问答</h3>
                <p>基于先进的RAG技术，提供精准的校园信息查询和智能问答服务</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🗺️</div>
                <h3>校园地图导航</h3>
                <p>详细的校园地图，快速定位教学楼、食堂、图书馆等重要场所</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">📖</div>
                <h3>学习资源管理</h3>
                <p>整合课程资料、学习笔记，打造个人专属的知识管理系统</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🍽️</div>
                <h3>生活服务</h3>
                <p>食堂菜单、宿舍管理、校园活动等全方位的校园生活服务</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">📊</div>
                <h3>个人中心</h3>
                <p>个性化设置、学习统计、使用记录等个人信息管理</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🔒</div>
                <h3>安全可靠</h3>
                <p>采用先进的安全技术，保护用户隐私和数据安全</p>
              </div>
            </div>
          </div>
        </section>

        {/* 技术亮点区域 */}
        <section className="tech-section">
          <div className="container">
            <h2 className="section-title">技术亮点</h2>
            <div className="tech-grid">
              <div className="tech-item">
                <div className="tech-icon">⚡</div>
                <h4>高性能架构</h4>
                <p>基于React + FastAPI的现代化技术栈，响应速度快</p>
              </div>
              <div className="tech-item">
                <div className="tech-icon">🧠</div>
                <h4>AI智能引擎</h4>
                <p>集成DeepSeek和豆包嵌入模型，提供智能化服务</p>
              </div>
              <div className="tech-item">
                <div className="tech-icon">🔄</div>
                <h4>实时更新</h4>
                <p>支持热重载和实时数据同步，保持信息最新</p>
              </div>
              <div className="tech-item">
                <div className="tech-icon">📱</div>
                <h4>响应式设计</h4>
                <p>完美适配各种设备，随时随地使用</p>
              </div>
            </div>
          </div>
        </section>

        {/* 行动号召区域 */}
        <section className="cta-section">
          <div className="container">
            <div className="cta-content">
              <h2>开始您的智能校园生活</h2>
              <p>加入WePlus，体验前所未有的校园服务</p>
              <div className="cta-buttons">
                <Link to="/register" className="cta-button primary large">
                  免费注册
                </Link>
                <Link to="/login" className="cta-button secondary large">
                  立即登录
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* 页脚 */}
      <footer className="hello-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <h3>WePlus 校园助手</h3>
              <p>让校园生活更智能</p>
            </div>
            <div className="footer-links">
              <div className="link-group">
                <h4>产品</h4>
                <a href="#features">功能特色</a>
                <a href="#tech">技术亮点</a>
              </div>
              <div className="link-group">
                <h4>支持</h4>
                <a href="#help">帮助中心</a>
                <a href="#contact">联系我们</a>
              </div>
              <div className="link-group">
                <h4>系统</h4>
                <Link to="/admin/login" className="admin-link">管理员入口</Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2025 WePlus研发团队版权所有 | 让校园生活更智能</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HelloPage;