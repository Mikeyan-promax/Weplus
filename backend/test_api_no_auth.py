#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临时测试API端点 - 绕过认证
"""

from fastapi import FastAPI, Query
from typing import Optional
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(__file__))

app = FastAPI()

@app.get("/test-users")
async def test_list_users(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="状态筛选")
):
    """测试用户列表API - 无需认证"""
    try:
        print(f"🔍 测试API调用")
        print(f"📋 请求参数: page={page}, limit={limit}, search={search}, is_active={is_active}")
        
        # 导入新的User模型
        from new_user_model import NewUser
        
        # 调用新的User模型获取数据
        users, total_count = await NewUser.get_paginated_simple(
            page=page,
            limit=limit,
            search=search,
            is_active=is_active
        )
        
        print(f"📊 获取到 {len(users)} 个用户，总数: {total_count}")
        
        # 转换为响应格式
        user_responses = []
        for user in users:
            user_dict = user.to_dict()
            user_response = {
                "id": user_dict['id'],
                "email": user_dict['email'],
                "username": user_dict['username'],
                "is_active": user_dict['is_active'],
                "is_verified": user_dict['is_verified'],
                "created_at": user_dict['created_at'],
                "updated_at": user_dict['updated_at'],
                "last_login": user_dict['last_login'],
                "profile": user_dict['profile']
            }
            user_responses.append(user_response)
            print(f"  ✅ 转换用户: {user.id} - {user.username}")
        
        # 计算分页信息
        total_pages = (total_count + limit - 1) // limit
        
        print(f"✅ 成功返回用户列表: {len(user_responses)} 个用户")
        
        return {
            "success": True,
            "data": {
                "users": user_responses,
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            },
            "message": f"成功获取用户列表，共 {total_count} 个用户"
        }
        
    except Exception as e:
        print(f"❌ 获取用户列表失败: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "message": "获取用户列表失败"
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动测试API服务器...")
    uvicorn.run(app, host="127.0.0.1", port=8001)