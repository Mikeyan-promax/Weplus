import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ResourcePreview from '../ResourcePreview';
import StarRating from '../common/StarRating';
import './StudyResourcesManagement.css';

interface StudyResource {
  id: number;
  title: string;
  description: string;
  file_name: string;
  file_size: number;
  file_type: string;
  category_id: number;
  category_name: string;
  tags: string[] | string;
  download_count: number;
  rating_count: number;
  avg_rating: number;
  created_at: string;
  updated_at: string;
}

interface Category {
  id: number;
  name: string;
  description: string;
  icon: string;
}

interface UploadFormData {
  title: string;
  description: string;
  category_id: number;
  tags: string;
  file: File | null;
}

const StudyResourcesManagement: React.FC = () => {
  const [resources, setResources] = useState<StudyResource[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [previewResource, setPreviewResource] = useState<any>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [uploadForm, setUploadForm] = useState<UploadFormData>({
    title: '',
    description: '',
    category_id: 0,
    tags: '',
    file: null
  });

  // 获取资源列表（管理员视图，使用相对路径）
  // 说明：路径改为 `/api/study-resources/admin/resources`，通过管理员Token鉴权。
  const fetchResources = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20'
      });
      
      if (searchKeyword) {
        params.append('keyword', searchKeyword);
      }
      
      if (selectedCategory) {
        params.append('category_id', selectedCategory.toString());
      }

      // 获取管理员token
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        console.error('管理员认证已过期');
        // 重定向到登录页面
        window.location.href = '/admin/login';
        return;
      }

      console.log('使用管理员Token:', adminToken);
      
      const response = await fetch(`/api/study-resources/admin/resources?${params}`, {
        headers: {
          'Authorization': `Bearer ${adminToken}`
        }
      });
      const data = await response.json();
      
      if (data.success) {
        setResources(data.data || []);
        setTotalPages(data.total_pages || 1);
      }
    } catch (error) {
      console.error('获取资源列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取分类列表（相对路径）
  // 说明：调用 `/api/study-resources/categories`，适配本地与生产环境代理。
  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/study-resources/categories');
      const data = await response.json();
      
      if (data.success) {
        setCategories(data.data);
      }
    } catch (error) {
      console.error('获取分类列表失败:', error);
    }
  };

  // 上传学习资源文件（管理员接口，使用相对路径）
  // 说明：改为 `/api/study-resources/admin/upload`，由服务端处理文件保存。
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!uploadForm.file || !uploadForm.title || !uploadForm.category_id) {
      alert('请填写完整信息并选择文件');
      return;
    }

    try {
      setUploading(true);
      
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('title', uploadForm.title);
      formData.append('description', uploadForm.description);
      formData.append('category_id', uploadForm.category_id.toString());
      formData.append('tags', uploadForm.tags);

      // 获取管理员token
      const adminToken = localStorage.getItem('admin_token');
      if (!adminToken) {
        alert('管理员认证已过期，请重新登录');
        return;
      }

      const response = await fetch('/api/study-resources/admin/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        alert('文件上传成功！');
        setShowUploadModal(false);
        setUploadForm({
          title: '',
          description: '',
          category_id: 0,
          tags: '',
          file: null
        });
        fetchResources();
      } else {
        alert(`上传失败: ${data.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败，请检查网络连接');
    } finally {
      setUploading(false);
    }
  };

  // 删除资源（管理员接口，相对路径）
  const handleDelete = async (resourceId: number) => {
    if (!confirm('确定要删除这个资源吗？此操作不可恢复。')) {
      return;
    }

    try {
      const response = await fetch(`/api/study-resources/${resourceId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        alert('资源删除成功！');
        fetchResources();
      } else {
        alert(`删除失败: ${data.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败，请检查网络连接');
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  useEffect(() => {
    fetchCategories();
    fetchResources();
  }, [currentPage, searchKeyword, selectedCategory]);

  return (
    <div className="study-resources-management">
      <div className="page-header">
        <Link to="/admin" className="back-button">
          <span>←</span>
          返回管理主页
        </Link>
        <h1>学习资源管理</h1>
        <button 
          className="upload-button"
          onClick={() => setShowUploadModal(true)}
        >
          <span>📤</span>
          上传资源
        </button>
      </div>

      {/* 资源预览模态框 */}
      {previewResource && (
        <ResourcePreview
          resourceId={previewResource.id}
          fileName={previewResource.original_filename || previewResource.title}
          fileType={previewResource.file_type}
          fileSize={previewResource.file_size}
          onClose={() => setPreviewResource(null)}
        />
      )}

      {/* 搜索和筛选 */}
      <div className="filters-section">
        <div className="search-box">
          <input
            type="text"
            placeholder="搜索资源标题或描述..."
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
          />
          <button onClick={() => setCurrentPage(1)}>
            🔍 搜索
          </button>
        </div>
        
        <div className="category-filter">
          <select
            value={selectedCategory || ''}
            onChange={(e) => {
              setSelectedCategory(e.target.value ? parseInt(e.target.value) : null);
              setCurrentPage(1);
            }}
          >
            <option value="">所有分类</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 资源列表 */}
      <div className="resources-section">
        {loading ? (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>加载中...</p>
          </div>
        ) : (
          <>
            <div className="resources-table">
              <table>
                <thead>
                  <tr>
                    <th>标题</th>
                    <th>分类</th>
                    <th>文件信息</th>
                    <th>统计</th>
                    <th>上传时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {resources && resources.length > 0 ? resources.map(resource => (
                    <tr key={resource.id}>
                      <td>
                        <div className="resource-title">
                          <Link to={`/resource/${resource.id}`} className="resource-title-link">
                            <h4>{resource.title}</h4>
                          </Link>
                          <p>{resource.description}</p>
                          {resource.tags && (
                            (Array.isArray(resource.tags) && resource.tags.length > 0) ||
                            (typeof resource.tags === 'string' && resource.tags.trim().length > 0)
                          ) && (
                            <div className="tags">
                              {Array.isArray(resource.tags) ? (
                                resource.tags.map((tag, index) => (
                                  <span key={index} className="tag">{tag}</span>
                                ))
                              ) : (
                                resource.tags.split(',').map((tag, index) => (
                                  <span key={index} className="tag">{tag.trim()}</span>
                                ))
                              )}
                            </div>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="category-badge">
                          {resource.category_name}
                        </span>
                      </td>
                      <td>
                        <div className="file-info">
                          <p><strong>{resource.file_name}</strong></p>
                          <p>{formatFileSize(resource.file_size)}</p>
                          <p className="file-type">{resource.file_type}</p>
                        </div>
                      </td>
                      <td>
                        <div className="stats">
                          <p>📥 {resource.download_count} 次下载</p>
                          <div className="rating-display">
                            <StarRating 
                              rating={resource.avg_rating || 0} 
                              readonly 
                              size="small" 
                              showValue 
                            />
                            <span className="rating-count">({resource.rating_count} 评分)</span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="dates">
                          <p>{formatDate(resource.created_at)}</p>
                          {resource.updated_at !== resource.created_at && (
                            <p className="updated">更新: {formatDate(resource.updated_at)}</p>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="actions">
                          <button 
                            className="preview-btn"
                            onClick={() => setPreviewResource(resource)}
                          >
                            👁️ 预览
                          </button>
                          <button 
                            className="download-btn"
                            onClick={() => window.open(`/api/study-resources/${resource.id}/download`, '_blank')}
                          >
                            📥 下载
                          </button>
                          <button 
                            className="delete-btn"
                            onClick={() => handleDelete(resource.id)}
                          >
                            🗑️ 删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={6} style={{textAlign: 'center', padding: '40px'}}>
                        {loading ? '加载中...' : '暂无资源'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* 分页 */}
            {totalPages > 1 && (
              <div className="pagination">
                <button 
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                >
                  上一页
                </button>
                <span>第 {currentPage} 页，共 {totalPages} 页</span>
                <button 
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* 上传模态框 */}
      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>上传学习资源</h2>
              <button 
                className="close-btn"
                onClick={() => setShowUploadModal(false)}
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleUpload} className="upload-form">
              <div className="form-group">
                <label>资源标题 *</label>
                <input
                  type="text"
                  value={uploadForm.title}
                  onChange={(e) => setUploadForm({...uploadForm, title: e.target.value})}
                  placeholder="请输入资源标题"
                  required
                />
              </div>

              <div className="form-group">
                <label>资源描述</label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({...uploadForm, description: e.target.value})}
                  placeholder="请输入资源描述"
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>资源分类 *</label>
                <select
                  value={uploadForm.category_id}
                  onChange={(e) => setUploadForm({...uploadForm, category_id: parseInt(e.target.value)})}
                  required
                >
                  <option value={0}>请选择分类</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>标签</label>
                <input
                  type="text"
                  value={uploadForm.tags}
                  onChange={(e) => setUploadForm({...uploadForm, tags: e.target.value})}
                  placeholder="请输入标签，用逗号分隔"
                />
              </div>

              <div className="form-group">
                <label>选择文件 *</label>
                <input
                  type="file"
                  onChange={(e) => setUploadForm({...uploadForm, file: e.target.files?.[0] || null})}
                  accept=".pdf,.doc,.docx,.txt,.md,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.7z,.jpg,.jpeg,.png,.gif,.mp4,.avi,.mov,.mp3,.wav,.ogg,.aac,.m4a,.flac"
                  required
                />
                <p className="file-hint">
                  支持的文件类型：PDF、Word、Excel、PowerPoint、文本、图片、视频、音频（MP3、WAV等）、压缩包等
                </p>
              </div>

              <div className="form-actions">
                <button 
                  type="button" 
                  onClick={() => setShowUploadModal(false)}
                  disabled={uploading}
                >
                  取消
                </button>
                <button 
                  type="submit" 
                  disabled={uploading}
                  className="primary"
                >
                  {uploading ? '上传中...' : '上传'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudyResourcesManagement;
