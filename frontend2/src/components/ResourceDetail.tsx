import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import StarRating from './common/StarRating';
import RatingStats from './common/RatingStats';
import CommentList from './common/CommentList';
import CommentForm from './common/CommentForm';
import ResourcePreview from './ResourcePreview';
import './ResourceDetail.css';

interface StudyResource {
  id: number;
  name: string;
  description: string;
  file_name: string;
  file_size: number;
  file_type: string;
  category_id: number;
  category_name: string;
  tags: string[] | string;
  download_count: number;
  rating_avg: number;
  upload_time: string;
  updated_at: string;
}

interface RatingData {
  average: number;
  total: number;
  distribution: {
    [key: number]: number;
  };
}

interface Comment {
  id: number;
  content: string;
  user_id: number;
  username?: string;
  avatar?: string;
  created_at: string;
  parent_id?: number;
  replies?: Comment[];
}

const ResourceDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [resource, setResource] = useState<StudyResource | null>(null);
  const [rating, setRating] = useState<RatingData>({
    average: 0,
    total: 0,
    distribution: {}
  });
  const [comments, setComments] = useState<Comment[]>([]);
  const [userRating, setUserRating] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const [commentsPage, setCommentsPage] = useState(1);
  const [hasMoreComments, setHasMoreComments] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);

  useEffect(() => {
    if (id) {
      fetchResourceDetail();
      fetchRatingStats();
      fetchComments();
    }
  }, [id]);

  const fetchResourceDetail = async () => {
    try {
      // 后端实际路由为 /api/study-resources/{resource_id}
      const response = await fetch(`/api/study-resources/${id}`);
      if (response.ok) {
        const data = await response.json();
        // 后端返回结构为 { success: true, data: <resource> }
        setResource(data.data);
      } else {
        console.error('获取资源详情失败');
      }
    } catch (error) {
      console.error('获取资源详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRatingStats = async () => {
    try {
      // 后端实际路由为 /api/study-resources/{resource_id}/ratings
      const response = await fetch(`/api/study-resources/${id}/ratings`);
      if (response.ok) {
        const data = await response.json();
        setRating(data.ratings);
      }
    } catch (error) {
      console.error('获取评分统计失败:', error);
    }
  };

  const fetchComments = async (page = 1, append = false) => {
    try {
      setLoadingComments(true);
      const response = await fetch(`/api/study-resources/resource/${id}/comments?page=${page}&limit=10`);
      if (response.ok) {
        const data = await response.json();
        if (append) {
          setComments(prev => [...prev, ...data.comments]);
        } else {
          setComments(data.comments);
        }
        setHasMoreComments(data.has_more);
        setCommentsPage(page);
      }
    } catch (error) {
      console.error('获取评论失败:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleRatingSubmit = async (newRating: number) => {
    try {
      const response = await fetch('/api/study-resources/ratings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resource_id: parseInt(id!),
          rating: newRating,
          user_id: 1 // 临时用户ID，实际应该从认证系统获取
        }),
      });

      if (response.ok) {
        setUserRating(newRating);
        fetchRatingStats(); // 重新获取评分统计
      } else {
        console.error('提交评分失败');
      }
    } catch (error) {
      console.error('提交评分失败:', error);
    }
  };

  const handleCommentSubmit = async (content: string) => {
    try {
      const response = await fetch('/api/study-resources/comments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resource_id: parseInt(id!),
          content,
          user_id: 1 // 临时用户ID，实际应该从认证系统获取
        }),
      });

      if (response.ok) {
        fetchComments(); // 重新获取评论列表
      } else {
        console.error('发布评论失败');
      }
    } catch (error) {
      console.error('发布评论失败:', error);
    }
  };

  const handleReply = async (parentId: number, content: string) => {
    try {
      const response = await fetch('/api/study-resources/comments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resource_id: parseInt(id!),
          content,
          parent_id: parentId,
          user_id: 1 // 临时用户ID，实际应该从认证系统获取
        }),
      });

      if (response.ok) {
        fetchComments(); // 重新获取评论列表
      } else {
        console.error('回复评论失败');
      }
    } catch (error) {
      console.error('回复评论失败:', error);
    }
  };

  /**
   * 资源下载：使用相对路径 `/api/study-resources/:id/download`，避免硬编码端口
   */
  const handleDownload = () => {
    try {
      // 使用window.open直接下载，这样会自动处理认证和文件名
      window.open(`/api/study-resources/${id}/download`, '_blank');
      console.log('下载已启动:', id);
    } catch (error) {
      console.error('下载失败:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-CN');
  };

  if (loading) {
    return (
      <div className="resource-detail">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (!resource) {
    return (
      <div className="resource-detail">
        <div className="error">资源不存在</div>
      </div>
    );
  }

  return (
    <div className="resource-detail">
      <div className="resource-detail__header">
        <button 
          className="btn btn--secondary btn--back"
          onClick={() => navigate(-1)}
        >
          ← 返回
        </button>
        <h1 className="resource-detail__title">{resource.name}</h1>
      </div>

      <div className="resource-detail__content">
        <div className="resource-detail__main">
          <div className="resource-detail__info">
            <div className="resource-info">
              <div className="resource-info__item">
                <span className="resource-info__label">文件名:</span>
                <span className="resource-info__value">{resource.file_name}</span>
              </div>
              <div className="resource-info__item">
                <span className="resource-info__label">文件大小:</span>
                <span className="resource-info__value">{formatFileSize(resource.file_size)}</span>
              </div>
              <div className="resource-info__item">
                <span className="resource-info__label">文件类型:</span>
                <span className="resource-info__value">{resource.file_type}</span>
              </div>
              <div className="resource-info__item">
                <span className="resource-info__label">分类:</span>
                <span className="resource-info__value">{resource.category_name}</span>
              </div>
              <div className="resource-info__item">
                <span className="resource-info__label">上传时间:</span>
                <span className="resource-info__value">{formatDate(resource.upload_time)}</span>
              </div>
              <div className="resource-info__item">
                <span className="resource-info__label">下载次数:</span>
                <span className="resource-info__value">{resource.download_count}</span>
              </div>
            </div>

            {resource.tags && (
              (Array.isArray(resource.tags) && resource.tags.length > 0) ||
              (typeof resource.tags === 'string' && resource.tags.trim().length > 0)
            ) && (
              <div className="resource-tags">
                <span className="resource-tags__label">标签:</span>
                <div className="resource-tags__list">
                  {Array.isArray(resource.tags) ? (
                    resource.tags.map((tag, index) => (
                      <span key={index} className="resource-tag">
                        {tag}
                      </span>
                    ))
                  ) : (
                    resource.tags.split(',').map((tag, index) => (
                      <span key={index} className="resource-tag">
                        {tag.trim()}
                      </span>
                    ))
                  )}
                </div>
              </div>
            )}

            {resource.description && (
              <div className="resource-description">
                <h3>资源描述</h3>
                <p>{resource.description}</p>
              </div>
            )}

            <div className="resource-actions">
              <button 
                className="btn btn--primary"
                onClick={handleDownload}
              >
                下载资源
              </button>
              <button 
                className="btn btn--secondary"
                onClick={() => setShowPreview(true)}
              >
                预览资源
              </button>
            </div>
          </div>

          <div className="resource-detail__rating">
            <h3>为这个资源评分</h3>
            <StarRating
              rating={userRating}
              onRatingChange={handleRatingSubmit}
              size="large"
            />
            {userRating > 0 && (
              <p className="rating-thanks">感谢您的评分！</p>
            )}
          </div>

          <div className="resource-detail__comments">
            <CommentForm
              resourceId={parseInt(id!)}
              onSubmit={handleCommentSubmit}
            />
            
            <CommentList
              resourceId={parseInt(id!)}
              comments={comments}
              onReply={handleReply}
              onLoadMore={() => fetchComments(commentsPage + 1, true)}
              hasMore={hasMoreComments}
              loading={loadingComments}
            />
          </div>
        </div>

        <div className="resource-detail__sidebar">
          <RatingStats rating={rating} />
        </div>
      </div>

      {showPreview && resource && (
        <ResourcePreview
          resourceId={resource.id}
          fileName={resource.file_name}
          fileType={resource.file_type}
          fileSize={resource.file_size}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
};

export default ResourceDetail;
