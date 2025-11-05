import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './DocumentManagement.css';

interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  upload_time: string;
  uploader_id: number;
  uploader_name: string;
  status: 'processing' | 'completed' | 'failed';
  vector_count?: number;
  description?: string;
  rag_document_id?: string; // RAG系统的真实文档ID
}

interface DocumentStats {
  total_documents: number;
  processing_documents: number;
  completed_documents: number;
  failed_documents: number;
  total_size: number;
  total_vectors: number;
}

/**
 * 将未知错误规范化为 Error 对象，避免 TS 在 catch 子句中将错误类型标记为 unknown 导致的属性访问报错。
 * 返回一个始终可用的 Error，便于统一日志与提示。
 */
const normalizeError = (err: unknown): Error => {
  if (err instanceof Error) return err;
  if (typeof err === 'string') return new Error(err);
  try {
    return new Error(JSON.stringify(err));
  } catch {
    return new Error('未知错误');
  }
};

const DocumentManagement: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<DocumentStats>({
    total_documents: 0,
    processing_documents: 0,
    completed_documents: 0,
    failed_documents: 0,
    total_size: 0,
    total_vectors: 0
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [documentsPerPage] = useState(10);
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // 检查管理员权限
  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (!adminToken) {
      navigate('/admin/login');
      return;
    }
    
    // 模拟加载文档数据
    loadDocuments();
  }, [navigate]);

  /**
   * 加载文档列表
   * - 使用相对路径 `/api/rag/documents` 以同源代理（避免硬编码 localhost:8000）
   * - 统一错误处理，避免 TS `catch` 的 `unknown` 报错
   */
  const loadDocuments = async () => {
    setLoading(true);
    try {
      console.log('开始加载文档列表...');
      console.log('请求URL: /api/rag/documents');
      console.log('认证Token:', localStorage.getItem('admin_token') ? '存在' : '不存在');
      
      // 调用真实的RAG API获取文档列表
      const response = await fetch('/api/rag/documents', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
        }
      });

      console.log('响应状态:', response.status);
      console.log('响应头:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const data = await response.json();
        console.log('API响应数据:', data);
        
        // 转换API数据格式为组件需要的格式
        const convertedDocuments: Document[] = data.documents?.map((doc: any, index: number) => ({
          id: index + 1,
          filename: doc.id || `doc_${index}`, // 使用RAG API返回的真实文档ID
          original_filename: doc.title || '未命名文档',
          file_size: doc.content_length || 0,
          file_type: 'text/plain',
          upload_time: doc.processed_at || new Date().toISOString(),
          uploader_id: 1,
          uploader_name: '系统',
          status: 'completed' as const,
          vector_count: doc.chunk_count || 0,
          description: doc.title || '文档描述',
          rag_document_id: doc.id // 保存RAG系统的真实文档ID用于删除
        })) || [];

        console.log('转换后的文档数据:', convertedDocuments);
        setDocuments(convertedDocuments);
        
        // 计算统计信息
        const totalSize = convertedDocuments.reduce((sum, doc) => sum + doc.file_size, 0);
        const totalVectors = convertedDocuments.reduce((sum, doc) => sum + (doc.vector_count || 0), 0);

        setStats({
          total_documents: convertedDocuments.length,
          processing_documents: convertedDocuments.filter(d => d.status === 'processing').length,
          completed_documents: convertedDocuments.filter(d => d.status === 'completed').length,
          failed_documents: convertedDocuments.filter(d => d.status === 'failed').length,
          total_size: totalSize,
          total_vectors: totalVectors
        });
      } else {
        const errorText = await response.text();
        console.error('API响应错误:', response.status, response.statusText, errorText);
        // 如果API调用失败，设置空数据
        setDocuments([]);
        setStats({
          total_documents: 0,
          processing_documents: 0,
          completed_documents: 0,
          failed_documents: 0,
          total_size: 0,
          total_vectors: 0
        });
      }
    } catch (error) {
      const e = normalizeError(error);
      console.error('Failed to load documents:', e);
      console.error('错误详情:', {
        name: e.name,
        message: e.message,
        stack: e.stack
      });
      // 出错时设置空数据
      setDocuments([]);
      setStats({
        total_documents: 0,
        processing_documents: 0,
        completed_documents: 0,
        failed_documents: 0,
        total_size: 0,
        total_vectors: 0
      });
    } finally {
      setLoading(false);
    }
  };



  /**
   * 处理文件上传（多文件）
   * - 走 `/api/rag/documents/upload` 相对路径
   * - 使用管理员 Token 认证
   */
  const handleFileUpload = async (files: FileList) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const uploadPromises = Array.from(files).map(async (file, index) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/rag/documents/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
          },
          body: formData
        });

        if (response.ok) {
          const result = await response.json();
          setUploadProgress(((index + 1) / files.length) * 100);
          return result;
        } else {
          throw new Error(`上传文件 ${file.name} 失败`);
        }
      });

      const results = await Promise.allSettled(uploadPromises);
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      const failCount = results.length - successCount;

      if (successCount > 0) {
        // 重新加载文档列表
        await loadDocuments();
        if (failCount === 0) {
          alert(`成功上传 ${successCount} 个文件`);
        } else {
          alert(`成功上传 ${successCount} 个文件，${failCount} 个文件上传失败`);
        }
      } else {
        alert('所有文件上传失败');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('文件上传失败');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setShowUploadModal(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  /**
   * 处理文档操作（重新处理、删除、批量操作）
   * - 所有接口统一使用 `/api/...` 相对路径
   * - 对错误进行规范化处理（部分场景）
   */
  const handleDocumentAction = async (action: string, documentId?: number) => {
    switch (action) {
      case 'reprocess':
        if (documentId) {
          try {
            const document = documents.find(d => d.id === documentId);
            if (document) {
              // 调用RAG API重新处理文档
              const response = await fetch(`/api/rag/documents/${document.filename}/reprocess`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
              });

              if (response.ok) {
                setDocuments(documents.map(d => 
                  d.id === documentId ? { ...d, status: 'processing' } : d
                ));
              } else {
                alert('重新处理文档失败');
              }
            }
          } catch (error) {
            console.error('Reprocess document error:', error);
            alert('重新处理文档失败');
          }
        }
        break;
      case 'delete':
        if (documentId) {
          if (window.confirm('确定要删除这个文档吗？此操作将永久删除文档及其向量数据，无法恢复！')) {
            try {
              const document = documents.find(d => d.id === documentId);
              if (document) {
                // 显示删除进度
                const loadingMessage = '正在删除文档和向量数据...';
                console.log(loadingMessage);
                
                // 调用RAG API删除文档
                const response = await fetch(`/api/rag/documents/${document.rag_document_id || document.filename}`, {
                  method: 'DELETE',
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                  }
                });

                if (response.ok) {
                  const result = await response.json();
                  console.log('删除成功:', result);
                  
                  // 更新文档列表
                  setDocuments(documents.filter(d => d.id !== documentId));
                  
                  // 显示详细的删除成功信息
                  alert(`✅ 文档删除成功！\n文档ID: ${result.document_id}\n删除详情: ${JSON.stringify(result.delete_details, null, 2)}`);
                } else {
                  const errorData = await response.json().catch(() => ({}));
                  console.error('删除失败:', errorData);
                  alert(`❌ 删除文档失败！\n错误信息: ${errorData.detail || '未知错误'}\n状态码: ${response.status}`);
                }
              }
            } catch (error) {
              console.error('Delete document error:', error);
              const errorMessage = normalizeError(error).message;
              alert(`❌ 删除文档时发生网络错误！\n错误详情: ${errorMessage}`);
            }
          }
        }
        break;
      case 'batch_delete':
        if (selectedDocuments.length > 0) {
          if (window.confirm(`确定要删除选中的 ${selectedDocuments.length} 个文档吗？此操作将永久删除文档及其向量数据，无法恢复！`)) {
            try {
              console.log(`开始批量删除 ${selectedDocuments.length} 个文档...`);
              
              const selectedDocs = documents.filter(d => selectedDocuments.includes(d.id));
              const deletePromises = selectedDocs.map(doc => 
              fetch(`/api/rag/documents/${doc.rag_document_id || doc.filename}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
              }).then(response => ({
                doc,
                response,
                success: response.ok
              }))
              );

              const results = await Promise.allSettled(deletePromises);
              
              let successCount = 0;
              let failedCount = 0;
              const successfulDocs = [];
              const failedDocs = [];
              
              for (const result of results) {
                if (result.status === 'fulfilled' && result.value.success) {
                  successCount++;
                  successfulDocs.push(result.value.doc);
                } else {
                  failedCount++;
                  if (result.status === 'fulfilled') {
                    failedDocs.push(result.value?.doc || { filename: '未知文档' });
                  } else {
                    failedDocs.push({ filename: '未知文档' });
                  }
                }
              }
              
              // 更新文档列表，只移除成功删除的文档
              if (successCount > 0) {
                const successfulIds = successfulDocs.map(doc => doc.id);
                setDocuments(documents.filter(d => !successfulIds.includes(d.id)));
                setSelectedDocuments([]);
              }
              
              // 显示详细的批量删除结果
              if (failedCount === 0) {
                alert(`✅ 批量删除成功！\n成功删除 ${successCount} 个文档`);
              } else if (successCount === 0) {
                alert(`❌ 批量删除失败！\n所有 ${failedCount} 个文档删除失败\n失败文档: ${failedDocs.map(d => d.filename).join(', ')}`);
              } else {
                alert(`⚠️ 批量删除部分成功！\n✅ 成功删除: ${successCount} 个文档\n❌ 删除失败: ${failedCount} 个文档\n失败文档: ${failedDocs.map(d => d.filename).join(', ')}`);
              }
              
              console.log(`批量删除完成: 成功 ${successCount} 个，失败 ${failedCount} 个`);
            } catch (error) {
              console.error('Batch delete error:', error);
              const errorMessage = error instanceof Error ? error.message : '未知错误';
              alert(`❌ 批量删除时发生网络错误！\n错误详情: ${errorMessage}`);
            }
          }
        }
        break;
      case 'batch_reprocess':
        if (selectedDocuments.length > 0) {
          try {
            const selectedDocs = documents.filter(d => selectedDocuments.includes(d.id));
            const reprocessPromises = selectedDocs.map(doc => 
              fetch(`/api/rag/documents/${doc.filename}/reprocess`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
              })
            );

            const results = await Promise.allSettled(reprocessPromises);
            const successCount = results.filter(r => r.status === 'fulfilled').length;
            
            if (successCount > 0) {
              setDocuments(documents.map(d => 
                selectedDocuments.includes(d.id) ? { ...d, status: 'processing' } : d
              ));
              setSelectedDocuments([]);
              if (successCount < selectedDocuments.length) {
                alert(`成功重新处理 ${successCount} 个文档，${selectedDocuments.length - successCount} 个文档处理失败`);
              }
            } else {
              alert('批量重新处理失败');
            }
          } catch (error) {
            console.error('Batch reprocess error:', error);
            alert('批量重新处理失败');
          }
        }
        break;
      default:
        break;
    }
  };

  const handleBackToDashboard = () => {
    navigate('/admin');
  };

  const handleSelectDocument = (documentId: number) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocuments.length === filteredDocuments.length) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(filteredDocuments.map(d => d.id));
    }
  };

  // 过滤文档
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.uploader_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (doc.description && doc.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = filterStatus === 'all' || doc.status === filterStatus;
    const matchesType = filterType === 'all' || doc.file_type.includes(filterType);
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // 分页
  const indexOfLastDocument = currentPage * documentsPerPage;
  const indexOfFirstDocument = indexOfLastDocument - documentsPerPage;
  const currentDocuments = filteredDocuments.slice(indexOfFirstDocument, indexOfLastDocument);
  const totalPages = Math.ceil(filteredDocuments.length / documentsPerPage);

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
      case 'processing': return '处理中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      default: return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return '#ffc107';
      case 'completed': return '#28a745';
      case 'failed': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('presentation')) return '📊';
    if (fileType.includes('text')) return '📃';
    if (fileType.includes('image')) return '🖼️';
    return '📁';
  };

  if (loading) {
    return (
      <div className="document-management-loading">
        <div className="loading-spinner"></div>
        <p>加载文档数据...</p>
      </div>
    );
  }

  return (
    <div className="document-management">
      {/* 头部 */}
      <header className="document-management-header">
        <div className="header-left">
          <button className="back-button" onClick={handleBackToDashboard}>
            ← 返回仪表板
          </button>
          <div className="header-title">
            <h1>文档管理</h1>
            <p>管理系统中的所有文档和向量数据</p>
          </div>
        </div>
        <div className="header-actions">
          <button 
            className="upload-btn"
            onClick={() => setShowUploadModal(true)}
            disabled={uploading}
          >
            📤 上传文档
          </button>
          {selectedDocuments.length > 0 && (
            <div className="batch-actions">
              <button 
                className="batch-btn reprocess"
                onClick={() => handleDocumentAction('batch_reprocess')}
              >
                批量重新处理 ({selectedDocuments.length})
              </button>
              <button 
                className="batch-btn delete"
                onClick={() => handleDocumentAction('batch_delete')}
              >
                批量删除 ({selectedDocuments.length})
              </button>
            </div>
          )}
        </div>
      </header>

      {/* 统计卡片 */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📚</div>
            <div className="stat-content">
              <h3>总文档数</h3>
              <p className="stat-number">{stats.total_documents}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h3>已完成</h3>
              <p className="stat-number">{stats.completed_documents}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⚡</div>
            <div className="stat-content">
              <h3>处理中</h3>
              <p className="stat-number">{stats.processing_documents}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🔢</div>
            <div className="stat-content">
              <h3>向量总数</h3>
              <p className="stat-number">{stats.total_vectors}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💾</div>
            <div className="stat-content">
              <h3>存储大小</h3>
              <p className="stat-number">{formatFileSize(stats.total_size)}</p>
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
              placeholder="搜索文档名称、上传者或描述..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <span className="search-icon">🔍</span>
          </div>
          
          <div className="filter-group">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">所有状态</option>
              <option value="completed">已完成</option>
              <option value="processing">处理中</option>
              <option value="failed">失败</option>
            </select>
            
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">所有类型</option>
              <option value="pdf">PDF</option>
              <option value="word">Word</option>
              <option value="text">文本</option>
              <option value="presentation">演示文稿</option>
            </select>
          </div>
        </div>
      </section>

      {/* 文档列表 */}
      <section className="documents-section">
        <div className="documents-table-container">
          <table className="documents-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedDocuments.length === filteredDocuments.length && filteredDocuments.length > 0}
                    onChange={handleSelectAll}
                  />
                </th>
                <th>文档信息</th>
                <th>状态</th>
                <th>文件大小</th>
                <th>向量数量</th>
                <th>上传者</th>
                <th>上传时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {currentDocuments.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedDocuments.includes(doc.id)}
                      onChange={() => handleSelectDocument(doc.id)}
                    />
                  </td>
                  <td>
                    <div className="document-info">
                      <div className="document-icon">
                        {getFileTypeIcon(doc.file_type)}
                      </div>
                      <div className="document-details">
                        <div className="document-name">{doc.original_filename}</div>
                        <div className="document-filename">{doc.filename}</div>
                        {doc.description && (
                          <div className="document-description">{doc.description}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(doc.status) }}
                    >
                      {getStatusText(doc.status)}
                    </span>
                  </td>
                  <td>{formatFileSize(doc.file_size)}</td>
                  <td>{doc.vector_count || '-'}</td>
                  <td>{doc.uploader_name}</td>
                  <td>{formatDate(doc.upload_time)}</td>
                  <td>
                    <div className="actions">
                      {doc.status === 'failed' && (
                        <button 
                          className="action-btn reprocess"
                          onClick={() => handleDocumentAction('reprocess', doc.id)}
                          title="重新处理"
                        >
                          🔄
                        </button>
                      )}
                      <button 
                        className="action-btn download"
                        onClick={() => console.log('Download document:', doc.id)}
                        title="下载文档"
                      >
                        📥
                      </button>
                      <button 
                        className="action-btn delete"
                        onClick={() => handleDocumentAction('delete', doc.id)}
                        title="删除文档"
                      >
                        🗑️
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

      {/* 文件上传模态框 */}
      {showUploadModal && (
        <div className="upload-modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
            <div className="upload-modal-header">
              <h3>上传文档</h3>
              <button 
                className="close-btn"
                onClick={() => setShowUploadModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="upload-modal-content">
              {uploading ? (
                <div className="upload-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p>上传进度: {Math.round(uploadProgress)}%</p>
                </div>
              ) : (
                <div 
                  className="upload-area"
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  <div className="upload-icon">📁</div>
                  <p>拖拽文件到此处或点击选择文件</p>
                  <p className="upload-hint">支持 PDF, DOC, DOCX, TXT, PPT, PPTX 等格式</p>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt,.ppt,.pptx"
                    onChange={(e) => {
                      if (e.target.files) {
                        handleFileUpload(e.target.files);
                      }
                    }}
                    style={{ display: 'none' }}
                    id="file-input"
                  />
                  <label htmlFor="file-input" className="upload-button">
                    选择文件
                  </label>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManagement;
