import React, { useState, useRef, useEffect } from 'react';
import AnimatedButton from './AnimatedButton';
import LoadingSpinner from './LoadingSpinner';
import { useAuth } from '../contexts/AuthContext';
import { getUserData, setUserData, USER_DATA_TYPES } from '../utils/userDataManager';
import './UserInfo.css';

// 注意：以下接口暂时未使用，但保留以备将来功能扩展
/* interface UserSettings {
  messageNotifications: boolean;
  activityReminders: boolean;
  emailNotifications: boolean;
  profileVisibility: boolean;
  dataSharing: boolean;
} */

interface UserProfile {
  name: string;
  major: string;
  grade: string;
  email: string;
  phone: string;
  avatar: string;
}

const UserInfo: React.FC = () => {
  const { user, logout } = useAuth();
  
  // 注意：以下函数暂时未使用，但保留以备将来功能扩展
  /* const loadUserSettings = (): UserSettings => {
    const defaultSettings: UserSettings = {
      messageNotifications: true,
      activityReminders: true,
      emailNotifications: false,
      profileVisibility: true,
      dataSharing: true
    };

    if (!user) return defaultSettings;
    
    try {
      const savedSettings = getUserData(USER_DATA_TYPES.NOTIFICATION_SETTINGS);
      if (savedSettings) {
        // 确保返回的设置包含所有必需的属性
        return {
          ...defaultSettings,
          ...savedSettings
        };
      }
    } catch (error) {
      console.warn('加载用户设置失败:', error);
    }
    
    return defaultSettings;
  }; */

  // 注意：以下函数和状态暂时未使用，但保留以备将来功能扩展
  /* const saveUserSettings = (settings: UserSettings) => {
    if (!user) return;
    
    try {
      setUserData(USER_DATA_TYPES.NOTIFICATION_SETTINGS, settings);
    } catch (error) {
      console.warn('保存用户设置失败:', error);
    }
  }; */

  // const [userSettings, setUserSettings] = useState<UserSettings>(loadUserSettings);
  
  const [userProfile, setUserProfile] = useState<UserProfile>({
    name: '待填写',
    major: '待填写',
    grade: '待填写',
    email: '待填写',
    phone: '待填写',
    avatar: ''
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState(userProfile);
  const [isLoading, setIsLoading] = useState(false);
  // 当前只有profile选项卡，不需要activeTab状态
  // const [activeTab, setActiveTab] = useState<'profile'>('profile');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 获取用户信息
  useEffect(() => {
    if (user) {
      // 尝试从本地存储获取用户数据
      try {
        const savedProfile = getUserData<UserProfile>(USER_DATA_TYPES.USER_PROFILE, null);
        if (savedProfile) {
          // 合并保存的数据，但确保邮箱始终使用登录邮箱
          setUserProfile({
            ...savedProfile,
            email: user.email || '未设置', // 邮箱始终使用登录邮箱
          });
          return;
        }
      } catch (error) {
        console.warn('加载用户个人资料失败:', error);
      }
      
      // 如果没有保存的数据，使用默认值
      setUserProfile({
        name: user.username || '待填写',
        major: '待填写',
        grade: '待填写',
        email: user.email || '未设置', // 邮箱始终使用登录邮箱
        phone: '待填写',
        avatar: ''
      });
    }
  }, [user]);

  // 处理注销
  const handleLogout = () => {
    if (window.confirm('确定要注销账户吗？注销后将返回登录页面。')) {
      logout();
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setEditForm(userProfile);
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      // 保存到本地存储
      setUserData(USER_DATA_TYPES.USER_PROFILE, {
        ...editForm,
        email: user?.email || editForm.email // 确保邮箱不被修改
      });
      
      // 更新状态
      setUserProfile({
        ...editForm,
        email: user?.email || editForm.email // 确保邮箱不被修改
      });
      setIsEditing(false);
    } catch (error) {
      console.error('保存失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setEditForm(userProfile);
    setIsEditing(false);
  };

  const handleInputChange = (field: keyof UserProfile, value: string) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        setEditForm(prev => ({
          ...prev,
          avatar: result
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const renderProfileTab = () => (
    <div className="profile-content">
      <div className="profile-header">
        <div className="avatar-section">
          <div className="avatar-container">
            {editForm.avatar ? (
              <img src={editForm.avatar} alt="用户头像" className="avatar-image" />
            ) : (
              <div className="avatar-placeholder">
                <span className="avatar-icon">👤</span>
              </div>
            )}
            {isEditing && (
              <button className="avatar-edit-btn" onClick={triggerFileInput}>
                📷
              </button>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleAvatarUpload}
            style={{ display: 'none' }}
          />
        </div>
        
        <div className="profile-info">
          <h2 className="user-name">{userProfile.name}</h2>
        </div>
        
        {/* 右上角注销按钮 */}
        <div className="logout-button-container">
          <AnimatedButton 
            variant="danger" 
            size="medium" 
            onClick={handleLogout} 
            className="logout-btn-corner"
          >
            注销账户
          </AnimatedButton>
        </div>
      </div>

      <div className="profile-form">
        <div className="form-section">
          <h3>个人信息</h3>
          <div className="form-grid">
            <div className="form-group">
              <label>姓名</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="form-input"
                />
              ) : (
                <span className="form-value">{userProfile.name}</span>
              )}
            </div>

            <div className="form-group">
              <label>专业</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editForm.major}
                  onChange={(e) => handleInputChange('major', e.target.value)}
                  className="form-input"
                />
              ) : (
                <span className="form-value">{userProfile.major}</span>
              )}
            </div>

            <div className="form-group">
              <label>年级</label>
              {isEditing ? (
                <select
                  value={editForm.grade}
                  onChange={(e) => handleInputChange('grade', e.target.value)}
                  className="form-input"
                >
                  <option value="2020级">2020级</option>
                  <option value="2021级">2021级</option>
                  <option value="2022级">2022级</option>
                  <option value="2023级">2023级</option>
                  <option value="2024级">2024级</option>
                  <option value="2025级">2025级</option>
                </select>
              ) : (
                <span className="form-value">{userProfile.grade}</span>
              )}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>联系方式</h3>
          <div className="form-grid">
            <div className="form-group">
              <label>邮箱 (不可修改)</label>
              <span className="form-value readonly">{userProfile.email}</span>
            </div>

            <div className="form-group">
              <label>手机号</label>
              {isEditing ? (
                <input
                  type="tel"
                  value={editForm.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="form-input"
                />
              ) : (
                <span className="form-value">{userProfile.phone}</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="user-info-container">
      <div className="tabs">
        <button
          className="tab-btn active"
          // 由于activeTab已被注释，这里不需要点击事件
          // onClick={() => setActiveTab('profile')}
        >
          个人资料
        </button>
      </div>

      <div className="tab-content">
        {renderProfileTab()}
      </div>

      <div className="action-buttons">
        {!isEditing && (
          <AnimatedButton onClick={handleEdit} className="edit-btn">
            编辑资料
          </AnimatedButton>
        )}
        
        {isEditing && (
          <>
            <AnimatedButton onClick={handleCancel} className="cancel-btn">
              取消
            </AnimatedButton>
            <AnimatedButton onClick={handleSave} className="save-btn" disabled={isLoading}>
              {isLoading ? <LoadingSpinner size="medium" /> : '保存'}
            </AnimatedButton>
          </>
        )}
      </div>
    </div>
  );
};

export default UserInfo;