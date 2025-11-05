"""
认证服务模块
提供JWT token生成、验证和用户认证功能
"""

import jwt
from jwt.exceptions import InvalidTokenError
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from passlib.context import CryptContext
import secrets

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """认证服务类"""
    
    def __init__(self):
        # 从环境变量获取JWT配置
        self.secret_key = os.getenv('JWT_SECRET_KEY', self._generate_secret_key())
        self.algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.access_token_expire_minutes = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        self.refresh_token_expire_days = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        
        # 为了向后兼容，添加类属性
        self.ACCESS_TOKEN_EXPIRE_MINUTES = self.access_token_expire_minutes
    
    def _generate_secret_key(self) -> str:
        """生成随机密钥"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 检查是否过期
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """从令牌中获取用户信息"""
        payload = self.verify_token(token)
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": int(user_id),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "is_verified": payload.get("is_verified", False)
        }
    
    def create_token_pair(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """创建访问令牌和刷新令牌对"""
        token_data = {
            "sub": str(user_data["id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "is_verified": user_data.get("is_verified", False)
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user_data["id"])})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def refresh_access_token(self, refresh_token: str, user_data: Dict[str, Any]) -> Dict[str, str]:
        """使用刷新令牌创建新的访问令牌"""
        # 验证刷新令牌
        payload = self.verify_token(refresh_token, "refresh")
        
        # 检查用户ID是否匹配
        if payload.get("sub") != str(user_data["id"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建新的访问令牌
        token_data = {
            "sub": str(user_data["id"]),
            "email": user_data["email"],
            "username": user_data["username"],
            "is_verified": user_data.get("is_verified", False)
        }
        
        access_token = self.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

# 全局认证服务实例
auth_service = AuthService()

# 用于依赖注入的函数
def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return auth_service