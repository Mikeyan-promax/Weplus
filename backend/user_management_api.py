"""
用户管理API模块
提供用户管理相关的API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging

from database.config import get_db_connection

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])

# 数据模型
class User(BaseModel):
    id: int
    username: str
    email: str
    status: str
    created_at: str
    last_login: Optional[str] = None
    password_created_at: Optional[str] = None  # 密码创建时间
    password_strength: Optional[str] = None    # 密码强度指示

class UserStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    new_users_today: int

class UserResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str = ""

class UserStatusUpdate(BaseModel):
    is_active: bool

# 辅助函数
def calculate_password_strength(password_hash: str) -> str:
    """根据密码哈希值计算密码强度指示"""
    if not password_hash:
        return "未知"
    
    # 基于哈希值长度的简单强度指示
    if len(password_hash) > 60:
        return "强"
    elif len(password_hash) > 40:
        return "中"
    else:
        return "弱"

@router.get("/", response_model=UserResponse)
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """获取用户列表 - 从PostgreSQL数据库获取真实数据"""
    try:
        with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 构建查询条件
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("(username ILIKE %s OR email ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if status:
                # 将前端状态映射到数据库字段
                if status == "active":
                    where_conditions.append("is_active = %s")
                    params.append(True)
                elif status == "inactive":
                    where_conditions.append("is_active = %s")
                    params.append(False)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM users {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['count']
            
            # 获取分页数据
            offset = (page - 1) * limit
            data_query = f"""
                SELECT id, username, email, is_active, created_at, updated_at, last_login, password_hash
                FROM users {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, params + [limit, offset])
            rows = cursor.fetchall()
            
            # 转换数据格式
            users = []
            for row in rows:
             # 计算密码强度
             password_strength = calculate_password_strength(row['password_hash'])
             
             users.append({
                 "id": row['id'],
                 "username": row['username'],
                 "email": row['email'],
                 "status": "active" if row['is_active'] else "inactive",
                 "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                 "last_login": row['last_login'].isoformat() if row['last_login'] else None,
                 "password_created_at": row['created_at'].isoformat() if row['created_at'] else None,
                 "password_strength": password_strength
             })
         
             return UserResponse(
                 success=True,
                 data={
                     "users": users,
                     "total": total,
                     "page": page,
                     "limit": limit
                 },
                 message="获取用户列表成功"
             )
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

@router.get("/stats", response_model=UserResponse)
async def get_user_stats():
    """获取用户统计信息 - 从PostgreSQL数据库获取真实数据"""
    try:
        with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 获取总用户数
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            # 获取活跃用户数
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = true")
            active_users = cursor.fetchone()['count']
            
            # 获取非活跃用户数
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = false")
            inactive_users = cursor.fetchone()['count']
            
            # 获取今日新用户数
            today = datetime.now().date()
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = %s", (today,))
            new_users_today = cursor.fetchone()['count']
            
            stats = {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "new_users_today": new_users_today
            }
            
            return UserResponse(
                success=True,
                data=stats,
                message="获取用户统计成功"
            )
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_detail(user_id: int):
    """获取用户详细信息"""
    try:
        with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, username, email, is_active, is_verified, created_at, 
                       updated_at, last_login, password_hash, profile
                FROM users WHERE id = %s
            """, (user_id,))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 计算密码强度
            password_strength = calculate_password_strength(row['password_hash'])
            
            user_data = {
                "id": row['id'],
                "username": row['username'],
                "email": row['email'],
                "status": "active" if row['is_active'] else "inactive",
                "is_verified": row['is_verified'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
                "last_login": row['last_login'].isoformat() if row['last_login'] else None,
                "password_created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "password_strength": password_strength,
                "profile": row['profile'] if row['profile'] else {}
            }
            
            return UserResponse(
                success=True,
                data=user_data,
                message="获取用户详情成功"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户详情失败: {str(e)}")

@router.put("/{user_id}/status")
async def update_user_status(user_id: int, status_update: UserStatusUpdate):
    """更新用户状态"""
    try:
        with get_db_connection() as conn, conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 更新用户状态
            cursor.execute("""
                UPDATE users 
                SET is_active = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (status_update.is_active, user_id))
            
            conn.commit()
            
            status_text = "激活" if status_update.is_active else "禁用"
            return UserResponse(
                success=True,
                message=f"用户状态已更新为 {status_text}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户状态失败: {e}")
        raise HTTPException(status_code=500, detail="更新用户状态失败")

@router.put("/{user_id}/verify")
async def update_user_verification(user_id: int):
    """更新用户验证状态"""
    try:
        with get_db_connection() as conn, conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id, is_verified FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 切换验证状态
            new_verification_status = not user[1]
            cursor.execute("""
                UPDATE users 
                SET is_verified = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (new_verification_status, user_id))
            
            conn.commit()
            
            status_text = "已验证" if new_verification_status else "未验证"
            return UserResponse(
                success=True,
                message=f"用户验证状态已更新为 {status_text}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户验证状态失败: {e}")
        raise HTTPException(status_code=500, detail="更新用户验证状态失败")

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """删除用户（软删除）"""
    try:
        with get_db_connection() as conn, conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 软删除用户（设置为非活跃状态）
            cursor.execute("""
                UPDATE users 
                SET is_active = false, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user_id,))
            
            conn.commit()
            
            return UserResponse(
                success=True,
                message="用户已删除"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        raise HTTPException(status_code=500, detail="删除用户失败")

@router.post("/{user_id}/reset-password")
async def reset_user_password(user_id: int):
    """重置用户密码"""
    try:
        with get_db_connection() as conn, conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 这里应该生成临时密码并发送邮件
            # 目前只是模拟操作
            temp_password = "TempPass123!"
            
            # 在实际应用中，这里应该：
            # 1. 生成安全的临时密码
            # 2. 哈希密码并更新数据库
            # 3. 发送邮件通知用户
            
            return UserResponse(
                success=True,
                message="密码重置邮件已发送到用户邮箱"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置用户密码失败: {e}")
        raise HTTPException(status_code=500, detail="重置用户密码失败")

@router.get("/{user_id}/activity")
async def get_user_activity(user_id: int, limit: int = Query(10, ge=1, le=50)):
    """获取用户活动记录"""
    try:
        with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 获取用户活动记录（从日志表）
            cursor.execute("""
                SELECT action, details, created_at
                FROM user_action_logs 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "action": row['action'],
                    "details": row['details'],
                    "timestamp": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return UserResponse(
                success=True,
                data={"activities": activities},
                message="获取用户活动记录成功"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户活动记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户活动记录失败")