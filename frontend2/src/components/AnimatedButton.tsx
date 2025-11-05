import React, { useState } from 'react';
import './AnimatedButton.css';

interface AnimatedButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'outline';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  // 允许外部传入内联样式，提升灵活性
  style?: React.CSSProperties;
}

/**
 * AnimatedButton 组件：
 * - 提供带动效的按钮；支持 variant/size/禁用/加载态等
 * - 新增 style 属性，允许传入内联样式
 */
const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  className = '',
  type = 'button',
  style
}) => {
  const [isClicked, setIsClicked] = useState(false);

  const handleClick = () => {
    if (disabled || loading) return;
    
    setIsClicked(true);
    setTimeout(() => setIsClicked(false), 200);
    
    if (onClick) {
      onClick();
    }
  };

  const buttonClass = [
    'animated-btn',
    `btn-${variant}`,
    `btn-${size}`,
    isClicked ? 'clicked' : '',
    loading ? 'loading' : '',
    disabled ? 'disabled' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      type={type}
      className={buttonClass}
      onClick={handleClick}
      disabled={disabled || loading}
      style={style}
    >
      <span className="btn-content">
        {loading && (
          <span className="btn-spinner">
            <span className="spinner-dot"></span>
            <span className="spinner-dot"></span>
            <span className="spinner-dot"></span>
          </span>
        )}
        {!loading && icon && <span className="btn-icon">{icon}</span>}
        <span className="btn-text">{children}</span>
      </span>
      <span className="btn-ripple"></span>
    </button>
  );
};

export default AnimatedButton;
