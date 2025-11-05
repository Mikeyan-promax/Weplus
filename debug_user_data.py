#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试用户数据 - 检查数据库中实际的用户信息
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def check_database_users():
    """检查数据库中的用户数据"""
    print("=" * 60)
    print("🔍 开始检查数据库中的用户数据")
    print("=" * 60)
    
    # 数据库连接配置 - 从backend/.env读取
    backend_env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
    if os.path.exists(backend_env_path):
        load_dotenv(backend_env_path)
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://weplus_db:123456yzlA@pgm-2ze58b40mdfqec4zwo.pg.rds.aliyuncs.com:5432/weplus_db")
    
    try:
        # 连接数据库
        print(f"📡 正在连接数据库: {DATABASE_URL}")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ 数据库连接成功")
        
        # 1. 检查users表是否存在
        print("\n📋 步骤1: 检查users表是否存在")
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        print(f"   users表存在: {table_exists}")
        
        if not table_exists:
            print("❌ users表不存在！")
            return
        
        # 2. 获取users表的结构
        print("\n📋 步骤2: 获取users表结构")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        print("   users表字段结构:")
        for col in columns:
            print(f"     - {col['column_name']}: {col['data_type']} (可空: {col['is_nullable']})")
        
        # 3. 统计用户总数
        print("\n📋 步骤3: 统计用户总数")
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users;")
        print(f"   用户总数: {total_users}")
        
        # 4. 获取所有用户的基本信息
        print("\n📋 步骤4: 获取所有用户的详细信息")
        users = await conn.fetch("""
            SELECT id, username, email, is_active, is_verified, created_at, last_login, 
                   updated_at, profile
            FROM users 
            ORDER BY id;
        """)
        
        print(f"   查询到 {len(users)} 个用户:")
        for i, user in enumerate(users, 1):
            print(f"     {i}. ID: {user['id']}")
            print(f"        用户名: {user['username']}")
            print(f"        邮箱: {user['email']}")
            print(f"        激活状态: {user['is_active']}")
            print(f"        验证状态: {user['is_verified']}")
            print(f"        创建时间: {user['created_at']}")
            print(f"        最后登录: {user['last_login']}")
            print(f"        更新时间: {user['updated_at']}")
            print(f"        个人资料: {user['profile']}")
            print("        " + "-" * 40)
        
        # 5. 按状态分组统计
        print("\n📋 步骤5: 按激活状态分组统计")
        status_stats = await conn.fetch("""
            SELECT is_active, COUNT(*) as count
            FROM users 
            GROUP BY is_active
            ORDER BY count DESC;
        """)
        
        print("   用户激活状态分布:")
        for stat in status_stats:
            status_text = "激活" if stat['is_active'] else "未激活"
            print(f"     - {status_text}: {stat['count']} 个用户")
        
        # 6. 检查最近创建的用户
        print("\n📋 步骤6: 检查最近创建的用户")
        recent_users = await conn.fetch("""
            SELECT id, username, email, created_at
            FROM users 
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        
        print("   最近创建的5个用户:")
        for user in recent_users:
            print(f"     - ID: {user['id']}, 用户名: {user['username']}, 创建时间: {user['created_at']}")
        
        # 7. 检查是否有重复的用户名或邮箱
        print("\n📋 步骤7: 检查数据完整性")
        
        # 检查重复用户名
        duplicate_usernames = await conn.fetch("""
            SELECT username, COUNT(*) as count
            FROM users 
            GROUP BY username
            HAVING COUNT(*) > 1;
        """)
        
        if duplicate_usernames:
            print("   ⚠️ 发现重复用户名:")
            for dup in duplicate_usernames:
                print(f"     - {dup['username']}: {dup['count']} 次")
        else:
            print("   ✅ 没有重复用户名")
        
        # 检查重复邮箱
        duplicate_emails = await conn.fetch("""
            SELECT email, COUNT(*) as count
            FROM users 
            GROUP BY email
            HAVING COUNT(*) > 1;
        """)
        
        if duplicate_emails:
            print("   ⚠️ 发现重复邮箱:")
            for dup in duplicate_emails:
                print(f"     - {dup['email']}: {dup['count']} 次")
        else:
            print("   ✅ 没有重复邮箱")
        
        # 8. 检查NULL值
        print("\n📋 步骤8: 检查NULL值情况")
        null_checks = [
            ("username", "用户名"),
            ("email", "邮箱"),
            ("is_active", "激活状态"),
            ("created_at", "创建时间")
        ]
        
        for field, name in null_checks:
            null_count = await conn.fetchval(f"SELECT COUNT(*) FROM users WHERE {field} IS NULL;")
            if null_count > 0:
                print(f"   ⚠️ {name}为NULL的用户: {null_count} 个")
            else:
                print(f"   ✅ {name}字段完整")
        
        await conn.close()
        print("\n✅ 数据库检查完成")
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await check_database_users()

if __name__ == "__main__":
    asyncio.run(main())