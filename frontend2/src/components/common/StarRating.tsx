import React, { useState } from 'react';
import './StarRating.css';

interface StarRatingProps {
  rating: number;
  onRatingChange?: (rating: number) => void;
  readonly?: boolean;
  size?: 'small' | 'medium' | 'large';
  showValue?: boolean;
}

const StarRating: React.FC<StarRatingProps> = ({
  rating,
  onRatingChange,
  readonly = false,
  size = 'medium',
  showValue = false
}) => {
  const [hoverRating, setHoverRating] = useState(0);

  const handleStarClick = (starRating: number) => {
    if (!readonly && onRatingChange) {
      onRatingChange(starRating);
    }
  };

  const handleStarHover = (starRating: number) => {
    if (!readonly) {
      setHoverRating(starRating);
    }
  };

  const handleMouseLeave = () => {
    if (!readonly) {
      setHoverRating(0);
    }
  };

  const displayRating = hoverRating || rating;

  return (
    <div className={`star-rating star-rating--${size}`}>
      <div className="star-rating__stars" onMouseLeave={handleMouseLeave}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`star-rating__star ${
              star <= displayRating ? 'star-rating__star--filled' : ''
            } ${readonly ? 'star-rating__star--readonly' : ''}`}
            onClick={() => handleStarClick(star)}
            onMouseEnter={() => handleStarHover(star)}
            disabled={readonly}
            aria-label={`${star} 星`}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M10 1.5L12.09 7.26L18 8.27L14 12.14L14.91 18.09L10 15.77L5.09 18.09L6 12.14L2 8.27L7.91 7.26L10 1.5Z" />
            </svg>
          </button>
        ))}
      </div>
      {showValue && (
        <span className="star-rating__value">
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  );
};

export default StarRating;