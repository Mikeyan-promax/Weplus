"""
认证路由模块
提供用户注册、登录、邮箱验证等API接口
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime

from auth_service import auth_service
from app.services.email_service import email_service
from app.core.config import settings
from database.config import get_db_connection

# 创建路由器
router = APIRouter(prefix="/auth", tags=["认证"])

# HTTP Bearer 认证
security = HTTPBearer()

# 配置日志
logger = logging.getLogger(__name__)

# 复用全局邮件服务实例（确保验证码内存存储一致）

# Pydantic 模型
class UserRegister(BaseModel):
    """用户注册模型"""
    email: EmailStr
    username: str
    password: str
    confirm_password: str
    verification_code: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError('用户名长度必须在2-50个字符之间')
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和中文字符')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码必须包含至少一个数字')
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('verification_code')
    def validate_verification_code(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('请输入验证码')
        if len(v) != 6:
            raise ValueError('验证码必须是6位数字')
        if not v.isdigit():
            raise ValueError('验证码只能包含数字')
        return v

class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str

class EmailVerificationRequest(BaseModel):
    """邮箱验证请求模型"""
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    """邮箱验证确认模型"""
    email: EmailStr
    code: str

class TokenRefresh(BaseModel):
    """令牌刷新模型"""
    refresh_token: str

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: Optional[str] = None

class TokenResponse(BaseModel):
    """令牌响应模型"""
    success: bool = True
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

# 辅助函数
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """根据邮箱获取用户
    
    说明：
    - 使用同步连接池上下文获取连接与游标；
    - 捕获并记录详细异常信息，便于定位“连接已关闭”等问题。
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, email, username, password_hash, is_active, is_verified,
                           created_at, updated_at, last_login, profile
                    FROM users WHERE email = %s
                """, (email,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'email': row['email'],
                        'username': row['username'],
                        'password_hash': row['password_hash'],
                        'is_active': bool(row['is_active']),
                        'is_verified': bool(row['is_verified']),
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                        'last_login': row['last_login'].isoformat() if row['last_login'] else None,
                        'profile': row['profile'] if row['profile'] else {}
                    }
                return None
    except Exception as e:
        logger.error(f"获取用户失败: {type(e).__name__} - {str(e)}")
        return None

def create_user(email: str, username: str, password: str) -> Dict[str, Any]:
    """创建新用户
    
    说明：
    - 插入用户基础信息并返回完整字段；
    - 在失败时抛出 HTTP 500，记录详细异常类型。
    """
    password_hash = auth_service.hash_password(password)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO users (email, username, password_hash, profile)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, email, username, password_hash, is_active, is_verified,
                              created_at, updated_at, last_login, profile
                """, (email, username, password_hash, '{}'))
                
                row = cursor.fetchone()
                conn.commit()
                
                return {
                    'id': row['id'],
                    'email': row['email'],
                    'username': row['username'],
                    'password_hash': row['password_hash'],
                    'is_active': bool(row['is_active']),
                    'is_verified': bool(row['is_verified']),
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'last_login': row['last_login'].isoformat() if row['last_login'] else None,
                    'profile': row['profile'] if row['profile'] else {}
                }
    except Exception as e:
        logger.error(f"创建用户失败: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )

def update_user_verification(email: str, is_verified: bool = True):
    """更新用户验证状态
    
    说明：
    - 标记邮箱验证，同时更新更新时间戳。
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users SET is_verified = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE email = %s
                """, (is_verified, email))
                conn.commit()
    except Exception as e:
        logger.error(f"更新用户验证状态失败: {type(e).__name__} - {str(e)}")

def update_user_last_login(user_id: int):
    """更新用户最后登录时间
    
    说明：
    - 登录成功后记录 last_login 与 updated_at。
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
    except Exception as e:
        logger.error(f"更新用户最后登录时间失败: {type(e).__name__} - {str(e)}")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前用户"""
    token = credentials.credentials
    user_info = auth_service.get_user_from_token(token)
    
    # 从数据库获取完整用户信息
    user = get_user_by_email(user_info["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    return user

# API 路由
@router.post("/send-verification-code", summary="发送邮箱验证码")
async def send_verification_code(
    request: EmailVerificationRequest,
    background_tasks: BackgroundTasks
):
    """发送邮箱验证码"""
    try:
        # 检查邮箱是否已注册
        existing_user = get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
        
        # 发送验证码
        result = await email_service.send_verification_code(request.email)
        if result.get("success"):
            response = {
                "success": True,
                "message": result.get("message", "验证码已发送到您的邮箱，请查收"),
                "email": request.email
            }
            # 开发模式下透传调试信息（不在生产暴露）
            if getattr(settings, "DEBUG", False) and result.get("dev"):
                response["dev"] = result["dev"]
            return response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "发送验证码失败，请稍后重试")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败"
        )

@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register_user(user_data: UserRegister):
    """用户注册"""
    try:
        # 验证邮箱验证码
        verify_result = await email_service.verify_code(user_data.email, user_data.verification_code)
        if not verify_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verify_result.get("message", "验证码无效或已过期")
            )
        
        # 检查邮箱是否已注册
        existing_user = get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
        
        # 创建用户
        user = create_user(user_data.email, user_data.username, user_data.password)
        
        # 标记邮箱为已验证
        update_user_verification(user_data.email, True)
        user['is_verified'] = True
        
        # 生成令牌
        token_pair = auth_service.create_token_pair(user)
        access_token = token_pair["access_token"]
        refresh_token = token_pair["refresh_token"]
        
        # 更新最后登录时间
        update_user_last_login(user['id'])
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=user['id'],
                email=user['email'],
                username=user['username'],
                is_active=user['is_active'],
                is_verified=user['is_verified'],
                created_at=user['created_at'],
                last_login=user['last_login']
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login_user(user_data: UserLogin):
    """用户登录"""
    try:
        # 获取用户
        user = get_user_by_email(user_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        # 验证密码
        if not auth_service.verify_password(user_data.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        # 检查用户状态
        if not user['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )
        
        if not user['is_verified']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="请先验证邮箱"
            )
        
        # 生成令牌
        tokens = auth_service.create_token_pair(user)
        
        # 更新最后登录时间
        update_user_last_login(user['id'])
        user['last_login'] = datetime.now().isoformat()
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=UserResponse(
                id=user['id'],
                email=user['email'],
                username=user['username'],
                is_active=user['is_active'],
                is_verified=user['is_verified'],
                created_at=user['created_at'],
                last_login=user['last_login']
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(token_data: TokenRefresh):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        user_info = auth_service.get_user_from_refresh_token(token_data.refresh_token)
        
        # 获取用户信息
        user = get_user_by_email(user_info["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        if not user['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )
        
        # 生成令牌
        tokens = auth_service.create_token_pair(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=UserResponse(
                id=user['id'],
                email=user['email'],
                username=user['username'],
                is_active=user['is_active'],
                is_verified=user['is_verified'],
                created_at=user['created_at'],
                last_login=user['last_login']
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效"
        )

@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        username=current_user['username'],
        is_active=current_user['is_active'],
        is_verified=current_user['is_verified'],
        created_at=current_user['created_at'],
        last_login=current_user['last_login']
    )

@router.post("/verify-email", summary="验证邮箱")
async def verify_email(request: EmailVerificationConfirm):
    """验证邮箱
    
    说明：
    - 仅进行验证码正确性校验，但不删除（不消费）验证码；
    - 保留验证码供后续 /register 端点进行二次校验并消费，避免注册阶段出现“验证码不存在或已过期”。
    """
    try:
        # 验证验证码（不删除，保留供注册阶段消费）
        verify_result = await email_service.verify_code(request.email, request.code, delete_on_success=False)
        if not verify_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=verify_result.get("message", "验证码无效或已过期")
            )
        
        # 更新用户验证状态
        update_user_verification(request.email, True)
        
        return {
            "success": True,
            "message": "邮箱验证成功"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"邮箱验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证失败，请稍后重试"
        )

@router.post("/logout", summary="用户登出")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """用户登出"""
    try:
        # 这里可以添加令牌黑名单逻辑
        # 目前只是返回成功响应
        return {
            "success": True,
            "message": "登出成功"
        }
    
    except Exception as e:
        logger.error(f"用户登出失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )

@router.post("/resend-verification", summary="重新发送验证码")
async def resend_verification_code(
    request: EmailVerificationRequest,
    background_tasks: BackgroundTasks
):
    """重新发送验证码"""
    try:
        # 发送验证码
        result = await email_service.send_verification_code(request.email)
        if result.get("success"):
            resp = {
                "success": True,
                "message": result.get("message", "验证码已重新发送到您的邮箱")
            }
            if getattr(settings, "DEBUG", False) and result.get("dev"):
                resp["dev"] = result["dev"]
            return resp
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "发送验证码失败，请稍后重试")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新发送验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败"
        )
