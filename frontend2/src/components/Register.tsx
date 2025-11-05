import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Register.css';

interface RegisterFormData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  verificationCode: string;
}

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<RegisterFormData>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    verificationCode: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [codeVerified, setCodeVerified] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 清除错误信息
    if (error) setError('');
  };

  const verifyCode = async () => {
    if (!formData.verificationCode) {
      setError('请输入验证码');
      return;
    }

    setLoading(true);
    setError('');

    /**
     * 验证邮箱验证码：相对路径 `/api/auth/verify-email`，避免硬编码端口
     */
    try {
      const response = await fetch('/api/auth/verify-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          code: formData.verificationCode
        }),
      });

      const data = await response.json();

      if (data.success) {
        setCodeVerified(true);
        setSuccess('验证码验证成功！现在可以完成注册。');
      } else {
        setError(data.message || '验证码验证失败');
      }
    } catch (error) {
      console.error('验证码验证错误:', error);
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const sendVerificationCode = async () => {
    if (!formData.email) {
      setError('请先输入邮箱地址');
      return;
    }

    setLoading(true);
    setError('');

    /**
     * 发送邮箱验证码：相对路径 `/api/auth/send-verification-code`，避免硬编码端口
     */
    try {
      const response = await fetch('/api/auth/send-verification-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          purpose: 'register'
        }),
      });

      const data = await response.json();

      if (data.success) {
        setCodeSent(true);
        setSuccess(data.message);
        // 开始倒计时
        setCountdown(60);
        const timer = setInterval(() => {
          setCountdown(prev => {
            if (prev <= 1) {
              clearInterval(timer);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      } else {
        setError(data.message || '发送验证码失败');
      }
    } catch (error) {
      console.error('发送验证码错误:', error);
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // 表单验证
    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致');
      setLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('密码长度至少6位');
      setLoading(false);
      return;
    }

    if (!codeVerified) {
      setError('请先验证邮箱验证码');
      setLoading(false);
      return;
    }

    /**
     * 提交注册：相对路径 `/api/auth/register`，避免硬编码端口造成云端不可用
     */
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          confirm_password: formData.confirmPassword,
          verification_code: formData.verificationCode
        }),
      });

      const data = await response.json();

      if (response.ok && data.access_token) {
        // 保存token到localStorage
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        setSuccess('注册成功！正在跳转到主页面...');
        setTimeout(() => {
          navigate('/app', { replace: true });
        }, 2000);
      } else {
        // 处理验证错误
        if (response.status === 422) {
          const errorDetail = data.detail;
          if (Array.isArray(errorDetail)) {
            // Pydantic验证错误
            const errorMessages = errorDetail.map((err: any) => err.msg).join(', ');
            setError(errorMessages);
          } else if (typeof errorDetail === 'string') {
            setError(errorDetail);
          } else {
            setError('注册信息验证失败，请检查输入');
          }
        } else {
          setError(data.detail || data.message || '注册失败');
        }
      }
    } catch (error) {
      console.error('注册错误:', error);
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <div className="register-header">
          <h1>WePlus 校园助手</h1>
          <p>创建您的账户</p>
        </div>

        <form onSubmit={handleSubmit} className="register-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">邮箱地址</label>
            <div className="email-input-group">
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="请输入您的邮箱"
                required
              />
              <button
                type="button"
                className="send-code-button"
                onClick={sendVerificationCode}
                disabled={loading || countdown > 0}
              >
                {countdown > 0 ? `${countdown}s` : '发送验证码'}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="verificationCode">验证码</label>
            <div className="verification-input-group">
              <input
                type="text"
                id="verificationCode"
                name="verificationCode"
                value={formData.verificationCode}
                onChange={handleInputChange}
                placeholder="请输入邮箱验证码"
                required
                disabled={codeVerified}
              />
              {codeSent && !codeVerified && (
                <button
                  type="button"
                  className="verify-code-button"
                  onClick={verifyCode}
                  disabled={loading || !formData.verificationCode}
                >
                  验证
                </button>
              )}
              {codeVerified && (
                <span className="verification-success">✓ 已验证</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="username">用户名</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="请输入用户名"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="请输入密码（至少6位）"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">确认密码</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              placeholder="请再次输入密码"
              required
            />
          </div>

          <button
            type="submit"
            className="register-button"
            disabled={loading}
          >
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <div className="register-footer">
          <p>
            已有账户？
            <Link to="/login" className="login-link">
              立即登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
