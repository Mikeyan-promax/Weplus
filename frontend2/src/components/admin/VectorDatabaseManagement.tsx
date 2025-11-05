import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './VectorDatabaseManagement.css';

interface VectorStats {
  total_vectors: number;
  total_documents: number;
  index_size: number;
  last_updated: string;
  embedding_model: string;
  vector_dimension: number;
}

interface IndexInfo {
  name: string;
  type: string;
  size_mb: number;
  document_count: number;
  vector_count: number;
  created_at?: string;
  last_updated?: string;
  status?: 'healthy' | 'rebuilding' | 'error';
}

const VectorDatabaseManagement: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<VectorStats>({
    total_vectors: 0,
    total_documents: 0,
    index_size: 0,
    last_updated: '',
    embedding_model: '',
    vector_dimension: 0
  });
  const [indexes, setIndexes] = useState<IndexInfo[]>([]);
  const [rebuilding, setRebuilding] = useState(false);
  const [rebuildProgress, setRebuildProgress] = useState(0);

  // 检查管理员权限
  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      navigate('/admin/login');
      return;
    }
    loadVectorStats();
  }, [navigate]);

  const loadVectorStats = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/admin/vector/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
        setIndexes(data.collections || []);
      } else {
        console.error('Failed to load vector stats');
        // 如果API失败，设置空数据而不是模拟数据
        setStats({
          total_vectors: 0,
          total_documents: 0,
          index_size: 0,
          last_updated: new Date().toISOString(),
          embedding_model: 'DeepSeek',
          vector_dimension: 1536
        });
        setIndexes([]);
      }
    } catch (error) {
      console.error('Failed to load vector stats:', error);
      // 如果API失败，设置空数据而不是模拟数据
      setStats({
        total_vectors: 0,
        total_documents: 0,
        index_size: 0,
        last_updated: new Date().toISOString(),
        embedding_model: 'DeepSeek',
        vector_dimension: 1536
      });
      setIndexes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRebuildIndex = async (indexName: string) => {
    if (window.confirm(`确定要重建索引 "${indexName}" 吗？这可能需要一些时间。`)) {
      setRebuilding(true);
      setRebuildProgress(0);

      try {
        const response = await fetch(`http://localhost:8000/api/admin/vector/rebuild/${indexName}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          }
        });

        if (response.ok) {
          // 模拟重建进度
          const progressInterval = setInterval(() => {
            setRebuildProgress(prev => {
              if (prev >= 100) {
                clearInterval(progressInterval);
                setRebuilding(false);
                setRebuildProgress(0);
                // 更新索引状态
                setIndexes(indexes.map(idx => 
                  idx.name === indexName 
                    ? { ...idx, status: 'healthy', last_updated: new Date().toISOString() }
                    : idx
                ));
                alert('索引重建完成');
                return 100;
              }
              return prev + 10;
            });
          }, 500);

          // 更新索引状态为重建中
          setIndexes(indexes.map(idx => 
            idx.name === indexName ? { ...idx, status: 'rebuilding' } : idx
          ));
        } else {
          alert('索引重建失败');
          setRebuilding(false);
          setRebuildProgress(0);
        }
      } catch (error) {
        console.error('Rebuild index error:', error);
        alert('索引重建失败');
        setRebuilding(false);
        setRebuildProgress(0);
      }
    }
  };

  const handleClearIndex = async (indexName: string) => {
    if (window.confirm(`确定要清空索引 "${indexName}" 吗？这将删除所有向量数据！`)) {
      try {
        const response = await fetch(`http://localhost:8000/api/admin/vector/clear/${indexName}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          }
        });

        if (response.ok) {
          // 更新索引信息
          setIndexes(indexes.map(idx => 
            idx.name === indexName 
              ? { ...idx, vector_count: 0, size: 0, last_updated: new Date().toISOString() }
              : idx
          ));
          // 重新加载统计信息
          await loadVectorStats();
          alert('索引清空完成');
        } else {
          alert('索引清空失败');
        }
      } catch (error) {
        console.error('Clear index error:', error);
        alert('索引清空失败');
      }
    }
  };

  const handleBackToDashboard = () => {
    navigate('/admin');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return '正常';
      case 'rebuilding': return '重建中';
      case 'error': return '错误';
      default: return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#28a745';
      case 'rebuilding': return '#ffc107';
      case 'error': return '#dc3545';
      default: return '#6c757d';
    }
  };

  if (loading) {
    return (
      <div className="vector-db-loading">
        <div className="loading-spinner"></div>
        <p>加载向量数据库信息...</p>
      </div>
    );
  }

  return (
    <div className="vector-database-management">
      {/* 头部 */}
      <header className="vector-db-header">
        <div className="header-left">
          <button className="back-button" onClick={handleBackToDashboard}>
            ← 返回仪表板
          </button>
          <div className="header-title">
            <h1>向量数据库管理</h1>
            <p>管理向量索引和嵌入数据</p>
          </div>
        </div>
        <div className="header-actions">
          <button 
            className="refresh-btn"
            onClick={loadVectorStats}
            disabled={loading}
          >
            🔄 刷新数据
          </button>
        </div>
      </header>

      {/* 统计卡片 */}
      <section className="vector-stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">🔢</div>
            <div className="stat-content">
              <h3>总向量数</h3>
              <p className="stat-number">{stats?.total_vectors?.toLocaleString() || '0'}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📚</div>
            <div className="stat-content">
              <h3>文档数量</h3>
              <p className="stat-number">{stats?.total_documents || '0'}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💾</div>
            <div className="stat-content">
              <h3>索引大小</h3>
              <p className="stat-number">{formatFileSize(stats?.index_size || 0)}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🤖</div>
            <div className="stat-content">
              <h3>嵌入模型</h3>
              <p className="stat-number">{stats?.embedding_model || 'N/A'}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📐</div>
            <div className="stat-content">
              <h3>向量维度</h3>
              <p className="stat-number">{stats?.vector_dimension || 0}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🕒</div>
            <div className="stat-content">
              <h3>最后更新</h3>
              <p className="stat-number">{formatDate(stats?.last_updated || '')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* 索引管理 */}
      <section className="indexes-section">
        <div className="section-header">
          <h2>索引管理</h2>
          <p>管理不同类型的向量索引</p>
        </div>

        {rebuilding && (
          <div className="rebuild-progress">
            <div className="progress-info">
              <span>正在重建索引...</span>
              <span>{rebuildProgress}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${rebuildProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        <div className="indexes-grid">
          {indexes.map((index) => (
            <div key={index.name} className="index-card">
              <div className="index-header">
                <div className="index-info">
                  <h3>{index.name}</h3>
                  <span className="index-type">{index.type}</span>
                </div>
                <span 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(index.status || 'healthy') }}
                >
                  {getStatusText(index.status || 'healthy')}
                </span>
              </div>
              
              <div className="index-stats">
                <div className="stat-item">
                  <span className="stat-label">向量数量:</span>
                  <span className="stat-value">{index.vector_count.toLocaleString()}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">文档数量:</span>
                  <span className="stat-value">{index.document_count}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">索引大小:</span>
                  <span className="stat-value">{index.size_mb.toFixed(2)} MB</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">创建时间:</span>
                  <span className="stat-value">{index.created_at ? formatDate(index.created_at) : '未知'}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">最后更新:</span>
                  <span className="stat-value">{index.last_updated ? formatDate(index.last_updated) : '未知'}</span>
                </div>
              </div>

              <div className="index-actions">
                <button 
                  className="action-btn rebuild"
                  onClick={() => handleRebuildIndex(index.name)}
                  disabled={rebuilding || (index.status || 'healthy') === 'rebuilding'}
                >
                  🔄 重建索引
                </button>
                <button 
                  className="action-btn clear"
                  onClick={() => handleClearIndex(index.name)}
                  disabled={rebuilding || (index.status || 'healthy') === 'rebuilding'}
                >
                  🗑️ 清空索引
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default VectorDatabaseManagement;