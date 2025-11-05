import React, { useState, useEffect } from 'react';
import './BackupManagement.css';

interface BackupInfo {
  id: string;
  timestamp: string;
  size: number;
  size_mb: number;
  type: string;
  status: string;
  file_path: string;
  description: string;
  error_message?: string;
}

interface BackupStatistics {
  total_backups: number;
  successful_backups: number;
  failed_backups: number;
  total_size: number;
  total_size_mb: number;
  backup_types: Record<string, number>;
  last_backup_time: string | null;
  oldest_backup_time: string | null;
}

// interface BackupConfig {
//   max_backups: number;
//   backup_interval_hours: number;
//   include_files: boolean;
//   include_database: boolean;
//   include_vector_store: boolean;
//   compress: boolean;
//   backup_dir: string;
// }

const BackupManagement: React.FC = () => {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [statistics, setStatistics] = useState<BackupStatistics | null>(null);
  // const [config, setConfig] = useState<BackupConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBackup, setSelectedBackup] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);

  // 创建备份表单状态
  const [createForm, setCreateForm] = useState({
    type: 'full',
    description: '',
    include_files: true,
    include_database: true,
    include_vector_store: true
  });

  // 配置表单状态
  const [configForm, setConfigForm] = useState({
    max_backups: 30,
    backup_interval_hours: 24,
    include_files: true,
    include_database: true,
    include_vector_store: true,
    compress: true
  });

  // 加载备份列表
  const loadBackups = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/backup/list');
      const data = await response.json();
      
      if (response.ok) {
        setBackups(data.backups);
        setStatistics(data.statistics);
      } else {
        setError('加载备份列表失败');
      }
    } catch (err) {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 加载配置
  const loadConfig = async () => {
    try {
      const response = await fetch('/api/admin/backup/config');
      
      if (!response.ok) {
        console.warn('配置API不可用，使用默认配置');
        return;
      }
      
      const text = await response.text();
      if (!text) {
        console.warn('配置响应为空，使用默认配置');
        return;
      }
      
      const data = JSON.parse(text);
      // setConfig(data.data);
      setConfigForm(data.data);
    } catch (err) {
      console.warn('加载配置失败，使用默认配置:', err);
    }
  };

  // 创建备份
  const createBackup = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/backup/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(createForm),
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setShowCreateModal(false);
        setCreateForm({
          type: 'full',
          description: '',
          include_files: true,
          include_database: true,
          include_vector_store: true
        });
        await loadBackups();
        alert('备份创建成功！');
      } else {
        alert(`备份创建失败: ${data.message}`);
      }
    } catch (err) {
      alert('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 删除备份
  const deleteBackup = async (backupId: string) => {
    if (!confirm('确定要删除这个备份吗？此操作不可逆。')) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/admin/backup/${backupId}`, {
        method: 'DELETE',
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        await loadBackups();
        alert('备份删除成功！');
      } else {
        alert(`备份删除失败: ${data.message}`);
      }
    } catch (err) {
      alert('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 恢复备份
  const restoreBackup = async () => {
    if (!selectedBackup) return;

    try {
      setLoading(true);
      const response = await fetch('/api/admin/backup/restore', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          backup_id: selectedBackup,
          confirm: true
        }),
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setShowRestoreModal(false);
        setSelectedBackup(null);
        alert('备份恢复成功！系统数据已恢复到备份时的状态。');
      } else {
        alert(`备份恢复失败: ${data.message}`);
      }
    } catch (err) {
      alert('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 更新配置
  const updateConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/backup/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configForm),
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setShowConfigModal(false);
        await loadConfig();
        alert('配置更新成功！');
      } else {
        alert(`配置更新失败: ${data.message}`);
      }
    } catch (err) {
      alert('网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 下载备份
  const downloadBackup = (backupId: string) => {
    const link = document.createElement('a');
    link.href = `/api/admin/backup/download/${backupId}`;
    link.download = `backup_${backupId}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 获取状态样式
  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'success': return 'status-success';
      case 'failed': return 'status-failed';
      case 'in_progress': return 'status-progress';
      default: return 'status-unknown';
    }
  };

  // 获取类型标签
  const getTypeLabel = (type: string): string => {
    switch (type) {
      case 'full': return '完整备份';
      case 'database': return '数据库备份';
      case 'files': return '文件备份';
      default: return type;
    }
  };

  useEffect(() => {
    loadBackups();
    loadConfig();
  }, []);

  return (
    <div className="backup-management">
      <div className="backup-header">
        <h2>数据备份管理</h2>
        <div className="backup-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
            disabled={loading}
          >
            创建备份
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => setShowConfigModal(true)}
          >
            备份设置
          </button>
          <button 
            className="btn btn-outline"
            onClick={loadBackups}
            disabled={loading}
          >
            刷新
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* 统计信息 */}
      {statistics && (
        <div className="backup-statistics">
          <div className="stat-card">
            <h3>总备份数</h3>
            <div className="stat-value">{statistics.total_backups}</div>
          </div>
          <div className="stat-card">
            <h3>成功备份</h3>
            <div className="stat-value success">{statistics.successful_backups}</div>
          </div>
          <div className="stat-card">
            <h3>失败备份</h3>
            <div className="stat-value failed">{statistics.failed_backups}</div>
          </div>
          <div className="stat-card">
            <h3>总大小</h3>
            <div className="stat-value">{statistics.total_size_mb.toFixed(2)} MB</div>
          </div>
        </div>
      )}

      {/* 备份列表 */}
      <div className="backup-list">
        <h3>备份列表</h3>
        {loading ? (
          <div className="loading">加载中...</div>
        ) : backups.length === 0 ? (
          <div className="empty-state">暂无备份记录</div>
        ) : (
          <div className="backup-table">
            <table>
              <thead>
                <tr>
                  <th>备份ID</th>
                  <th>类型</th>
                  <th>描述</th>
                  <th>大小</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {backups.map((backup) => (
                  <tr key={backup.id}>
                    <td className="backup-id">{backup.id}</td>
                    <td>
                      <span className="type-badge">{getTypeLabel(backup.type)}</span>
                    </td>
                    <td>{backup.description || '-'}</td>
                    <td>{formatFileSize(backup.size)}</td>
                    <td>
                      <span className={`status-badge ${getStatusClass(backup.status)}`}>
                        {backup.status === 'success' ? '成功' : 
                         backup.status === 'failed' ? '失败' : 
                         backup.status === 'in_progress' ? '进行中' : backup.status}
                      </span>
                    </td>
                    <td>{formatDate(backup.timestamp)}</td>
                    <td>
                      <div className="action-buttons">
                        {backup.status === 'success' && (
                          <>
                            <button
                              className="btn btn-small btn-outline"
                              onClick={() => downloadBackup(backup.id)}
                              title="下载备份"
                            >
                              下载
                            </button>
                            <button
                              className="btn btn-small btn-primary"
                              onClick={() => {
                                setSelectedBackup(backup.id);
                                setShowRestoreModal(true);
                              }}
                              title="恢复备份"
                            >
                              恢复
                            </button>
                          </>
                        )}
                        <button
                          className="btn btn-small btn-danger"
                          onClick={() => deleteBackup(backup.id)}
                          title="删除备份"
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 创建备份模态框 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>创建备份</h3>
              <button 
                className="modal-close"
                onClick={() => setShowCreateModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>备份类型</label>
                <select
                  value={createForm.type}
                  onChange={(e) => setCreateForm({...createForm, type: e.target.value})}
                >
                  <option value="full">完整备份</option>
                  <option value="database">数据库备份</option>
                </select>
              </div>
              <div className="form-group">
                <label>备份描述</label>
                <input
                  type="text"
                  value={createForm.description}
                  onChange={(e) => setCreateForm({...createForm, description: e.target.value})}
                  placeholder="可选的备份描述"
                />
              </div>
              <div className="form-group">
                <label>备份内容</label>
                <div className="checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.include_database}
                      onChange={(e) => setCreateForm({...createForm, include_database: e.target.checked})}
                    />
                    包含数据库
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.include_files}
                      onChange={(e) => setCreateForm({...createForm, include_files: e.target.checked})}
                    />
                    包含文件
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.include_vector_store}
                      onChange={(e) => setCreateForm({...createForm, include_vector_store: e.target.checked})}
                    />
                    包含向量存储
                  </label>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowCreateModal(false)}
              >
                取消
              </button>
              <button 
                className="btn btn-primary"
                onClick={createBackup}
                disabled={loading}
              >
                {loading ? '创建中...' : '创建备份'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 配置模态框 */}
      {showConfigModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>备份设置</h3>
              <button 
                className="modal-close"
                onClick={() => setShowConfigModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>最大备份数量</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={configForm.max_backups}
                  onChange={(e) => setConfigForm({...configForm, max_backups: parseInt(e.target.value)})}
                />
              </div>
              <div className="form-group">
                <label>备份间隔（小时）</label>
                <input
                  type="number"
                  min="1"
                  max="168"
                  value={configForm.backup_interval_hours}
                  onChange={(e) => setConfigForm({...configForm, backup_interval_hours: parseInt(e.target.value)})}
                />
              </div>
              <div className="form-group">
                <label>默认备份内容</label>
                <div className="checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={configForm.include_database}
                      onChange={(e) => setConfigForm({...configForm, include_database: e.target.checked})}
                    />
                    包含数据库
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={configForm.include_files}
                      onChange={(e) => setConfigForm({...configForm, include_files: e.target.checked})}
                    />
                    包含文件
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={configForm.include_vector_store}
                      onChange={(e) => setConfigForm({...configForm, include_vector_store: e.target.checked})}
                    />
                    包含向量存储
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={configForm.compress}
                      onChange={(e) => setConfigForm({...configForm, compress: e.target.checked})}
                    />
                    压缩备份
                  </label>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowConfigModal(false)}
              >
                取消
              </button>
              <button 
                className="btn btn-primary"
                onClick={updateConfig}
                disabled={loading}
              >
                {loading ? '保存中...' : '保存设置'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 恢复确认模态框 */}
      {showRestoreModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>确认恢复备份</h3>
              <button 
                className="modal-close"
                onClick={() => setShowRestoreModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="warning-message">
                <strong>警告：</strong>恢复备份将覆盖当前所有数据，此操作不可逆！
              </div>
              <p>确定要恢复备份 <strong>{selectedBackup}</strong> 吗？</p>
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowRestoreModal(false)}
              >
                取消
              </button>
              <button 
                className="btn btn-danger"
                onClick={restoreBackup}
                disabled={loading}
              >
                {loading ? '恢复中...' : '确认恢复'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BackupManagement;