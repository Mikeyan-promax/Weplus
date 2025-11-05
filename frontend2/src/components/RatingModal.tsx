import React, { useState } from 'react';
import StarRating from './StarRating';
import './RatingModal.css';

interface RatingModalProps {
  resourceId: number;
  resourceTitle: string;
  onClose: () => void;
  onRatingSubmit: (rating: number, comment?: string) => Promise<void>;
}

const RatingModal: React.FC<RatingModalProps> = ({
  resourceId: _resourceId,
  resourceTitle,
  onClose,
  onRatingSubmit
}) => {
  const [rating, setRating] = useState<number>(0);
  const [comment, setComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (rating === 0) {
      alert('请选择评分');
      return;
    }

    setIsSubmitting(true);
    try {
      await onRatingSubmit(rating, comment.trim() || undefined);
      onClose();
    } catch (error) {
      console.error('提交评分失败:', error);
      alert('提交评分失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="rating-modal-overlay" onClick={handleOverlayClick}>
      <div className="rating-modal">
        <div className="rating-modal-header">
          <h3>为资源评分</h3>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div className="rating-modal-content">
          <div className="resource-info">
            <h4>{resourceTitle}</h4>
            <p>请为这个资源打分并留下您的评价</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="rating-section">
              <label>您的评分：</label>
              <StarRating
                rating={rating}
                onRatingChange={setRating}
                size="large"
              />
              {rating > 0 && (
                <span className="rating-text">
                  {rating === 1 && '很差'}
                  {rating === 2 && '较差'}
                  {rating === 3 && '一般'}
                  {rating === 4 && '良好'}
                  {rating === 5 && '优秀'}
                </span>
              )}
            </div>

            <div className="comment-section">
              <label htmlFor="comment">评价内容（可选）：</label>
              <textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="分享您对这个资源的看法..."
                maxLength={500}
                rows={4}
              />
              <div className="char-count">
                {comment.length}/500
              </div>
            </div>

            <div className="rating-modal-actions">
              <button
                type="button"
                className="cancel-btn"
                onClick={onClose}
                disabled={isSubmitting}
              >
                取消
              </button>
              <button
                type="submit"
                className="submit-btn"
                disabled={rating === 0 || isSubmitting}
              >
                {isSubmitting ? '提交中...' : '提交评分'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RatingModal;
