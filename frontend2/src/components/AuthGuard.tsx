import React from 'react';
import { Navigate } from 'react-router-dom';
import { isAuthenticated } from '../utils/auth';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  if (!isAuthenticated()) {
    // 未登录用户重定向到HelloPage而不是login页面
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default AuthGuard;