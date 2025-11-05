import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './AdminDashboard.css';

interface SystemStats {
  total_users: number;
  active_users: number;
  total_documents: number;
  total_chats: number;
  storage_used: number;
  api_calls_today: number;
}

interface SystemHealth {
  rag_system: 'healthy' | 'warning' | 'error';
  deepseek_api: 'healthy' | 'warning' | 'error';
  vector_database: 'healthy' | 'warning' | 'error';
  file_storage: 'healthy' | 'warning' | 'error';
}

interface Activity {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  user?: string;
}

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<SystemStats>({
    total_users: 0,
    active_users: 0,
    total_documents: 0,
    total_chats: 0,
    storage_used: 0,
    api_calls_today: 0
  });
  const [health, /* setHealth */] = useState<SystemHealth>({
    rag_system: 'healthy',
    deepseek_api: 'healthy',
    vector_database: 'healthy',
    file_storage: 'healthy'
  });
  const [activities, setActivities] = useState<Activity[]>([]);

  // 检查管理员登录状态
  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      navigate('/admin/login');
      return;
    }
    
    // 模拟数据加载
    setTimeout(() => {
      setStats({
        total_users: 1247,
        active_users: 89,
        total_documents: 342,
        total_chats: 5678,
        storage_used: 2.4,
        api_calls_today: 1234
      });
      
      setActivities([
        {
          id: '1',
          type: 'user_register',
          message: '新用户注册',
          timestamp: '2024-01-15 14:30:00',
          user: 'user123@example.com'
        },
        {
          id: '2',
          type: 'document_upload',
          message: '文档上传成功',
          timestamp: '2024-01-15 14:25:00',
          user: 'admin@weplus.com'
        },
        {
          id: '3',
          type: 'system_backup',
          message: '系统自动备份完成',
          timestamp: '2024-01-15 14:00:00'
        }
      ]);
      
      setLoading(false);
    }, 1000);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    navigate('/admin/login');
  };

  const handleBackToApp = () => {
    navigate('/');
  };

  const refreshData = () => {
    setLoading(true);
    // 模拟刷新数据
    setTimeout(() => {
      setLoading(false);
    }, 500);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#48bb78';
      case 'warning': return '#ed8936';
      case 'error': return '#f56565';
      default: return '#a0aec0';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return '正常';
      case 'warning': return '警告';
      case 'error': return '错误';
      default: return '未知';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'user_register': return '👤';
      case 'document_upload': return '📄';
      case 'system_backup': return '💾';
      case 'api_call': return '🔗';
      default: return '📝';
    }
  };

  const formatFileSize = (gb: number) => {
    if (gb < 1) {
      return `${(gb * 1024).toFixed(0)} MB`;
    }
    return `${gb.toFixed(1)} GB`;
  };

  if (loading) {
    return (
      <div className="admin-dashboard-loading">
        <div className="loading-spinner"></div>
        <p>加载管理后台数据...</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* 顶部导航栏 */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">🎓</span>
            <h1>WePlus 管理后台</h1>
          </div>
        </div>
        <div className="header-right">
          <div className="admin-info">
            <span className="admin-avatar">👨‍💼</span>
            <div className="admin-details">
              <span className="admin-name">系统管理员</span>
              <span className="admin-role">Super Admin</span>
            </div>
          </div>
          <button className="back-to-app-button" onClick={handleBackToApp}>
            <span>🏠</span>
            返回应用
          </button>
          <button className="logout-button" onClick={handleLogout}>
            <span>🚪</span>
            退出登录
          </button>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main className="dashboard-main">
        {/* 统计卡片 */}
        <section className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-icon">👥</span>
              <div className="stat-content">
                <h3>总用户数</h3>
                <p className="stat-number">{stats.total_users.toLocaleString()}</p>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">🟢</span>
              <div className="stat-content">
                <h3>活跃用户</h3>
                <p className="stat-number">{stats.active_users}</p>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">📄</span>
              <div className="stat-content">
                <h3>文档总数</h3>
                <p className="stat-number">{stats.total_documents}</p>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">💬</span>
              <div className="stat-content">
                <h3>对话总数</h3>
                <p className="stat-number">{stats.total_chats.toLocaleString()}</p>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">💾</span>
              <div className="stat-content">
                <h3>存储使用</h3>
                <p className="stat-number">{formatFileSize(stats.storage_used)}</p>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">🔗</span>
              <div className="stat-content">
                <h3>今日API调用</h3>
                <p className="stat-number">{stats.api_calls_today.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </section>

        {/* 仪表板内容 */}
        <div className="dashboard-content">
          <div className="content-grid">
            {/* 系统状态 */}
            <div className="dashboard-card">
              <div className="card-header">
                <h2>系统状态</h2>
                <button className="refresh-button" onClick={refreshData}>
                  🔄
                </button>
              </div>
              <div className="card-content">
                <div className="system-status">
                  <div className="status-item">
                    <span className="status-label">RAG系统</span>
                    <span 
                      className="status-value healthy"
                      style={{ color: getStatusColor(health.rag_system) }}
                    >
                      <span 
                        className="status-indicator" 
                        style={{ backgroundColor: getStatusColor(health.rag_system) }}
                      ></span>
                      {getStatusText(health.rag_system)}
                    </span>
                  </div>
                  <div className="status-item">
                    <span className="status-label">DeepSeek API</span>
                    <span 
                      className="status-value healthy"
                      style={{ color: getStatusColor(health.deepseek_api) }}
                    >
                      <span 
                        className="status-indicator" 
                        style={{ backgroundColor: getStatusColor(health.deepseek_api) }}
                      ></span>
                      {getStatusText(health.deepseek_api)}
                    </span>
                  </div>
                  <div className="status-item">
                    <span className="status-label">向量数据库</span>
                    <span 
                      className="status-value healthy"
                      style={{ color: getStatusColor(health.vector_database) }}
                    >
                      <span 
                        className="status-indicator" 
                        style={{ backgroundColor: getStatusColor(health.vector_database) }}
                      ></span>
                      {getStatusText(health.vector_database)}
                    </span>
                  </div>
                  <div className="status-item">
                    <span className="status-label">文件存储</span>
                    <span 
                      className="status-value healthy"
                      style={{ color: getStatusColor(health.file_storage) }}
                    >
                      <span 
                        className="status-indicator" 
                        style={{ backgroundColor: getStatusColor(health.file_storage) }}
                      ></span>
                      {getStatusText(health.file_storage)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 快捷操作 */}
            <div className="dashboard-card">
              <div className="card-header">
                <h2>快捷操作</h2>
              </div>
              <div className="card-content">
                <div className="quick-actions">
                  <Link to="/admin/users" className="action-button">
                    <span className="action-icon">👥</span>
                    用户管理
                  </Link>
                  <Link to="/admin/documents" className="action-button">
                    <span className="action-icon">📄</span>
                    文档管理
                  </Link>
                  <Link to="/admin/study-resources" className="action-button">
                    <span className="action-icon">📚</span>
                    学习资源管理
                  </Link>
                  <Link to="/admin/vector-database" className="action-button">
                    <span className="action-icon">🔗</span>
                    向量数据库
                  </Link>
                  <Link to="/admin/backup" className="action-button">
                    <span className="action-icon">💾</span>
                    数据备份
                  </Link>
                  <button className="action-button" onClick={refreshData}>
                    <span className="action-icon">🔄</span>
                    刷新数据
                  </button>
                </div>
              </div>
            </div>

            {/* 最近活动 */}
            <div className="dashboard-card recent-activities">
              <div className="card-header">
                <h2>最近活动</h2>
              </div>
              <div className="card-content">
                {activities.length > 0 ? (
                  <div className="activities-list">
                    {activities.map((activity) => (
                      <div key={activity.id} className="activity-item">
                        <span className="activity-icon">
                          {getActivityIcon(activity.type)}
                        </span>
                        <div className="activity-content">
                          <p className="activity-message">
                            {activity.message}
                            {activity.user && (
                              <span className="activity-user"> - {activity.user}</span>
                            )}
                          </p>
                          <span className="activity-time">{activity.timestamp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-activities">
                    <span className="no-data-icon">📝</span>
                    <p>暂无最近活动</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;