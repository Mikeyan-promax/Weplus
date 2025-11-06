import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './AdminLogin.css';

/**
 * 管理员登录页面组件
 * 负责处理管理员登录流程：
 * - 检查本地存储中的 admin_token，已登录则跳转管理后台
 * - 采集邮箱和密码并发起登录请求
 * - 登录成功后跳转至管理后台首页
 */
const AdminLogin: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 检查是否已经登录
  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (adminToken) {
      navigate('/admin');
    }
  }, [navigate]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 清除错误信息
    if (error) {
      setError('');
    }
  };

  /**
   * 管理员登录提交：相对路径 `/api/admin/auth/login`，避免硬编码端口影响部署
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.email || !formData.password) {
      setError('请填写所有必填字段');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 调用后端管理员登录API（相对路径，适配本地/云端端口）
      const response = await fetch('/api/admin/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // 保存管理员token和用户信息
        localStorage.setItem('admin_token', data.data.access_token);
        localStorage.setItem('admin_user_info', JSON.stringify(data.data.user));
        
        // 登录成功，跳转到管理后台
        navigate('/admin');
      } else {
        setError(data.message || '邮箱或密码错误，请重试');
      }
    } catch (err) {
      setError('登录失败，请检查网络连接或稍后重试');
      console.error('Admin login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToApp = () => {
    navigate('/');
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-background">
        <div className="background-pattern"></div>
      </div>
      
      <div className="admin-login-card">
        <div className="admin-login-header">
          <div className="admin-logo">
            <span className="logo-icon">🎓</span>
          </div>
          <h1>WePlus 管理后台</h1>
          <p className="admin-subtitle">系统管理员登录</p>
        </div>

        <form className="admin-login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">管理员邮箱</label>
            <div className="input-wrapper">
              <span className="input-icon">📧</span>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="请输入管理员邮箱"
                disabled={loading}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">密码</label>
            <div className="input-wrapper">
              <span className="input-icon">🔒</span>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="请输入密码"
                disabled={loading}
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            className={`login-button ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? (
              <>
                <div className="loading-spinner"></div>
                登录中...
              </>
            ) : (
              <>
                <span>🚀</span>
                登录管理后台
              </>
            )}
          </button>
        </form>

        <div className="admin-login-footer">
          <button className="back-button" onClick={handleBackToApp}>
            ← 返回应用首页
          </button>
          
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
