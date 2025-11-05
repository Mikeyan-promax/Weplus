"""
WePlus 后台管理系统 - 用户管理API
提供用户注册、登录、信息管理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import bcrypt
import logging

# 导入数据库配置
from database.admin_models import AdminUser, UserRole
from database.models import User  # 导入正确的User模型
from database.config import get_db_connection

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])

# JWT配置
JWT_SECRET_KEY = "weplus_admin_secret_key_2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# HTTP Bearer认证
security = HTTPBearer()

# Pydantic模型定义
class UserRegistrationRequest(BaseModel):
    """用户注册请求模型"""
    email: EmailStr
    username: str
    password: str
    real_name: Optional[str] = ""
    phone: Optional[str] = ""
    department: Optional[str] = ""
    student_id: Optional[str] = ""
    role: Optional[str] = "user"
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v

class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str  # 可以是用户名或邮箱
    password: str

class UserUpdateRequest(BaseModel):
    """用户信息更新请求模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    student_id: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('新密码长度至少6个字符')
        if len(v) > 128:
            raise ValueError('新密码长度不能超过128个字符')
        return v

class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    login_count: int = 0
    profile: Dict[str, Any] = {}

class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PaginatedUsersResponse(BaseModel):
    """分页用户列表响应模型"""
    success: bool = True
    data: Dict[str, Any]
    message: str = "获取用户列表成功"

# 工具函数
def create_access_token(user_data: Dict[str, Any]) -> str:
    """创建JWT访问令牌"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": expire
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """获取当前用户信息"""
    return token_data

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """要求管理员权限"""
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

# 数据库操作函数
def create_user_in_db(user_data: UserRegistrationRequest) -> AdminUser:
    """在数据库中创建用户"""
    try:
        # 检查用户名和邮箱是否已存在
        existing_user = AdminUser.get_by_username_or_email(user_data.username, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在"
            )
        
        # 创建用户
        user = AdminUser.create(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            real_name=user_data.real_name,
            phone=user_data.phone,
            department=user_data.department,
            student_id=user_data.student_id,
            role=UserRole(user_data.role)
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户创建失败"
        )

def authenticate_user(username: str, password: str) -> Optional[AdminUser]:
    """用户认证"""
    try:
        user = AdminUser.authenticate(username, password)
        return user
    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        return None

# API端点
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegistrationRequest):
    """用户注册"""
    try:
        # 创建用户
        user = create_user_in_db(user_data)
        
        logger.info(f"用户注册成功: {user.email}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            real_name=user.real_name,
            phone=user.phone,
            department=user.department,
            student_id=user.student_id,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            login_count=user.login_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户注册失败"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: UserLoginRequest):
    """用户登录"""
    try:
        user = authenticate_user(login_data.username, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 创建访问令牌
        access_token = create_access_token(user.to_dict())
        
        logger.info(f"用户登录成功: {user.email}")
        
        return LoginResponse(
            access_token=access_token,
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                real_name=user.real_name,
                phone=user.phone,
                department=user.department,
                student_id=user.student_id,
                role=user.role.value,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                login_count=user.login_count
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
        user = AdminUser.get_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            real_name=user.real_name,
            phone=user.phone,
            department=user.department,
            student_id=user.student_id,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            login_count=user.login_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.get("/", response_model=PaginatedUsersResponse)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取用户列表（管理员权限）- 全新简化版本"""
    try:
        logger.info(f"🔍 管理员 {admin_user.get('username', 'unknown')} 请求用户列表")
        logger.info(f"📋 请求参数: page={page}, limit={limit}, search={search}, is_active={is_active}")
        
        # 导入新的User模型
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from new_user_model import NewUser
        
        # 调用新的User模型获取数据
        users, total_count = await NewUser.get_paginated_simple(
            page=page,
            limit=limit,
            search=search,
            is_active=is_active
        )
        
        logger.info(f"📊 获取到 {len(users)} 个用户，总数: {total_count}")
        
        # 转换为响应格式
        user_responses = []
        for user in users:
            user_dict = user.to_dict()
            user_response = UserResponse(
                id=user_dict['id'],
                email=user_dict['email'],
                username=user_dict['username'],
                is_active=user_dict['is_active'],
                is_verified=user_dict['is_verified'],
                created_at=user_dict['created_at'],
                updated_at=user_dict['updated_at'],
                last_login=user_dict['last_login'],
                login_count=user_dict['login_count'],
                profile=user_dict['profile']
            )
            user_responses.append(user_response)
            logger.info(f"  ✅ 转换用户: {user.id} - {user.username}")
        
        # 计算分页信息
        total_pages = (total_count + limit - 1) // limit
        
        logger.info(f"✅ 成功返回用户列表: {len(user_responses)} 个用户")
        
        return PaginatedUsersResponse(
            success=True,
            data={
                "users": user_responses,
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            },
            message=f"成功获取用户列表，共 {total_count} 个用户"
        )
        
    except Exception as e:
        logger.error(f"❌ 获取用户列表失败: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """根据ID获取用户信息（管理员权限）"""
    try:
        user = await User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            profile=user.profile
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """更新用户信息（管理员权限）"""
    try:
        user = AdminUser.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户信息
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            user.update(**update_dict)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            real_name=user.real_name,
            phone=user.phone,
            department=user.department,
            student_id=user.student_id,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            login_count=user.login_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """删除用户及其所有相关数据（管理员权限）"""
    try:
        user = AdminUser.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不允许删除超级管理员
        if user.role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能删除超级管理员"
            )
        
        # 不允许删除自己
        if user.id == admin_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能删除自己"
            )
        
        # 记录要删除的用户信息（用于日志）
        deleted_user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
        # 执行级联删除
        if await user.delete():
            logger.info(f"管理员 {admin_user['username']} 删除了用户 {user.username} 及其所有相关数据")
            
            return {
                "success": True,
                "message": f"用户 {user.username} 及其所有相关数据删除成功",
                "deleted_user": deleted_user_info,
                "deleted_by": admin_user["username"],
                "deleted_at": datetime.now().isoformat(),
                "cascade_deleted": [
                    "用户上传的文件记录",
                    "用户创建的文档",
                    "用户的学习资源"
                ]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户删除失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """激活用户（管理员权限）"""
    try:
        user = AdminUser.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user.update(is_active=True)
        
        return {"message": "用户激活成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活用户失败"
        )

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """停用用户（管理员权限）"""
    try:
        user = AdminUser.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不允许停用超级管理员
        if user.role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能停用超级管理员"
            )
        
        # 不允许停用自己
        if user.id == admin_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能停用自己"
            )
        
        user.update(is_active=False)
        
        return {"message": "用户停用成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停用用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用用户失败"
        )

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """重置用户密码（管理员权限）"""
    try:
        user = AdminUser.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 重置密码
        if user.reset_password(password_data.new_password):
            # 保存到数据库
            user.save()
            
            logger.info(f"管理员 {admin_user['username']} 重置了用户 {user.username} 的密码")
            
            return {
                "success": True,
                "message": f"用户 {user.username} 的密码重置成功",
                "user_id": user_id,
                "reset_by": admin_user["username"],
                "reset_time": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码重置失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置用户密码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置用户密码失败"
        )