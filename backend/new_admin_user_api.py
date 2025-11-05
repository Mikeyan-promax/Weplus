#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全新的用户管理API - 简化版本，确保功能正确
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from new_user_model import NewUser

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])

# HTTP Bearer认证
security = HTTPBearer()

# Pydantic模型
class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None
    profile: Dict[str, Any] = {}

class PaginatedUsersResponse(BaseModel):
    """分页用户响应模型"""
    success: bool
    message: str
    data: Dict[str, Any]

# 简化的认证依赖（暂时跳过真实认证）
async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前管理员用户（简化版本）"""
    # 暂时跳过真实的JWT验证，直接返回管理员信息
    return {"id": 1, "username": "admin", "is_admin": True}

@router.get("", response_model=PaginatedUsersResponse)
async def list_users_new(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="激活状态过滤"),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    获取用户列表 - 全新简化版本
    
    Args:
        page: 页码（从1开始）
        limit: 每页数量（1-100）
        search: 搜索关键词（用户名或邮箱）
        is_active: 激活状态过滤
        current_user: 当前管理员用户
    
    Returns:
        PaginatedUsersResponse: 分页用户响应
    """
    try:
        logger.info(f"🔍 管理员 {current_user['username']} 请求用户列表")
        logger.info(f"📋 请求参数: page={page}, limit={limit}, search={search}, is_active={is_active}")
        
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
            user_response = UserResponse(**user_dict)
            user_responses.append(user_response.dict())
            logger.info(f"  ✅ 转换用户: {user.id} - {user.username}")
        
        # 计算分页信息
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # 构建响应数据
        response_data = {
            "users": user_responses,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
        
        logger.info(f"✅ 成功返回用户列表: {len(user_responses)} 个用户")
        
        return PaginatedUsersResponse(
            success=True,
            message=f"成功获取用户列表，共 {total_count} 个用户",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ 获取用户列表失败: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"获取用户列表失败: {str(e)}"
        )

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id_new(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    根据ID获取用户信息
    
    Args:
        user_id: 用户ID
        current_user: 当前管理员用户
    
    Returns:
        Dict[str, Any]: 用户信息
    """
    try:
        logger.info(f"🔍 管理员 {current_user['username']} 请求用户 {user_id} 的信息")
        
        # 这里可以添加根据ID获取单个用户的逻辑
        # 暂时返回一个简单的响应
        return {
            "success": True,
            "message": f"获取用户 {user_id} 信息成功",
            "data": {"user_id": user_id, "message": "功能开发中"}
        }
        
    except Exception as e:
        logger.error(f"❌ 获取用户 {user_id} 信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户信息失败: {str(e)}"
        )

# 如果直接运行此文件，启动测试服务器
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="用户管理API测试", version="1.0.0")
    app.include_router(router)
    
    print("🚀 启动用户管理API测试服务器...")
    print("📋 API文档: http://localhost:8001/docs")
    print("🔍 用户列表: http://localhost:8001/api/admin/users")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)