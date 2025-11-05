import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Breadcrumb.css';

interface BreadcrumbItem {
  path: string;
  label: string;
  icon?: string;
}

const Breadcrumb: React.FC = () => {
  const location = useLocation();

  // 定义路径映射
  const pathMap: Record<string, BreadcrumbItem> = {
    '/': { path: '/', label: '首页', icon: 'fas fa-home' },
    '/chat': { path: '/chat', label: 'AI助手', icon: 'fas fa-robot' },
    '/profile': { path: '/profile', label: '用户信息', icon: 'fas fa-user' },
    '/map': { path: '/map', label: '校园地图', icon: 'fas fa-map' },
    '/dining': { path: '/dining', label: '食堂服务', icon: 'fas fa-utensils' },
    '/study': { path: '/study', label: '学习资源', icon: 'fas fa-book' },
    '/life': { path: '/life', label: '生活服务', icon: 'fas fa-heart' },
    '/other': { path: '/other', label: '其他功能', icon: 'fas fa-ellipsis-h' }
  };

  // 生成面包屑路径
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const breadcrumbs: BreadcrumbItem[] = [];

    // 总是包含首页
    breadcrumbs.push(pathMap['/']);

    // 如果不是首页，添加当前页面
    if (location.pathname !== '/') {
      const currentPath = location.pathname;
      const currentItem = pathMap[currentPath];
      if (currentItem) {
        breadcrumbs.push(currentItem);
      }
    }

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  // 如果只有首页，不显示面包屑
  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav className="breadcrumb" aria-label="面包屑导航">
      <ol className="breadcrumb-list">
        {breadcrumbs.map((item, index) => (
          <li key={item.path} className="breadcrumb-item">
            {index < breadcrumbs.length - 1 ? (
              <>
                <Link to={item.path} className="breadcrumb-link">
                  {item.icon && <i className={item.icon}></i>}
                  <span>{item.label}</span>
                </Link>
                <span className="breadcrumb-separator">
                  <i className="fas fa-chevron-right"></i>
                </span>
              </>
            ) : (
              <span className="breadcrumb-current">
                {item.icon && <i className={item.icon}></i>}
                <span>{item.label}</span>
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default Breadcrumb;