import React from 'react';
import StarRating from './StarRating';
import './RatingStats.css';

interface RatingData {
  average: number;
  total: number;
  distribution: {
    [key: number]: number;
  };
}

interface RatingStatsProps {
  rating: RatingData;
  showDistribution?: boolean;
  compact?: boolean;
}

const RatingStats: React.FC<RatingStatsProps> = ({
  rating,
  showDistribution = true,
  compact = false
}) => {
  const { average, total, distribution } = rating;

  const getPercentage = (count: number) => {
    return total > 0 ? (count / total) * 100 : 0;
  };

  if (compact) {
    return (
      <div className="rating-stats rating-stats--compact">
        <StarRating rating={average} readonly showValue />
        <span className="rating-stats__total">({total})</span>
      </div>
    );
  }

  return (
    <div className="rating-stats">
      <div className="rating-stats__summary">
        <div className="rating-stats__average">
          <span className="rating-stats__score">{average.toFixed(1)}</span>
          <StarRating rating={average} readonly size="large" />
          <span className="rating-stats__total">{total} 个评分</span>
        </div>
      </div>

      {showDistribution && total > 0 && (
        <div className="rating-stats__distribution">
          <h4 className="rating-stats__distribution-title">评分分布</h4>
          <div className="rating-stats__bars">
            {[5, 4, 3, 2, 1].map((star) => {
              const count = distribution[star] || 0;
              const percentage = getPercentage(count);
              
              return (
                <div key={star} className="rating-stats__bar-row">
                  <span className="rating-stats__star-label">{star} 星</span>
                  <div className="rating-stats__bar">
                    <div 
                      className="rating-stats__bar-fill"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="rating-stats__count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {total === 0 && (
        <div className="rating-stats__empty">
          <p>暂无评分</p>
        </div>
      )}
    </div>
  );
};

export default RatingStats;