import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import AnimatedButton from './AnimatedButton';
import LoadingSpinner from './LoadingSpinner';
import './WelcomeScreen.css';

const WelcomeScreen: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isLoading, setIsLoading] = useState(true);
  const [animationStep, setAnimationStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    // 模拟加载过程
    const loadingTimer = setTimeout(() => {
      setIsLoading(false);
    }, 1500);

    // 动画步骤
    const animationTimer = setInterval(() => {
      setAnimationStep(prev => (prev + 1) % 4);
    }, 3000);

    return () => {
      clearInterval(timer);
      clearTimeout(loadingTimer);
      clearInterval(animationTimer);
    };
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    });
  };

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 6) return '夜深了';
    if (hour < 12) return '早上好';
    if (hour < 18) return '下午好';
    return '晚上好';
  };

  const quickActions = [
    { 
      title: 'AI智能助手', 
      description: '与DeepSeek AI对话，获取智能帮助',
      icon: '🤖', 
      path: '/chat',
      color: 'primary'
    },
    { 
      title: '校园地图', 
      description: '查看校园各个区域和建筑位置',
      icon: '🗺️', 
      path: '/map',
      color: 'success'
    },
    { 
      title: '用户信息', 
      description: '管理个人资料和偏好设置',
      icon: '👤', 
      path: '/profile',
      color: 'secondary'
    },
    { 
      title: '食堂服务', 
      description: '查看食堂菜单和营养信息',
      icon: '🍽️', 
      path: '/dining',
      color: 'outline'
    }
  ];

  if (isLoading) {
    return (
      <div className="welcome-loading">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="welcome-screen">
      {/* 动态背景 */}
      <div className="welcome-bg">
        <div className="bg-shapes">
          <div className={`shape shape-1 ${animationStep === 0 ? 'active' : ''}`}></div>
          <div className={`shape shape-2 ${animationStep === 1 ? 'active' : ''}`}></div>
          <div className={`shape shape-3 ${animationStep === 2 ? 'active' : ''}`}></div>
          <div className={`shape shape-4 ${animationStep === 3 ? 'active' : ''}`}></div>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="welcome-content">
        {/* 问候区域 */}
        <div className="greeting-section">
          <div className="time-display">
            <div className="current-time">{formatTime(currentTime)}</div>
            <div className="current-date">{formatDate(currentTime)}</div>
          </div>
          <div className="greeting-text">
            <h1 className="greeting-title">
              {getGreeting()}！欢迎使用 <span className="brand-name">WePlus</span>
            </h1>
            <p className="greeting-subtitle">
              您的智能校园助手，让校园生活更便捷、更智能
            </p>
          </div>
        </div>

        {/* 快速操作区域 */}
        <div className="quick-actions">
          <h2 className="section-title">快速开始</h2>
          <div className="actions-grid">
            {quickActions.map((action, index) => (
              <Link 
                key={action.path} 
                to={action.path} 
                className="action-card"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="action-icon">{action.icon}</div>
                <div className="action-content">
                  <h3 className="action-title">{action.title}</h3>
                  <p className="action-description">{action.description}</p>
                </div>
                <div className="action-arrow">→</div>
              </Link>
            ))}
          </div>
        </div>

        {/* 功能亮点 */}
        <div className="features-section">
          <h2 className="section-title">功能亮点</h2>
          <div className="features-list">
            <div className="feature-item">
              <span className="feature-icon">🎯</span>
              <span className="feature-text">智能AI对话，24小时在线服务</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">📍</span>
              <span className="feature-text">精准校园导航，快速找到目的地</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🔔</span>
              <span className="feature-text">实时信息推送，不错过重要通知</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🌟</span>
              <span className="feature-text">个性化服务，专属您的校园体验</span>
            </div>
          </div>
        </div>

        {/* 开始使用按钮 */}
        <div className="start-section">
          <AnimatedButton 
            variant="primary" 
            size="large"
            icon="🚀"
            className="glow"
          >
            <Link to="/chat" style={{ color: 'inherit', textDecoration: 'none' }}>
              开始体验 AI 助手
            </Link>
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;