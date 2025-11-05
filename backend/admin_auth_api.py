"""
管理员认证API模块
提供管理员登录认证相关的API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
import jwt

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/auth", tags=["管理员认证"])

# JWT配置
SECRET_KEY = "weplus_admin_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 数据模型
class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    data: dict = None
    message: str = ""

# 模拟管理员数据
ADMIN_USERS = {
    "admin@weplus.com": {
        "email": "admin@weplus.com",
        "username": "admin",
        "password": "admin123",  # 实际应用中应该使用哈希密码
        "role": "super_admin",
        "permissions": ["user_management", "document_management", "backup_management"]
    },
    "manager@weplus.com": {
        "email": "manager@weplus.com",
        "username": "manager",
        "password": "manager123",
        "role": "manager",
        "permissions": ["user_management", "document_management"]
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(login_data: AdminLoginRequest):
    """管理员登录"""
    try:
        email = login_data.email
        password = login_data.password
        
        # 验证邮箱和密码
        if email not in ADMIN_USERS:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        admin_user = ADMIN_USERS[email]
        if admin_user["password"] != password:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin_user["username"], "role": admin_user["role"], "email": email},
            expires_delta=access_token_expires
        )
        
        return AdminLoginResponse(
            success=True,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "email": email,
                    "username": admin_user["username"],
                    "role": admin_user["role"],
                    "permissions": admin_user["permissions"]
                }
            },
            message="登录成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员登录失败: {e}")
        raise HTTPException(status_code=500, detail="登录失败")

@router.post("/logout")
async def admin_logout():
    """管理员登出"""
    try:
        return AdminLoginResponse(
            success=True,
            message="登出成功"
        )
    except Exception as e:
        logger.error(f"管理员登出失败: {e}")
        raise HTTPException(status_code=500, detail="登出失败")

@router.get("/verify")
async def verify_token():
    """验证令牌"""
    try:
        # 这里应该验证JWT令牌
        # 为了简化，直接返回成功
        return AdminLoginResponse(
            success=True,
            message="令牌有效"
        )
    except Exception as e:
        logger.error(f"令牌验证失败: {e}")
        raise HTTPException(status_code=401, detail="令牌无效")