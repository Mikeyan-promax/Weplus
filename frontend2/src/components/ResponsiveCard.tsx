import React from 'react';
import './ResponsiveCard.css';

interface ResponsiveCardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  icon?: string;
  onClick?: () => void;
  hoverable?: boolean;
  loading?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'gradient' | 'glass' | 'minimal';
}

const ResponsiveCard: React.FC<ResponsiveCardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  icon,
  onClick,
  hoverable = true,
  loading = false,
  size = 'medium',
  variant = 'default'
}) => {
  const cardClasses = [
    'responsive-card',
    `card-${size}`,
    `card-${variant}`,
    hoverable ? 'hoverable' : '',
    onClick ? 'clickable' : '',
    loading ? 'loading' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClasses} onClick={onClick}>
      {loading && (
        <div className="card-loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
      
      {(title || subtitle || icon) && (
        <div className="card-header">
          {icon && <span className="card-icon">{icon}</span>}
          <div className="card-header-text">
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
        </div>
      )}
      
      <div className="card-content">
        {children}
      </div>
    </div>
  );
};

export default ResponsiveCard;