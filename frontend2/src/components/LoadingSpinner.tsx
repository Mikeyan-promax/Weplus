import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  text?: string; // 保留接口兼容性，但不使用
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  color = '#667eea'
}) => {
  return (
    <div className={`loading-spinner ${size}`}>
      <div className="spinner" style={{ 
        '--primary-color': color,
        '--secondary-color': color === '#667eea' ? '#764ba2' : color 
      } as React.CSSProperties}>
        <div className="spinner-inner"></div>
      </div>
    </div>
  );
};

export default LoadingSpinner;