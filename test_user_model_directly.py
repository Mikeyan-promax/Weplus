#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试User.get_paginated方法 - 绕过API层分析问题
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

async def test_user_get_paginated():
    """直接测试User.get_paginated方法"""
    print("🔍 直接测试User.get_paginated方法")
    print("=" * 60)
    
    # 加载环境变量
    backend_env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
    if os.path.exists(backend_env_path):
        load_dotenv(backend_env_path)
        print("✅ 已加载backend/.env环境变量")
    
    try:
        # 测试1: 默认参数
        print("\n📋 测试1: 默认参数 (page=1, limit=10)")
        users, total = await User.get_paginated()
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        if users:
            print("   用户列表:")
            for i, user in enumerate(users, 1):
                print(f"     {i}. ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
                print(f"        激活: {user.is_active}, 验证: {user.is_verified}")
                print(f"        创建时间: {user.created_at}")
        else:
            print("   ⚠️ 没有返回用户")
        
        # 测试2: 更大的limit
        print("\n📋 测试2: 更大的limit (page=1, limit=20)")
        users, total = await User.get_paginated(page=1, limit=20)
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        if users:
            print("   用户列表:")
            for i, user in enumerate(users, 1):
                print(f"     {i}. ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
        
        # 测试3: 无过滤条件
        print("\n📋 测试3: 无过滤条件 (page=1, limit=20, search=None, filters=None)")
        users, total = await User.get_paginated(page=1, limit=20, search=None, filters=None)
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        # 测试4: 空过滤条件
        print("\n📋 测试4: 空过滤条件 (page=1, limit=20, search='', filters={})")
        users, total = await User.get_paginated(page=1, limit=20, search='', filters={})
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        # 测试5: 激活用户过滤
        print("\n📋 测试5: 激活用户过滤 (is_active=True)")
        users, total = await User.get_paginated(page=1, limit=20, filters={'is_active': True})
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        # 测试6: 未激活用户过滤
        print("\n📋 测试6: 未激活用户过滤 (is_active=False)")
        users, total = await User.get_paginated(page=1, limit=20, filters={'is_active': False})
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        # 测试7: 搜索功能
        print("\n📋 测试7: 搜索功能 (search='test')")
        users, total = await User.get_paginated(page=1, limit=20, search='test')
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        if users:
            print("   搜索结果:")
            for i, user in enumerate(users, 1):
                print(f"     {i}. ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_user_get_all_users():
    """测试User.get_all_users方法"""
    print("\n🔍 测试User.get_all_users方法")
    print("=" * 60)
    
    try:
        users, total = await User.get_all_users(page=1, page_size=20)
        print(f"   返回用户数: {len(users)}")
        print(f"   总用户数: {total}")
        
        if users:
            print("   用户列表:")
            for i, user in enumerate(users, 1):
                print(f"     {i}. ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
                print(f"        激活: {user.is_active}, 验证: {user.is_verified}")
        
    except Exception as e:
        print(f"❌ get_all_users测试失败: {e}")
        import traceback
        traceback.print_exc()

async def debug_sql_query():
    """调试SQL查询"""
    print("\n🔍 调试SQL查询")
    print("=" * 60)
    
    try:
        # 导入数据库配置
        from database.config import db_config
        
        # 测试直接SQL查询
        async with db_config.get_connection() as conn:
            # 查询1: 简单计数
            print("\n📋 查询1: 简单计数")
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"   用户总数: {count}")
            
            # 查询2: 获取所有用户ID
            print("\n📋 查询2: 获取所有用户ID")
            ids = await conn.fetch("SELECT id FROM users ORDER BY id")
            print(f"   用户ID列表: {[row['id'] for row in ids]}")
            
            # 查询3: 模拟get_paginated的查询
            print("\n📋 查询3: 模拟get_paginated的查询")
            query = """
                SELECT id, email, username, password_hash, is_active, is_verified,
                       created_at, updated_at, last_login, profile
                FROM users 
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            results = await conn.fetch(query, 20, 0)
            print(f"   查询结果数: {len(results)}")
            
            if results:
                print("   查询结果:")
                for i, row in enumerate(results, 1):
                    print(f"     {i}. ID: {row['id']}, 用户名: {row['username']}, 邮箱: {row['email']}")
                    print(f"        激活: {row['is_active']}, 创建时间: {row['created_at']}")
        
    except Exception as e:
        print(f"❌ SQL调试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("🔍 直接测试User模型方法")
    print("=" * 80)
    
    # 测试get_paginated方法
    await test_user_get_paginated()
    
    # 测试get_all_users方法
    await test_user_get_all_users()
    
    # 调试SQL查询
    await debug_sql_query()
    
    print(f"\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(main())