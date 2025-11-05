import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import './CommentList.css';

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

interface CommentListProps {
  resourceId: number;
  comments: Comment[];
  onReply?: (parentId: number, content: string) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  loading?: boolean;
}

/**
 * 评论列表组件：
 * - 展示评论与回复；支持加载更多与提交回复
 * - resourceId 当前未直接使用，预留给后续筛选/加载
 */
const CommentList: React.FC<CommentListProps> = ({
  resourceId: _resourceId,
  comments,
  onReply,
  onLoadMore,
  hasMore = false,
  loading = false
}) => {
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyContent, setReplyContent] = useState('');

  const handleReplySubmit = (parentId: number) => {
    if (replyContent.trim() && onReply) {
      onReply(parentId, replyContent.trim());
      setReplyContent('');
      setReplyingTo(null);
    }
  };

  const formatTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { 
        addSuffix: true, 
        locale: zhCN 
      });
    } catch (error) {
      return '刚刚';
    }
  };

  const renderComment = (comment: Comment, isReply = false) => (
    <div key={comment.id} className={`comment ${isReply ? 'comment--reply' : ''}`}>
      <div className="comment__avatar">
        {comment.avatar ? (
          <img src={comment.avatar} alt={comment.username} />
        ) : (
          <div className="comment__avatar-placeholder">
            {comment.username?.charAt(0) || 'U'}
          </div>
        )}
      </div>
      
      <div className="comment__content">
        <div className="comment__header">
          <span className="comment__username">
            {comment.username || `用户${comment.user_id}`}
          </span>
          <span className="comment__time">
            {formatTime(comment.created_at)}
          </span>
        </div>
        
        <div className="comment__text">
          {comment.content}
        </div>
        
        {!isReply && (
          <div className="comment__actions">
            <button
              className="comment__reply-btn"
              onClick={() => setReplyingTo(comment.id)}
            >
              回复
            </button>
          </div>
        )}
        
        {replyingTo === comment.id && (
          <div className="comment__reply-form">
            <textarea
              className="comment__reply-input"
              placeholder="写下你的回复..."
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              rows={3}
            />
            <div className="comment__reply-actions">
              <button
                className="btn btn--secondary btn--small"
                onClick={() => {
                  setReplyingTo(null);
                  setReplyContent('');
                }}
              >
                取消
              </button>
              <button
                className="btn btn--primary btn--small"
                onClick={() => handleReplySubmit(comment.id)}
                disabled={!replyContent.trim()}
              >
                发布回复
              </button>
            </div>
          </div>
        )}
        
        {comment.replies && comment.replies.length > 0 && (
          <div className="comment__replies">
            {comment.replies.map(reply => renderComment(reply, true))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="comment-list">
      <div className="comment-list__header">
        <h3>评论 ({comments.length})</h3>
      </div>
      
      <div className="comment-list__content">
        {comments.length === 0 ? (
          <div className="comment-list__empty">
            <p>暂无评论，快来发表第一条评论吧！</p>
          </div>
        ) : (
          <>
            {comments.map(comment => renderComment(comment))}
            
            {hasMore && (
              <div className="comment-list__load-more">
                <button
                  className="btn btn--secondary"
                  onClick={onLoadMore}
                  disabled={loading}
                >
                  {loading ? '加载中...' : '加载更多评论'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CommentList;
