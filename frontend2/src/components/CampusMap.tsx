import React, { useState, useRef } from 'react';
import AnimatedButton from './AnimatedButton';
import './CampusMap.css';

interface MapLocation {
  id: string;
  name: string;
  category: string;
  description: string;
  coordinates: { x: number; y: number };
  icon: string;
  floor?: string;
  openHours?: string;
  contact?: string;
  facilities?: string[];
}

interface RouteStep {
  instruction: string;
  distance: string;
  duration: string;
}

const CampusMap: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedLocation, setSelectedLocation] = useState<MapLocation | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isRouting, setIsRouting] = useState(false);
  const [routeStart, setRouteStart] = useState<MapLocation | null>(null);
  const [routeEnd, setRouteEnd] = useState<MapLocation | null>(null);
  const [routeSteps, setRouteSteps] = useState<RouteStep[]>([]);
  const [mapZoom, setMapZoom] = useState(1);
  const [mapPosition, setMapPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const mapRef = useRef<HTMLDivElement>(null);

  const categories = [
    { id: 'all', name: '全部', icon: 'fas fa-th', color: '#6c757d' },
    { id: 'academic', name: '教学楼', icon: 'fas fa-graduation-cap', color: '#007bff' },
    { id: 'dormitory', name: '宿舍楼', icon: 'fas fa-bed', color: '#28a745' },
    { id: 'dining', name: '餐厅', icon: 'fas fa-utensils', color: '#fd7e14' },
    { id: 'library', name: '图书馆', icon: 'fas fa-book', color: '#6f42c1' },
    { id: 'sports', name: '体育设施', icon: 'fas fa-dumbbell', color: '#e83e8c' },
    { id: 'service', name: '服务设施', icon: 'fas fa-concierge-bell', color: '#20c997' },
    { id: 'medical', name: '医疗服务', icon: 'fas fa-hospital', color: '#dc3545' }
  ];

  const locations: MapLocation[] = [
    {
      id: '1',
      name: '第一教学楼',
      category: 'academic',
      description: '主要承担基础课程教学，设有多媒体教室和实验室',
      coordinates: { x: 25, y: 35 },
      icon: 'fas fa-graduation-cap',
      floor: '1-6层',
      openHours: '6:00-22:00',
      facilities: ['多媒体教室', '计算机实验室', '语音室', '自习室']
    },
    {
      id: '2',
      name: '第二教学楼',
      category: 'academic',
      description: '理工科专业教学楼，配备先进的实验设备',
      coordinates: { x: 35, y: 25 },
      icon: 'fas fa-graduation-cap',
      floor: '1-8层',
      openHours: '6:00-22:00',
      facilities: ['物理实验室', '化学实验室', '工程实验室', '阶梯教室']
    },
    {
      id: '3',
      name: '图书馆',
      category: 'library',
      description: '藏书丰富，提供安静的学习环境和电子资源',
      coordinates: { x: 50, y: 30 },
      icon: 'fas fa-book',
      floor: '1-7层',
      openHours: '6:00-23:00',
      contact: '0532-66782000',
      facilities: ['阅览室', '电子阅览室', '研讨室', '自习室', '咖啡厅']
    },
    {
      id: '4',
      name: '第一食堂',
      category: 'dining',
      description: '提供丰富的餐饮选择，价格实惠',
      coordinates: { x: 70, y: 50 },
      icon: 'fas fa-utensils',
      floor: '1-3层',
      openHours: '6:30-21:30',
      facilities: ['中式快餐', '西式简餐', '特色小吃', '清真餐厅']
    },
    {
      id: '5',
      name: '第二食堂',
      category: 'dining',
      description: '新建食堂，环境优雅，菜品丰富',
      coordinates: { x: 20, y: 70 },
      icon: 'fas fa-utensils',
      floor: '1-2层',
      openHours: '6:30-21:30',
      facilities: ['自助餐厅', '火锅', '烧烤', '甜品店']
    },
    {
      id: '6',
      name: '海韵园宿舍区',
      category: 'dormitory',
      description: '学生宿舍区，环境优美，设施完善',
      coordinates: { x: 15, y: 15 },
      icon: 'fas fa-bed',
      floor: '1-6层',
      openHours: '24小时',
      facilities: ['4人间', '6人间', '洗衣房', '开水房', '活动室']
    },
    {
      id: '7',
      name: '浮山园宿舍区',
      category: 'dormitory',
      description: '研究生宿舍区，独立卫浴，网络覆盖',
      coordinates: { x: 80, y: 20 },
      icon: 'fas fa-bed',
      floor: '1-8层',
      openHours: '24小时',
      facilities: ['2人间', '单人间', '独立卫浴', '空调', '网络']
    },
    {
      id: '8',
      name: '体育馆',
      category: 'sports',
      description: '综合性体育场馆，可举办各类体育赛事',
      coordinates: { x: 60, y: 70 },
      icon: 'fas fa-dumbbell',
      floor: '1-3层',
      openHours: '6:00-22:00',
      facilities: ['篮球场', '羽毛球球场', '乒乓球室', '健身房', '游泳池']
    },
    {
      id: '9',
      name: '田径场',
      category: 'sports',
      description: '标准400米跑道，足球场，晨练好去处',
      coordinates: { x: 45, y: 80 },
      icon: 'fas fa-running',
      openHours: '5:30-22:00',
      facilities: ['400米跑道', '足球场', '看台', '器材室']
    },
    {
      id: '10',
      name: '校医院',
      category: 'medical',
      description: '为师生提供基本医疗服务和健康咨询',
      coordinates: { x: 30, y: 60 },
      icon: 'fas fa-hospital',
      floor: '1-2层',
      openHours: '8:00-17:30',
      contact: '0532-66782120',
      facilities: ['内科', '外科', '药房', '体检中心']
    },
    {
      id: '11',
      name: '学生服务中心',
      category: 'service',
      description: '一站式学生事务办理中心',
      coordinates: { x: 55, y: 45 },
      icon: 'fas fa-concierge-bell',
      floor: '1-3层',
      openHours: '8:00-17:30',
      facilities: ['教务处', '学工处', '财务处', '就业指导中心']
    },
    {
      id: '12',
      name: '银行ATM',
      category: 'service',
      description: '多家银行ATM机，方便师生取款',
      coordinates: { x: 65, y: 35 },
      icon: 'fas fa-credit-card',
      openHours: '24小时',
      facilities: ['工商银行', '建设银行', '农业银行', '中国银行']
    }
  ];

  // 过滤位置
  const filteredLocations = locations.filter(location => {
    const matchesCategory = selectedCategory === 'all' || location.category === selectedCategory;
    const matchesSearch = location.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         location.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // 处理地图拖拽
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - mapPosition.x,
      y: e.clientY - mapPosition.y
    });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    
    setMapPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // 地图缩放
  const handleZoomIn = () => {
    setMapZoom(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setMapZoom(prev => Math.max(prev - 0.2, 0.5));
  };

  const resetMapView = () => {
    setMapZoom(1);
    setMapPosition({ x: 0, y: 0 });
  };

  // 位置点击处理
  const handleLocationClick = (location: MapLocation) => {
    setSelectedLocation(location);
    if (isRouting) {
      if (!routeStart) {
        setRouteStart(location);
      } else if (!routeEnd && location.id !== routeStart.id) {
        setRouteEnd(location);
        generateRoute(routeStart, location);
      }
    }
  };

  // 生成路线
  const generateRoute = async (start: MapLocation, end: MapLocation) => {
    // 模拟路线规划
    const steps: RouteStep[] = [
      {
        instruction: `从${start.name}出发`,
        distance: '0米',
        duration: '0分钟'
      },
      {
        instruction: '向东步行至主干道',
        distance: '50米',
        duration: '1分钟'
      },
      {
        instruction: '沿主干道向南步行',
        distance: '200米',
        duration: '3分钟'
      },
      {
        instruction: `到达${end.name}`,
        distance: '250米',
        duration: '4分钟'
      }
    ];
    
    setRouteSteps(steps);
  };

  // 开始路线规划
  const startRouting = () => {
    setIsRouting(true);
    setRouteStart(null);
    setRouteEnd(null);
    setRouteSteps([]);
    setSelectedLocation(null);
  };

  // 取消路线规划
  const cancelRouting = () => {
    setIsRouting(false);
    setRouteStart(null);
    setRouteEnd(null);
    setRouteSteps([]);
  };

  // 搜索位置
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      const foundLocation = locations.find(loc => 
        loc.name.toLowerCase().includes(query.toLowerCase())
      );
      if (foundLocation) {
        setSelectedLocation(foundLocation);
        // 将地图中心移动到找到的位置
        const mapRect = mapRef.current?.getBoundingClientRect();
        if (mapRect) {
          const centerX = mapRect.width / 2;
          const centerY = mapRect.height / 2;
          const locationX = (foundLocation.coordinates.x / 100) * mapRect.width;
          const locationY = (foundLocation.coordinates.y / 100) * mapRect.height;
          
          setMapPosition({
            x: centerX - locationX,
            y: centerY - locationY
          });
        }
      }
    }
  };

  return (
    <div className="campus-map">
      {/* 地图头部 */}
      <div className="map-header">
        <div className="map-title">
          <h1>
            <i className="fas fa-map-marked-alt"></i>
            校园地图
          </h1>
          <p>探索校园，发现精彩</p>
        </div>
        
        <div className="map-actions">
          {!isRouting ? (
            <AnimatedButton 
              onClick={startRouting}
              variant="primary"
              size="medium"
              icon="fas fa-route"
            >
              路线规划
            </AnimatedButton>
          ) : (
            <div className="routing-actions">
              <AnimatedButton 
                onClick={cancelRouting}
                variant="outline"
                size="medium"
              >
                取消规划
              </AnimatedButton>
              {routeStart && routeEnd && (
                <span className="route-info">
                  {routeStart.name} → {routeEnd.name}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="map-container">
        {/* 侧边栏 */}
        <div className="map-sidebar">
          {/* 搜索框 */}
          <div className="search-section">
            <div className="search-box">
              <i className="fas fa-search"></i>
              <input
                type="text"
                placeholder="搜索地点..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
              />
              {searchQuery && (
                <button 
                  className="clear-search"
                  onClick={() => handleSearch('')}
                >
                  <i className="fas fa-times"></i>
                </button>
              )}
            </div>
          </div>

          {/* 分类筛选 */}
          <div className="category-section">
            <h3>地点分类</h3>
            <div className="category-list">
              {categories.map(category => (
                <button
                  key={category.id}
                  className={`category-btn ${selectedCategory === category.id ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(category.id)}
                  style={{ '--category-color': category.color } as React.CSSProperties}
                >
                  <i className={category.icon}></i>
                  <span>{category.name}</span>
                  <span className="count">
                    {category.id === 'all' 
                      ? locations.length 
                      : locations.filter(loc => loc.category === category.id).length
                    }
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* 位置列表 */}
          <div className="location-section">
            <h3>地点列表</h3>
            <div className="location-list">
              {filteredLocations.map(location => (
                <div
                  key={location.id}
                  className={`location-item ${selectedLocation?.id === location.id ? 'selected' : ''}`}
                  onClick={() => handleLocationClick(location)}
                >
                  <div className="location-icon">
                    <i className={location.icon}></i>
                  </div>
                  <div className="location-info">
                    <h4>{location.name}</h4>
                    <p>{location.description}</p>
                    {location.openHours && (
                      <span className="open-hours">
                        <i className="fas fa-clock"></i>
                        {location.openHours}
                      </span>
                    )}
                  </div>
                  {isRouting && (
                    <div className="routing-indicators">
                      {routeStart?.id === location.id && (
                        <span className="route-marker start">起点</span>
                      )}
                      {routeEnd?.id === location.id && (
                        <span className="route-marker end">终点</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 路线步骤 */}
          {routeSteps.length > 0 && (
            <div className="route-section">
              <h3>路线指引</h3>
              <div className="route-steps">
                {routeSteps.map((step, index) => (
                  <div key={index} className="route-step">
                    <div className="step-number">{index + 1}</div>
                    <div className="step-info">
                      <p>{step.instruction}</p>
                      <span className="step-details">
                        {step.distance} · {step.duration}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 地图主体 */}
        <div className="map-main">
          {/* 地图控制按钮 */}
          <div className="map-controls">
            <button className="control-btn" onClick={handleZoomIn}>
              <i className="fas fa-plus"></i>
            </button>
            <button className="control-btn" onClick={handleZoomOut}>
              <i className="fas fa-minus"></i>
            </button>
            <button className="control-btn" onClick={resetMapView}>
              <i className="fas fa-expand-arrows-alt"></i>
            </button>
          </div>

          {/* 地图画布 */}
          <div 
            ref={mapRef}
            className="map-canvas"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{
              transform: `translate(${mapPosition.x}px, ${mapPosition.y}px) scale(${mapZoom})`,
              cursor: isDragging ? 'grabbing' : 'grab'
            }}
          >
            {/* 校园背景 */}
            <div className="campus-background">
              <div className="campus-boundary"></div>
              <div className="campus-roads"></div>
              <div className="campus-green-areas"></div>
            </div>

            {/* 位置标记 */}
            {filteredLocations.map(location => (
              <div
                key={location.id}
                className={`location-marker ${selectedLocation?.id === location.id ? 'selected' : ''} ${
                  routeStart?.id === location.id ? 'route-start' : ''
                } ${routeEnd?.id === location.id ? 'route-end' : ''}`}
                style={{
                  left: `${location.coordinates.x}%`,
                  top: `${location.coordinates.y}%`,
                  '--marker-color': categories.find(cat => cat.id === location.category)?.color || '#6c757d'
                } as React.CSSProperties}
                onClick={() => handleLocationClick(location)}
              >
                <div className="marker-icon">
                  <i className={location.icon}></i>
                </div>
                <div className="marker-label">{location.name}</div>
              </div>
            ))}

            {/* 路线线条 */}
            {routeStart && routeEnd && (
              <svg className="route-line">
                <line
                  x1={`${routeStart.coordinates.x}%`}
                  y1={`${routeStart.coordinates.y}%`}
                  x2={`${routeEnd.coordinates.x}%`}
                  y2={`${routeEnd.coordinates.y}%`}
                  stroke="var(--primary-color)"
                  strokeWidth="3"
                  strokeDasharray="10,5"
                />
              </svg>
            )}
          </div>

          {/* 位置详情弹窗 */}
          {selectedLocation && !isRouting && (
            <div className="location-popup">
              <div className="popup-header">
                <h3>
                  <i className={selectedLocation.icon}></i>
                  {selectedLocation.name}
                </h3>
                <button 
                  className="close-popup"
                  onClick={() => setSelectedLocation(null)}
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
              
              <div className="popup-content">
                <p className="location-description">
                  {selectedLocation.description}
                </p>
                
                <div className="location-details">
                  {selectedLocation.floor && (
                    <div className="detail-item">
                      <i className="fas fa-building"></i>
                      <span>楼层：{selectedLocation.floor}</span>
                    </div>
                  )}
                  
                  {selectedLocation.openHours && (
                    <div className="detail-item">
                      <i className="fas fa-clock"></i>
                      <span>开放时间：{selectedLocation.openHours}</span>
                    </div>
                  )}
                  
                  {selectedLocation.contact && (
                    <div className="detail-item">
                      <i className="fas fa-phone"></i>
                      <span>联系电话：{selectedLocation.contact}</span>
                    </div>
                  )}
                </div>

                {selectedLocation.facilities && selectedLocation.facilities.length > 0 && (
                  <div className="facilities-section">
                    <h4>设施服务</h4>
                    <div className="facilities-list">
                      {selectedLocation.facilities.map((facility, index) => (
                        <span key={index} className="facility-tag">
                          {facility}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="popup-actions">
                  <AnimatedButton
                    variant="primary"
                    size="small"
                    onClick={() => {
                      setRouteEnd(selectedLocation);
                      startRouting();
                    }}
                  >
                    <i className="fas fa-route"></i>
                    导航到这里
                  </AnimatedButton>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CampusMap;