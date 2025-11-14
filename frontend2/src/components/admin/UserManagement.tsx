import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './UserManagement.css';

// 用户数据接口
interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  login_count: number;
  profile: Record<string, unknown> | null;
  // 保留旧字段以兼容现有代码
  status?: string;
  password_created_at?: string;
  password_strength?: string;
  password_hash?: string;
}

// API响应接口
interface ApiResponse {
  success: boolean;
  data: {
    users: User[];
    total: number;
    page: number;
    limit: number;
  };
  message: string;
}

// 用户统计接口
interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  new_users_today: number;
}

const UserManagement: React.FC = () => {
  const navigate = useNavigate();
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [, setStats] = useState<UserStats | null>(null); // 统计数据（当前未直接用于渲染）
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [verificationFilter, setVerificationFilter] = useState('');
  const [registrationDateFrom, setRegistrationDateFrom] = useState('');
  const [registrationDateTo, setRegistrationDateTo] = useState('');
  const [loginCountMin, setLoginCountMin] = useState('');
  const [loginCountMax, setLoginCountMax] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // 批量选择相关状态
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [showBatchActions, setShowBatchActions] = useState(false);
  
  // 重置密码相关状态
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [resetPasswordUserId, setResetPasswordUserId] = useState<number | null>(null);
  const [resetPasswordUsername, setResetPasswordUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetPasswordLoading, setResetPasswordLoading] = useState(false);
  
  // 删除用户相关状态
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteUserId, setDeleteUserId] = useState<number | null>(null);
  const [deleteUsername, setDeleteUsername] = useState('');
  const [deleteUserEmail, setDeleteUserEmail] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [, setTotalUsers] = useState(0); // 总用户数当前未直接用于渲染，仅用于计算分页
  const itemsPerPage = 10;

  // 返回管理系统主页
  const handleBackToAdmin = () => {
    navigate('/admin');
  };

  // 计算注册天数
  const calculateDaysSinceRegistration = (createdAt: string) => {
    if (!createdAt) return 0;
    const now = new Date();
    const created = new Date(createdAt);
    const diffTime = Math.abs(now.getTime() - created.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  // 格式化登录次数显示
  const formatLoginCount = (count: number) => {
    if (!count || count === 0) return '未登录';
    return `${count} 次`;
  };

  // 格式化验证状态
  const formatVerificationStatus = (isVerified: boolean) => {
    return isVerified ? '已验证' : '未验证';
  };

  // 批量选择处理函数
  const handleSelectUser = (userId: number) => {
    setSelectedUsers(prev => {
      const newSelected = prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId];
      setShowBatchActions(newSelected.length > 0);
      return newSelected;
    });
  };

  // 全选/取消全选
  const handleSelectAll = () => {
    if (selectedUsers.length === users.length) {
      setSelectedUsers([]);
      setShowBatchActions(false);
    } else {
      const allUserIds = users.map(user => user.id);
      setSelectedUsers(allUserIds);
      setShowBatchActions(true);
    }
  };

  // 清空选择
  const clearSelection = () => {
    setSelectedUsers([]);
    setShowBatchActions(false);
  };

  // 批量状态更改
  const handleBatchStatusChange = async (isActive: boolean) => {
    if (selectedUsers.length === 0) return;

    const action = isActive ? '激活' : '停用';
    if (!confirm(`确定要${action}选中的 ${selectedUsers.length} 个用户吗？`)) {
      return;
    }

    try {
      setLoading(true);
      const promises = selectedUsers.map(userId =>
        fetch(`/api/admin/users/${userId}/status`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ is_active: isActive }),
        })
      );

      await Promise.all(promises);
      
      // 刷新用户列表
      await fetchUsers(currentPage, searchTerm, statusFilter);
      clearSelection();
      alert(`成功${action}了 ${selectedUsers.length} 个用户`);
    } catch (error) {
      console.error(`批量${action}用户失败:`, error);
      setError(`批量${action}用户失败，请重试`);
    } finally {
      setLoading(false);
    }
  };

  // 批量删除用户
  const handleBatchDelete = async () => {
    if (selectedUsers.length === 0) return;

    if (!confirm(`确定要删除选中的 ${selectedUsers.length} 个用户吗？此操作不可撤销！`)) {
      return;
    }

    try {
      setLoading(true);
      const promises = selectedUsers.map(userId =>
        fetch(`/api/admin/users/${userId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          },
        })
      );

      await Promise.all(promises);
      
      // 刷新用户列表和统计数据
      await fetchUsers(currentPage, searchTerm, statusFilter);
      await fetchStats();
      clearSelection();
      alert(`成功删除了 ${selectedUsers.length} 个用户`);
    } catch (error) {
      console.error('批量删除用户失败:', error);
      setError('批量删除用户失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取用户列表
   * 功能：调用后端 `/api/admin/users/` 接口，支持分页与搜索；
   * 说明：将前端状态筛选（active/inactive）转换为后端所需的 `is_active` 布尔参数；
   * 参数：
   *  - page: 页码（默认1）
   *  - search: 关键词（用户名或邮箱）
   *  - status: 前端状态筛选（"active" | "inactive" | ''），转换为 is_active=true/false
   *  - verification: 验证状态（目前后端未使用，保留占位）
   *  - dateFrom/dateTo/loginMin/loginMax: 高级筛选占位（后端暂未实现）
   */
  const fetchUsers = async (
    page = 1, 
    search = '', 
    status = '', 
    verification = '',
    dateFrom = '',
    dateTo = '',
    loginMin = '',
    loginMax = ''
  ) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        limit: itemsPerPage.toString(),
      });
      
      if (search) params.append('search', search);
      // 将前端传入的 status(active/inactive) 映射为后端的 is_active 布尔参数
      if (status === 'active') {
        params.append('is_active', 'true');
      } else if (status === 'inactive') {
        params.append('is_active', 'false');
      }
      if (verification) params.append('verification', verification);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      if (loginMin) params.append('login_min', loginMin);
      if (loginMax) params.append('login_max', loginMax);

      // 修复API路径，添加正确的斜杠
      const response = await fetch(`/api/admin/users/?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('认证失败，请重新登录');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      console.log('API响应数据:', data); // 调试日志
      
      if (data.success) {
        setUsers(data.data.users || []);
        setTotalUsers(data.data.total || 0);
        setTotalPages(Math.ceil((data.data.total || 0) / itemsPerPage));
      } else {
        throw new Error(data.message || '获取用户列表失败');
      }
    } catch (err) {
      console.error('获取用户列表错误:', err); // 调试日志
      setError(err instanceof Error ? err.message : '获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取用户统计
   * 功能：调用后端“仪表板概览”端点 `/api/admin/dashboard/overview`，
   *      从返回的系统概览中提取与用户相关的统计信息并适配前端使用的结构。
   * 说明：后端新仪表板API返回的是对象模型（非统一 success/data 包裹），
   *      这里做兼容解析：若含有 success 字段则用 data，否则直接用原对象。
   */
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/admin/dashboard/overview', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 统一处理认证失败与其他HTTP错误
        if (response.status === 401 || response.status === 403) {
          throw new Error('认证失败，请重新登录');
        }
        console.warn('获取统计数据失败:', response.status);
        return;
      }

      const raw = await response.json();
      console.log('统计数据响应:', raw);

      // 兼容 success/data 与直接对象两种返回格式
      const overview = (raw && typeof raw === 'object' && 'success' in raw) ? raw.data : raw;

      // 从系统概览中构造前端需要的用户统计结构
      const total_users = overview?.total_users ?? 0;
      const active_users = overview?.active_users ?? 0;
      const inactive_users = Math.max(0, total_users - active_users);
      const new_users_today = overview?.new_users_today ?? 0;

      setStats({
        total_users,
        active_users,
        inactive_users,
        new_users_today,
      });
    } catch (err) {
      console.error('获取统计数据失败:', err);
      setError(err instanceof Error ? err.message : '获取统计数据失败');
    }
  };

  /**
   * 更新用户状态
   * 功能：根据目标状态选择后端的激活/禁用端点，保持与后端路径一致。
   * 说明：后端提供 POST /api/admin/users/{id}/activate 与 /deactivate 两个端点；
   * 参数：
   *  - userId: 用户ID
   *  - isActive: 更新后的目标状态（true=激活；false=禁用）
   */
  const updateUserStatus = async (userId: number, isActive: boolean) => {
    try {
      // 使用后端的 activate/deactivate 端点，避免 404
      const endpoint = isActive ? 'activate' : 'deactivate';
      const response = await fetch(`/api/admin/users/${userId}/${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json',
        },
        // 后端不需要请求体，这里不传 body
      });

      if (response.ok) {
        // 刷新用户列表
        fetchUsers(currentPage, searchTerm, statusFilter);
        fetchStats();
      } else {
        if (response.status === 401 || response.status === 403) {
          throw new Error('认证失败，请重新登录');
        }
        throw new Error('更新用户状态失败');
      }
    } catch (err) {
      console.error('更新用户状态错误:', err); // 调试日志
      setError(err instanceof Error ? err.message : '更新用户状态失败');
    }
  };

  // 搜索处理
  const handleSearch = () => {
    setCurrentPage(1);
    fetchUsers(
      1, 
      searchTerm, 
      statusFilter, 
      verificationFilter,
      registrationDateFrom,
      registrationDateTo,
      loginCountMin,
      loginCountMax
    );
  };

  // 重置搜索
  const handleReset = () => {
    setSearchTerm('');
    setStatusFilter('');
    setVerificationFilter('');
    setRegistrationDateFrom('');
    setRegistrationDateTo('');
    setLoginCountMin('');
    setLoginCountMax('');
    setCurrentPage(1);
    fetchUsers();
  };

  // 分页处理
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchUsers(
      page, 
      searchTerm, 
      statusFilter, 
      verificationFilter,
      registrationDateFrom,
      registrationDateTo,
      loginCountMin,
      loginCountMax
    );
  };

  // 格式化日期显示
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '从未';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 打开重置密码弹窗
  const openResetPasswordModal = (userId: number, username: string) => {
    setResetPasswordUserId(userId);
    setResetPasswordUsername(username);
    setNewPassword('');
    setConfirmPassword('');
    setShowResetPasswordModal(true);
  };

  // 关闭重置密码弹窗
  const closeResetPasswordModal = () => {
    setShowResetPasswordModal(false);
    setResetPasswordUserId(null);
    setResetPasswordUsername('');
    setNewPassword('');
    setConfirmPassword('');
    setResetPasswordLoading(false);
  };

  // 重置用户密码
  const handleResetPassword = async () => {
    if (!resetPasswordUserId) return;

    // 验证密码
    if (!newPassword || newPassword.length < 6) {
      alert('新密码长度至少6个字符');
      return;
    }

    if (newPassword !== confirmPassword) {
      alert('两次输入的密码不一致');
      return;
    }

    setResetPasswordLoading(true);

    try {
      const token = localStorage.getItem('admin_token');
      if (!token) {
        alert('请先登录管理员账户');
        return;
      }

      console.log(`重置用户 ${resetPasswordUserId} 的密码...`);

      const response = await fetch(`/api/admin/users/${resetPasswordUserId}/reset-password/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          new_password: newPassword
        })
      });

      const data = await response.json();
      console.log('重置密码响应:', data);

      if (response.ok && data.success) {
        alert(`用户 ${resetPasswordUsername} 的密码重置成功！`);
        closeResetPasswordModal();
      } else {
        const errorMessage = data.detail || data.message || '重置密码失败';
        alert(`重置密码失败: ${errorMessage}`);
      }
    } catch (error) {
      console.error('重置密码失败:', error);
      alert('重置密码失败，请检查网络连接');
    } finally {
      setResetPasswordLoading(false);
    }
  };

  // 打开删除用户确认弹窗
  const openDeleteModal = (userId: number, username: string, email: string) => {
    setDeleteUserId(userId);
    setDeleteUsername(username);
    setDeleteUserEmail(email);
    setShowDeleteModal(true);
  };

  // 关闭删除用户弹窗
  const closeDeleteModal = () => {
    setShowDeleteModal(false);
    setDeleteUserId(null);
    setDeleteUsername('');
    setDeleteUserEmail('');
    setDeleteLoading(false);
  };

  // 删除用户
  const handleDeleteUser = async () => {
    if (!deleteUserId) return;

    setDeleteLoading(true);

    try {
      const token = localStorage.getItem('admin_token');
      if (!token) {
        alert('请先登录管理员账户');
        return;
      }

      console.log(`删除用户 ${deleteUserId}...`);

      const response = await fetch(`/api/admin/users/${deleteUserId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      console.log('删除用户响应:', data);

      if (response.ok && data.success) {
        alert(`用户 ${deleteUsername} 及其所有相关数据已成功删除！`);
        closeDeleteModal();
        // 重新加载用户列表
        await fetchUsers();
        // 重新加载统计数据
        await fetchStats();
      } else {
        const errorMessage = data.detail || data.message || '删除用户失败';
        alert(`删除用户失败: ${errorMessage}`);
      }
    } catch (error) {
      console.error('删除用户失败:', error);
      alert('删除用户失败，请检查网络连接');
    } finally {
      setDeleteLoading(false);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchUsers(
      currentPage, 
      searchTerm, 
      statusFilter, 
      verificationFilter,
      registrationDateFrom,
      registrationDateTo,
      loginCountMin,
      loginCountMax
    );
    fetchStats();
  }, []);

  if (loading && users.length === 0) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="user-management">
      <div className="header">
        <div className="header-content">
          <button onClick={handleBackToAdmin} className="back-button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回管理系统
          </button>
          <h1>用户管理</h1>
        </div>
      </div>

      {/* 数据统计列已删除 */}

      {/* 搜索和筛选 */}
      <div className="filters">
        <div className="search-group">
          <input
            type="text"
            placeholder="搜索用户名或邮箱..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">全部状态</option>
            <option value="active">活跃</option>
            <option value="inactive">非活跃</option>
          </select>
          <select
            value={verificationFilter}
            onChange={(e) => setVerificationFilter(e.target.value)}
          >
            <option value="">全部验证状态</option>
            <option value="verified">已验证</option>
            <option value="unverified">未验证</option>
          </select>
          <button 
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
            className="advanced-filter-btn"
          >
            {showAdvancedFilters ? '收起高级筛选' : '展开高级筛选'}
          </button>
          <button onClick={handleSearch} className="search-btn">搜索</button>
          <button onClick={handleReset} className="reset-btn">重置</button>
        </div>
        
        {/* 高级筛选选项 */}
        {showAdvancedFilters && (
          <div className="advanced-filters">
            <div className="filter-row">
              <div className="filter-group">
                <label>注册时间范围：</label>
                <input
                  type="date"
                  value={registrationDateFrom}
                  onChange={(e) => setRegistrationDateFrom(e.target.value)}
                  placeholder="开始日期"
                />
                <span className="date-separator">至</span>
                <input
                  type="date"
                  value={registrationDateTo}
                  onChange={(e) => setRegistrationDateTo(e.target.value)}
                  placeholder="结束日期"
                />
              </div>
            </div>
            <div className="filter-row">
              <div className="filter-group">
                <label>登录次数范围：</label>
                <input
                  type="number"
                  value={loginCountMin}
                  onChange={(e) => setLoginCountMin(e.target.value)}
                  placeholder="最小次数"
                  min="0"
                />
                <span className="range-separator">-</span>
                <input
                  type="number"
                  value={loginCountMax}
                  onChange={(e) => setLoginCountMax(e.target.value)}
                  placeholder="最大次数"
                  min="0"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 批量操作栏 */}
      {showBatchActions && (
        <div className="batch-actions">
          <div className="batch-info">
            <span>已选择 {selectedUsers.length} 个用户</span>
            <button onClick={clearSelection} className="clear-selection-btn">
              清空选择
            </button>
          </div>
          <div className="batch-buttons">
            <button 
              onClick={() => handleBatchStatusChange(true)}
              className="batch-btn batch-activate"
            >
              批量激活
            </button>
            <button 
              onClick={() => handleBatchStatusChange(false)}
              className="batch-btn batch-deactivate"
            >
              批量停用
            </button>
            <button 
              onClick={handleBatchDelete}
              className="batch-btn batch-delete"
            >
              批量删除
            </button>
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* 用户表格 */}
      <div className="table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  checked={selectedUsers.length === users.length && users.length > 0}
                  onChange={handleSelectAll}
                  className="select-checkbox"
                />
              </th>
              <th>ID</th>
              <th>用户名</th>
              <th>邮箱</th>
              <th>验证状态</th>
              <th>登录次数</th>
              <th>注册天数</th>
              <th>最后登录</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(user.id)}
                    onChange={() => handleSelectUser(user.id)}
                    className="select-checkbox"
                  />
                </td>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`verification-status ${user.is_verified ? 'verified' : 'unverified'}`}>
                    {formatVerificationStatus(user.is_verified)}
                  </span>
                </td>
                <td>
                  <span className="login-count">
                    {formatLoginCount(user.login_count)}
                  </span>
                </td>
                <td>
                  <span className="registration-days">
                    {calculateDaysSinceRegistration(user.created_at)} 天
                  </span>
                </td>
                <td>{formatDate(user.last_login)}</td>
                <td>
                  <div className="action-buttons">
                    <button
                      onClick={() => openResetPasswordModal(user.id, user.username)}
                      className="action-btn reset-password"
                      title="重置密码"
                    >
                      重置密码
                    </button>
                    <button
                      onClick={() => openDeleteModal(user.id, user.username, user.email)}
                      className="action-btn delete-user"
                      title="删除用户"
                    >
                      删除用户
                    </button>
                    <button
                      onClick={() => updateUserStatus(
                        user.id, 
                        !user.is_active
                      )}
                      className={`action-btn ${user.is_active ? 'deactivate' : 'activate'}`}
                    >
                      {user.is_active ? '禁用' : '启用'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            上一页
          </button>
          
          <span className="page-info">
            第 {currentPage} 页，共 {totalPages} 页
          </span>
          
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            下一页
          </button>
        </div>
      )}

      {/* 重置密码弹窗 */}
      {showResetPasswordModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>重置用户密码</h3>
              <button 
                className="close-btn" 
                onClick={closeResetPasswordModal}
                disabled={resetPasswordLoading}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <p className="user-info">
                正在为用户 <strong>{resetPasswordUsername}</strong> 重置密码
              </p>
              
              <div className="form-group">
                <label htmlFor="newPassword">新密码:</label>
                <input
                  type="password"
                  id="newPassword"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="请输入新密码（至少6个字符）"
                  disabled={resetPasswordLoading}
                  minLength={6}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="confirmPassword">确认密码:</label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="请再次输入新密码"
                  disabled={resetPasswordLoading}
                  minLength={6}
                />
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn-cancel" 
                onClick={closeResetPasswordModal}
                disabled={resetPasswordLoading}
              >
                取消
              </button>
              <button 
                className="btn-confirm" 
                onClick={handleResetPassword}
                disabled={resetPasswordLoading || !newPassword || !confirmPassword}
              >
                {resetPasswordLoading ? '重置中...' : '确认重置'}
              </button>
            </div>
          </div>
        </div>
       )}

      {/* 删除用户确认弹窗 */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-content delete-modal">
            <div className="modal-header">
              <h3>⚠️ 删除用户确认</h3>
              <button 
                className="close-btn" 
                onClick={closeDeleteModal}
                disabled={deleteLoading}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="warning-info">
                <div className="warning-icon">⚠️</div>
                <div className="warning-text">
                  <p><strong>警告：此操作不可撤销！</strong></p>
                  <p>您即将删除以下用户及其所有相关数据：</p>
                </div>
              </div>
              
              <div className="user-details">
                <div className="detail-item">
                  <span className="label">用户名：</span>
                  <span className="value">{deleteUsername}</span>
                </div>
                <div className="detail-item">
                  <span className="label">邮箱：</span>
                  <span className="value">{deleteUserEmail}</span>
                </div>
              </div>
              
              <div className="delete-consequences">
                <h4>将被删除的数据包括：</h4>
                <ul>
                  <li>用户基本信息和账户数据</li>
                  <li>用户上传的所有文件</li>
                  <li>用户创建的所有文档</li>
                  <li>用户的学习资源和记录</li>
                  <li>所有相关的历史记录</li>
                </ul>
              </div>
              
              <div className="confirmation-text">
                <p>请确认您真的要删除此用户吗？</p>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn-cancel" 
                onClick={closeDeleteModal}
                disabled={deleteLoading}
              >
                取消
              </button>
              <button 
                className="btn-delete" 
                onClick={handleDeleteUser}
                disabled={deleteLoading}
              >
                {deleteLoading ? '删除中...' : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
