"""
用户API模块
提供用户相关的API接口，如用户资料等
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any
from pydantic import BaseModel
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import logging

from database.config import get_db_connection
from psycopg2.extras import RealDictCursor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["用户"])

# JWT配置
JWT_SECRET_KEY = "weplus_admin_secret_key_2024"
JWT_ALGORITHM = "HS256"

# 数据模型
class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    real_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    student_id: Optional[str] = None
    profile: Dict[str, Any] = {}
    created_at: str
    last_login: Optional[str] = None

class UserProfileResponse(BaseModel):
    success: bool
    data: Optional[UserProfile] = None
    message: str = ""

# 依赖函数：验证JWT令牌
async def get_current_user(authorization: Optional[str] = Header(None)):
    """从JWT令牌获取当前用户信息"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    try:
        # 提取Bearer令牌
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="无效的令牌格式")
        
        token = authorization.split(" ")[1]
        
        # 解码JWT令牌
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的令牌")
        
        return user_id
        
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user_id: int = Depends(get_current_user)):
    """获取当前用户的资料信息"""
    try:
        logger.info(f"获取用户资料，用户ID: {current_user_id}")
        
        with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 查询用户信息
            query = """
                SELECT id, username, email, real_name, phone, department, 
                       student_id, profile, created_at, last_login
                FROM users 
                WHERE id = %s AND is_active = true
            """
            cursor.execute(query, (current_user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                raise HTTPException(status_code=404, detail="用户不存在或已被禁用")
            
            # 构建用户资料响应
            profile_data = UserProfile(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                real_name=user_data.get('real_name'),
                phone=user_data.get('phone'),
                department=user_data.get('department'),
                student_id=user_data.get('student_id'),
                profile=user_data.get('profile', {}),
                created_at=user_data['created_at'].isoformat() if user_data['created_at'] else None,
                last_login=user_data['last_login'].isoformat() if user_data['last_login'] else None
            )
            
            logger.info(f"成功获取用户资料: {user_data['username']}")
            
            return UserProfileResponse(
                success=True,
                data=profile_data,
                message="成功获取用户资料"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户资料失败: {str(e)}")

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: Dict[str, Any],
    current_user_id: int = Depends(get_current_user)
):
    """更新当前用户的资料信息"""
    try:
        logger.info(f"更新用户资料，用户ID: {current_user_id}")
        
        # 允许更新的字段
        allowed_fields = ['real_name', 'phone', 'department', 'student_id', 'profile']
        update_fields = []
        update_values = []
        
        for field, value in profile_update.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = %s")
                update_values.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有有效的更新字段")
        
        update_values.append(current_user_id)
        
        with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 更新用户信息
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND is_active = true
                RETURNING id, username, email, real_name, phone, department, 
                          student_id, profile, created_at, last_login
            """
            cursor.execute(query, update_values)
            updated_user = cursor.fetchone()
            
            if not updated_user:
                raise HTTPException(status_code=404, detail="用户不存在或已被禁用")
            
            conn.commit()
            
            # 构建响应
            profile_data = UserProfile(
                id=updated_user['id'],
                username=updated_user['username'],
                email=updated_user['email'],
                real_name=updated_user.get('real_name'),
                phone=updated_user.get('phone'),
                department=updated_user.get('department'),
                student_id=updated_user.get('student_id'),
                profile=updated_user.get('profile', {}),
                created_at=updated_user['created_at'].isoformat() if updated_user['created_at'] else None,
                last_login=updated_user['last_login'].isoformat() if updated_user['last_login'] else None
            )
            
            logger.info(f"成功更新用户资料: {updated_user['username']}")
            
            return UserProfileResponse(
                success=True,
                data=profile_data,
                message="成功更新用户资料"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新用户资料失败: {str(e)}")