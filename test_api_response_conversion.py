#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API响应转换问题 - 调试为什么API只返回1个用户
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from database.models import User
from dotenv import load_dotenv
import json

async def test_api_response_conversion():
    """测试API响应转换过程"""
    print("🔍 测试API响应转换过程")
    print("=" * 60)
    
    # 加载环境变量
    backend_env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
    if os.path.exists(backend_env_path):
        load_dotenv(backend_env_path)
        print("✅ 已加载backend/.env环境变量")
    
    try:
        # 模拟API调用参数
        page = 1
        limit = 20
        search = None
        filters = {}
        
        print(f"\n📋 模拟API调用参数:")
        print(f"   - page: {page}")
        print(f"   - limit: {limit}")
        print(f"   - search: {search}")
        print(f"   - filters: {filters}")
        
        # 调用User.get_paginated方法
        print(f"\n🔍 调用User.get_paginated方法...")
        users, total = await User.get_paginated(
            page=page,
            limit=limit,
            search=search,
            filters=filters
        )
        
        print(f"✅ User.get_paginated返回结果:")
        print(f"   - 用户数量: {len(users)}")
        print(f"   - 总用户数: {total}")
        
        # 检查每个用户对象的属性
        print(f"\n🔍 检查用户对象属性:")
        for i, user in enumerate(users[:3], 1):  # 只检查前3个
            print(f"   用户 {i}:")
            print(f"     - id: {user.id}")
            print(f"     - email: {user.email}")
            print(f"     - username: {user.username}")
            print(f"     - is_active: {user.is_active}")
            print(f"     - is_verified: {user.is_verified}")
            print(f"     - created_at: {user.created_at}")
            print(f"     - updated_at: {user.updated_at}")
            print(f"     - last_login: {user.last_login}")
            print(f"     - profile: {user.profile}")
            print(f"     - profile type: {type(user.profile)}")
        
        # 模拟API响应转换过程
        print(f"\n🔍 模拟API响应转换过程...")
        
        # 导入UserResponse模型
        sys.path.insert(0, os.path.join(backend_path, "app", "api"))
        from admin_user_api import UserResponse
        
        user_responses = []
        for user in users:
            try:
                user_response = UserResponse(
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
                user_responses.append(user_response)
                print(f"   ✅ 成功转换用户 {user.id}")
            except Exception as e:
                print(f"   ❌ 转换用户 {user.id} 失败: {e}")
                print(f"      用户数据: {user}")
        
        print(f"\n📋 转换结果:")
        print(f"   - 成功转换的用户数: {len(user_responses)}")
        
        # 模拟完整的API响应
        total_pages = (total + limit - 1) // limit
        
        api_response = {
            "success": True,
            "data": {
                "users": [user_response.dict() for user_response in user_responses],
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            },
            "message": "获取用户列表成功"
        }
        
        print(f"\n📋 模拟API响应:")
        print(f"   - 响应中的用户数: {len(api_response['data']['users'])}")
        print(f"   - 总用户数: {api_response['data']['total']}")
        print(f"   - 页码: {api_response['data']['page']}")
        print(f"   - 每页数量: {api_response['data']['limit']}")
        
        # 显示前3个用户的响应数据
        if api_response['data']['users']:
            print(f"\n📋 前3个用户的响应数据:")
            for i, user_data in enumerate(api_response['data']['users'][:3], 1):
                print(f"   用户 {i}: ID={user_data['id']}, 用户名={user_data['username']}")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await test_api_response_conversion()
    print(f"\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(main())