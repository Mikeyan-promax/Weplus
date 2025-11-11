import React, { useState, useEffect } from 'react';
import ResourcePreview from './ResourcePreview';
import StarRating from './StarRating';
import RatingModal from './RatingModal';
import './StudyResources.css';

interface Resource {
  id: number;
  title: string;
  description?: string;
  category_id: number;
  file_path: string;
  file_size: number;
  file_type: string;
  download_count: number;
  rating_avg?: number;
  rating_count?: number;
  upload_time: string;
  created_at: string;
  updated_at: string;
  tags?: string | string[];
  status: string;
  difficulty_level?: string;
  original_filename?: string;
  category_name?: string;
}

interface Category {
  id: number;
  name: string;
  code: string;
  description: string;
  icon?: string;
  sort_order: number;
  is_active: boolean;
  resource_count?: number;
}

const StudyResources: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<number | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [resources, setResources] = useState<Resource[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [previewResource, setPreviewResource] = useState<Resource | null>(null);
  const [ratingResource, setRatingResource] = useState<Resource | null>(null);

  // 获取分类列表（使用相对路径以适配代理/生产环境）
  // 说明：改为调用 `/api/study-resources/categories`，避免硬编码 localhost，便于通过 Vite/Nginx 代理转发。
  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/study-resources/categories');
      const data = await response.json();
      
      if (data.success) {
        // 函数级注释：
        // - 前端容错过滤：隐藏名称为“英语四六级”或代码为 `cet` 的分类；
        // - 与后端保持一致的最小改动策略，仅在展示层隐藏，不修改数据库。
        const filtered = (data.data || []).filter((c: any) => c?.name !== '英语四六级' && c?.code !== 'cet');
        setCategories(filtered);
      }
    } catch (error) {
      console.error('获取分类列表失败:', error);
    }
  };

  // 获取资源列表（使用相对路径，以免跨域/环境差异）
  // 说明：请求路径改为 `/api/study-resources/resources` 并保留查询参数构建逻辑。
  const fetchResources = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20'
      });
      
      if (searchTerm) {
        params.append('keyword', searchTerm);
      }
      
      if (selectedCategory !== 'all') {
        params.append('category_id', selectedCategory.toString());
      }

      const response = await fetch(`/api/study-resources/resources?${params}`);
      const data = await response.json();
      
      if (data.success) {
        // 后端直接返回资源数组，不是嵌套在resources字段中
        const resourcesWithCategory = data.data.map((resource: Resource) => ({
          ...resource,
          category_name: categories.find(cat => cat.id === resource.category_id)?.name || '未知分类'
        }));
        setResources(resourcesWithCategory);
        // 暂时设置为1页，后续可以添加分页支持
        setTotalPages(1);
      }
    } catch (error) {
      console.error('获取资源列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 提交评分（使用相对路径，避免硬编码域名）
  // 说明：评分接口改为 `/api/study-resources/rate/:id`，以适配不同部署环境。
  const handleRatingSubmit = async (rating: number, comment?: string) => {
    if (!ratingResource) return;

    try {
      const response = await fetch(`/api/study-resources/rate/${ratingResource.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rating,
          comment
        })
      });

      if (!response.ok) {
        throw new Error('评分提交失败');
      }

      const result = await response.json();
      
      if (result.success) {
        // 刷新资源列表以显示更新的评分
        await fetchResources();
        alert('评分提交成功！');
      } else {
        throw new Error(result.message || '评分提交失败');
      }
    } catch (error) {
      console.error('评分提交失败:', error);
      throw error;
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchCategories();
  }, []);

  // 当分类数据加载完成后，获取资源列表
  useEffect(() => {
    if (categories.length > 0) {
      fetchResources();
    }
  }, [categories, selectedCategory, searchTerm, currentPage]);

  // 触发资源下载（改为相对路径，前端同域直连）
  // 说明：使用 `window.open('/api/study-resources/:id/download')`，由浏览器发起下载，避免跨域问题。
  const handleDownload = (resourceId: number) => {
    try {
      // 显示下载开始提示
      console.log('开始下载资源:', resourceId);
      
      // 使用window.open直接下载，这样会自动处理认证和文件名
      window.open(`/api/study-resources/${resourceId}/download`, '_blank');
      
      console.log('下载已启动:', resourceId);
      
    } catch (error: unknown) {
      console.error('下载失败:', error);
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      alert(`下载失败: ${errorMessage}`);
    }
  };

  const formatFileSize = (sizeBytes: number) => {
    if (sizeBytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(sizeBytes) / Math.log(k));
    return parseFloat((sizeBytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  return (
    <div className="study-resources">
      {/* 页面头部 */}
      <div className="resources-header">
        <div className="header-content">
          <h1>
            <i className="fas fa-graduation-cap"></i>
            学习资源中心
          </h1>
          <p>海量优质学习资料，助力学业成功</p>
        </div>
        
        {/* 搜索栏 */}
        <div className="search-section">
          <div className="search-box">
            <i className="fas fa-search"></i>
            <input
              type="text"
              placeholder="搜索资源名称、关键词..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* 分类导航 */}
      <div className="category-navigation">
        <div className="category-tabs">
          <button
            className={`category-tab ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            <span className="tab-icon">📋</span>
            <span className="tab-text">全部资源</span>
            <span className="tab-count">{resources.length}</span>
          </button>
          
          {categories.map(category => (
            <button
              key={category.id}
              className={`category-tab ${selectedCategory === category.id ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category.id)}
            >
              <span className="tab-icon">{category.icon || '📁'}</span>
              <span className="tab-text">{category.name}</span>
              <span className="tab-count">{category.resource_count || 0}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 分类介绍卡片 */}
      {selectedCategory !== 'all' && (
        <div className="category-info">
          {categories
            .filter(cat => cat.id === selectedCategory)
            .map(category => (
              <div key={category.id} className="category-card">
                <div className="category-icon">{category.icon || '📁'}</div>
                <div className="category-details">
                  <h3>{category.name}</h3>
                  <p>{category.description}</p>
                  <div className="category-stats">
                    <span><i className="fas fa-file-alt"></i> {category.resource_count || 0} 个资源</span>
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}

      {/* 资源列表 */}
      <div className="resources-content">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>正在加载资源...</p>
          </div>
        ) : (
          <>
            <div className="resources-grid">
              {resources.map(resource => (
                <div key={resource.id} className="resource-card">
                  <div className="resource-header">
                    <div className="file-type-badge">{resource.file_type}</div>
                    <div className="resource-rating">
                      <StarRating
                        rating={resource.rating_avg || 0}
                        readonly={true}
                        size="small"
                        showCount={true}
                        ratingCount={resource.rating_count || 0}
                      />
                    </div>
                  </div>
                  
                  <div className="resource-content">
                    <h3 className="resource-title">{resource.title}</h3>
                    {resource.description && (
                      <p className="resource-description">{resource.description}</p>
                    )}
                    
                    <div className="resource-meta">
                      <div className="meta-item">
                        <i className="fas fa-hdd"></i>
                        <span>{formatFileSize(resource.file_size)}</span>
                      </div>
                      <div className="meta-item">
                        <i className="fas fa-calendar"></i>
                        <span>{formatDate(resource.upload_time)}</span>
                      </div>
                      <div className="meta-item">
                        <i className="fas fa-download"></i>
                        <span>{resource.download_count} 次下载</span>
                      </div>
                      <div className="meta-item">
                        <i className="fas fa-folder"></i>
                        <span>{resource.category_name}</span>
                      </div>
                    </div>
                    
                    {resource.tags && Array.isArray(resource.tags) && resource.tags.length > 0 && (
                      <div className="resource-tags">
                        {resource.tags.map((tag, index) => (
                          <span key={index} className="tag">{typeof tag === 'string' ? tag.trim() : tag}</span>
                        ))}
                      </div>
                    )}
                    {resource.tags && typeof resource.tags === 'string' && resource.tags.trim().length > 0 && (
                      <div className="resource-tags">
                        {resource.tags.split(',').map((tag, index) => (
                          <span key={index} className="tag">{tag.trim()}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="resource-actions">
                    <button 
                      className="download-btn"
                      onClick={() => handleDownload(resource.id)}
                    >
                      <i className="fas fa-download"></i>
                      立即下载
                    </button>
                    <button 
                      className="preview-btn"
                      onClick={() => setPreviewResource(resource)}
                    >
                      <i className="fas fa-eye"></i>
                      预览
                    </button>
                    <button 
                      className="rating-btn"
                      onClick={() => setRatingResource(resource)}
                    >
                      <i className="fas fa-star"></i>
                      评分
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* 分页控件 */}
            {totalPages > 1 && (
              <div className="pagination">
                <button 
                  className="page-btn"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                >
                  <i className="fas fa-chevron-left"></i>
                  上一页
                </button>
                
                <div className="page-info">
                  第 {currentPage} 页，共 {totalPages} 页
                </div>
                
                <button 
                  className="page-btn"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  下一页
                  <i className="fas fa-chevron-right"></i>
                </button>
              </div>
            )}

            {resources.length === 0 && !loading && (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <h3>暂无相关资源</h3>
                <p>试试搜索其他关键词或选择不同分类</p>
              </div>
            )}
          </>
        )}
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

      {/* 评分模态框 */}
      {ratingResource && (
        <RatingModal
          resourceId={ratingResource.id}
          resourceTitle={ratingResource.title}
          onClose={() => setRatingResource(null)}
          onRatingSubmit={handleRatingSubmit}
        />
      )}
    </div>
  );
};

export default StudyResources;
