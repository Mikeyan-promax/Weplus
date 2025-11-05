import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './UserManagement.css';

interface User {
  id: number;
  username: string;
  email: string;
  real_name: string;
  role: 'user' | 'admin' | 'super_admin';
  is_active: boolean;
  created_at: string;
  last_login?: string;
  login_count: number;
  phone?: string;
  department?: string;
  student_id?: string;
}

interface UserStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  new_users_today: number;
}

const UserManagement: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats>({
    total_users: 0,
    active_users: 0,
    admin_users: 0,
    new_users_today: 0
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [usersPerPage] = useState(10);

  // 检查管理员权限
  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      navigate('/admin/login');
      return;
    }
    
    // 模拟加载用户数据
    loadUsers();
  }, [navigate]);

  /**
   * 加载用户列表：相对路径 `/api/admin/users`，避免硬编码端口
   */
  const loadUsers = async () => {
    setLoading(true);
    try {
      const adminToken = localStorage.getItem('admin_token');
      
      // 调用真实API获取用户数据
      const response = await fetch('/api/admin/users', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // 转换API数据格式以匹配前端接口
          const convertedUsers: User[] = result.data.users.map((user: any) => ({
            id: user.id,
            username: user.username,
            email: user.email,
            real_name: user.username, // 使用username作为显示名称
            role: 'user' as const, // 默认角色
            is_active: user.status === 'active',
            created_at: user.created_at,
            last_login: user.last_login,
            login_count: 0, // API暂未提供此字段
            phone: '',
            department: '',
            student_id: ''
          }));
          
          setUsers(convertedUsers);
          
          // 计算统计数据
          const activeUsers = convertedUsers.filter(u => u.is_active).length;
          const adminUsers = convertedUsers.filter(u => u.role === 'admin').length;
          
          setStats({
            total_users: convertedUsers.length,
            active_users: activeUsers,
            admin_users: adminUsers,
            new_users_today: 0 // 暂时设为0，后续可从API获取
          });
        }
      } else {
        console.error('获取用户数据失败:', response.statusText);
        // 如果API调用失败，可以显示错误信息或使用备用数据
      }
    } catch (error) {
      console.error('加载用户数据时出错:', error);
    } finally {
      setLoading(false);
    }
  };
  const handleUserAction = (action: string, userId: number) => {
    switch (action) {
      case 'edit':
        // 编辑用户
        console.log('Edit user:', userId);
        break;
      case 'delete':
        // 删除用户
        if (window.confirm('确定要删除这个用户吗？')) {
          setUsers(users.filter(u => u.id !== userId));
        }
        break;
      case 'toggle':
        // 切换用户状态
        setUsers(users.map(u => 
          u.id === userId ? { ...u, is_active: !u.is_active } : u
        ));
        break;
      default:
        break;
    }
  };

  const handleBackToDashboard = () => {
    navigate('/admin');
  };

  // 过滤用户
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.real_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRole = filterRole === 'all' || user.role === filterRole;
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'active' && user.is_active) ||
                         (filterStatus === 'inactive' && !user.is_active);
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  // 分页
  const indexOfLastUser = currentPage * usersPerPage;
  const indexOfFirstUser = indexOfLastUser - usersPerPage;
  const currentUsers = filteredUsers.slice(indexOfFirstUser, indexOfLastUser);
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getRoleText = (role: string) => {
    switch (role) {
      case 'user': return '普通用户';
      case 'admin': return '管理员';
      case 'super_admin': return '超级管理员';
      default: return role;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'user': return '#28a745';
      case 'admin': return '#ffc107';
      case 'super_admin': return '#dc3545';
      default: return '#6c757d';
    }
  };

  if (loading) {
    return (
      <div className="user-management-loading">
        <div className="loading-spinner"></div>
        <p>加载用户数据...</p>
      </div>
    );
  }

  return (
    <div className="user-management">
      {/* 头部 */}
      <header className="user-management-header">
        <div className="header-left">
          <button className="back-button" onClick={handleBackToDashboard}>
            ← 返回仪表板
          </button>
          <div className="header-title">
            <h1>用户管理</h1>
            <p>管理系统中的所有用户账户</p>
          </div>
        </div>
      </header>

      {/* 统计卡片 */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h3>总用户数</h3>
              <p className="stat-number">{stats.total_users}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h3>活跃用户</h3>
              <p className="stat-number">{stats.active_users}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔑</div>
            <div className="stat-content">
              <h3>管理员</h3>
              <p className="stat-number">{stats.admin_users}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🆕</div>
            <div className="stat-content">
              <h3>今日新增</h3>
              <p className="stat-number">{stats.new_users_today}</p>
            </div>
          </div>
        </div>
      </section>

      {/* 搜索和过滤 */}
      <section className="filters-section">
        <div className="filters-container">
          <div className="search-box">
            <input
              type="text"
              placeholder="搜索用户名、邮箱或姓名..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <span className="search-icon">🔍</span>
          </div>
          
          <div className="filter-group">
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
            >
              <option value="all">所有角色</option>
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
              <option value="super_admin">超级管理员</option>
            </select>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">所有状态</option>
              <option value="active">活跃</option>
              <option value="inactive">禁用</option>
            </select>
          </div>
        </div>
      </section>

      {/* 用户列表 */}
      <section className="users-section">
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>用户信息</th>
                <th>角色</th>
                <th>状态</th>
                <th>注册时间</th>
                <th>最后登录</th>
                <th>登录次数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {currentUsers.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="user-info">
                      <div className="user-avatar">
                        {user.real_name.charAt(0)}
                      </div>
                      <div className="user-details">
                        <div className="user-name">{user.real_name}</div>
                        <div className="user-email">{user.email}</div>
                        <div className="user-username">@{user.username}</div>
                        {user.student_id && (
                          <div className="user-student-id">学号: {user.student_id}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    <span 
                      className="role-badge"
                      style={{ backgroundColor: getRoleColor(user.role) }}
                    >
                      {getRoleText(user.role)}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? '活跃' : '禁用'}
                    </span>
                  </td>
                  <td>{formatDate(user.created_at)}</td>
                  <td>{user.last_login ? formatDate(user.last_login) : '从未登录'}</td>
                  <td>{user.login_count}</td>
                  <td>
                    <div className="actions">
                      <button 
                        className="action-btn edit"
                        onClick={() => handleUserAction('edit', user.id)}
                        title="编辑用户"
                      >
                        ✏️
                      </button>
                      <button 
                        className="action-btn toggle"
                        onClick={() => handleUserAction('toggle', user.id)}
                        title={user.is_active ? '禁用用户' : '启用用户'}
                      >
                        {user.is_active ? '🚫' : '✅'}
                      </button>
                      {user.role !== 'super_admin' && (
                        <button 
                          className="action-btn delete"
                          onClick={() => handleUserAction('delete', user.id)}
                          title="删除用户"
                        >
                          🗑️
                        </button>
                      )}
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
              className="page-btn"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
            >
              上一页
            </button>
            
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                className={`page-btn ${currentPage === page ? 'active' : ''}`}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}
            
            <button 
              className="page-btn"
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
            >
              下一页
            </button>
          </div>
        )}
      </section>
    </div>
  );
};

export default UserManagement;
