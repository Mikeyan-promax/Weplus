import React from 'react';
import { useTheme } from './ThemeProvider';
import './ThemeToggle.css';

interface ThemeToggleProps {
  className?: string;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  className = '', 
  size = 'medium',
  showLabel = false 
}) => {
  const { theme, setTheme, isDark } = useTheme();

  const handleToggle = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('auto');
    } else {
      setTheme('light');
    }
  };

  const getIcon = () => {
    switch (theme) {
      case 'light':
        return '☀️';
      case 'dark':
        return '🌙';
      case 'auto':
        return '🌓';
      default:
        return '☀️';
    }
  };

  const getLabel = () => {
    switch (theme) {
      case 'light':
        return '浅色模式';
      case 'dark':
        return '深色模式';
      case 'auto':
        return '跟随系统';
      default:
        return '浅色模式';
    }
  };

  return (
    <button
      className={`theme-toggle theme-toggle-${size} ${isDark ? 'dark' : 'light'} ${className}`}
      onClick={handleToggle}
      title={`当前: ${getLabel()}, 点击切换`}
      aria-label={`切换主题，当前为${getLabel()}`}
    >
      <span className="theme-icon">{getIcon()}</span>
      {showLabel && <span className="theme-label">{getLabel()}</span>}
    </button>
  );
};

export default ThemeToggle;