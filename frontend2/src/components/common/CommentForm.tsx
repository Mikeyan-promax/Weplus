import React, { useState } from 'react';
import './CommentForm.css';

interface CommentFormProps {
  resourceId: number;
  onSubmit: (content: string) => Promise<void>;
  placeholder?: string;
  buttonText?: string;
  loading?: boolean;
}

const CommentForm: React.FC<CommentFormProps> = ({
  resourceId,
  onSubmit,
  placeholder = "写下你的评论...",
  buttonText = "发布评论",
  loading = false
}) => {
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim() || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(content.trim());
      setContent('');
    } catch (error) {
      console.error('发布评论失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit(e);
    }
  };

  return (
    <form className="comment-form" onSubmit={handleSubmit}>
      <div className="comment-form__content">
        <textarea
          className="comment-form__textarea"
          placeholder={placeholder}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={4}
          maxLength={1000}
          disabled={isSubmitting || loading}
        />
        
        <div className="comment-form__footer">
          <div className="comment-form__info">
            <span className="comment-form__char-count">
              {content.length}/1000
            </span>
            <span className="comment-form__shortcut">
              Ctrl+Enter 快速发布
            </span>
          </div>
          
          <div className="comment-form__actions">
            <button
              type="button"
              className="btn btn--secondary"
              onClick={() => setContent('')}
              disabled={!content || isSubmitting || loading}
            >
              清空
            </button>
            <button
              type="submit"
              className="btn btn--primary"
              disabled={!content.trim() || isSubmitting || loading}
            >
              {isSubmitting ? '发布中...' : buttonText}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};

export default CommentForm;