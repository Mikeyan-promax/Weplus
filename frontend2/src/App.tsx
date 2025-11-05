import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import PageHeader from './components/PageHeader';
import WelcomeScreen from './components/WelcomeScreen';
import RAGChat from './components/RAGChat';
import UserInfo from './components/UserInfo';
import CampusMap from './components/CampusMap';
import ChatUITest from './components/ChatUITest';
import Login from './components/Login';
import Register from './components/Register';
import AdminLogin from './components/AdminLogin';
import HelloPage from './components/HelloPage';
// import AdminLayout from './components/admin/AdminLayout';
import AdminDashboard from './components/AdminDashboard';
import UserManagement from './components/admin/UserManagement';
import DocumentManagement from './components/admin/DocumentManagement';
import VectorDatabaseManagement from './components/admin/VectorDatabaseManagement';
import BackupManagement from './components/admin/BackupManagement';
import StudyResourcesManagement from './components/admin/StudyResourcesManagement';
import AuthGuard from './components/AuthGuard';
import TestUserDataIsolation from './components/TestUserDataIsolation';
import MathTestPage from './components/MathTestPage';
import StudyResources from './components/StudyResources';
import ResourceDetail from './components/ResourceDetail';
import './App.css';
import './components/Auth.css';
import OtherTools from './components/OtherTools';

// 主应用组件（需要登录后才能访问）
const MainApp = () => (
  <div className="app">
    <Sidebar />
    <div className="main-content">
      <PageHeader />
      <Routes>
        <Route path="/" element={<WelcomeScreen />} />
        <Route path="/chat" element={<RAGChat />} />
        <Route path="/chat-test" element={<ChatUITest />} />
        <Route path="/profile" element={<UserInfo />} />
        <Route path="/map" element={<CampusMap />} />
        <Route path="/test-isolation" element={<TestUserDataIsolation />} />
        <Route path="/math-test" element={<MathTestPage />} />
        <Route path="/settings" element={<div className="page-placeholder">⚙️ 设置功能开发中...</div>} />
        <Route path="/dining" element={<div className="page-placeholder">🍽️ 食堂服务功能开发中...</div>} />
        <Route path="/study" element={<StudyResources />} />
        <Route path="/resource/:id" element={<ResourceDetail />} />
        <Route path="/life" element={<div className="page-placeholder">🏠 生活服务功能开发中...</div>} />
        <Route path="/other" element={<OtherTools />} />
      </Routes>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* 默认首页 - HelloPage欢迎页面 */}
          <Route path="/" element={<HelloPage />} />
          
          {/* 认证页面路由 - 不需要认证 */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* 管理员系统路由 */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<UserManagement />} />
          <Route path="/admin/documents" element={<DocumentManagement />} />
          <Route path="/admin/study-resources" element={<StudyResourcesManagement />} />
          <Route path="/admin/vector-database" element={<VectorDatabaseManagement />} />
          <Route path="/admin/backup" element={<BackupManagement />} />
          <Route path="/admin/*" element={<Navigate to="/admin/login" replace />} />
          
          {/* 主应用路由 - 需要认证，现在在/app路径下 */}
          <Route path="/app/*" element={
            <AuthGuard>
              <MainApp />
            </AuthGuard>
          } />
          
          {/* 兼容性路由：保留原有的HelloPage路径 */}
          <Route path="/HelloPage" element={<Navigate to="/" replace />} />
          
          {/* 404处理：未匹配的路由重定向到首页 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
