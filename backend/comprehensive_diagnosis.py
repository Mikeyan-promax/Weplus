#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面诊断脚本 - 分析用户管理系统的所有问题
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

async def comprehensive_diagnosis():
    """执行全面的系统诊断"""
    print("=" * 80)
    print("🔍 开始全面系统诊断...")
    print("=" * 80)
    
    # 获取数据库配置
    db_manager = DatabaseManager()
    config = db_manager.config
    print(f"📊 数据库配置: {config['host']}:{config['port']}/{config['database']}")
    
    try:
        # 连接数据库
        conn = await asyncpg.connect(**config)
        print("✅ 数据库连接成功")
        
        # 1. 检查用户表结构
        print("\n" + "=" * 50)
        print("📋 1. 检查用户表结构")
        print("=" * 50)
        
        table_info = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print("用户表字段:")
        for row in table_info:
            print(f"  - {row['column_name']}: {row['data_type']} "
                  f"({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # 2. 检查用户数据完整性
        print("\n" + "=" * 50)
        print("📊 2. 检查用户数据完整性")
        print("=" * 50)
        
        # 总用户数
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"📈 总用户数: {total_users}")
        
        # 活跃用户数
        active_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
        print(f"✅ 活跃用户数: {active_users}")
        
        # 已验证用户数
        verified_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_verified = true")
        print(f"🔐 已验证用户数: {verified_users}")
        
        # 检查空值
        null_checks = [
            ("用户名为空", "SELECT COUNT(*) FROM users WHERE username IS NULL OR username = ''"),
            ("邮箱为空", "SELECT COUNT(*) FROM users WHERE email IS NULL OR email = ''"),
            ("密码哈希为空", "SELECT COUNT(*) FROM users WHERE password_hash IS NULL OR password_hash = ''"),
        ]
        
        for check_name, query in null_checks:
            count = await conn.fetchval(query)
            status = "❌" if count > 0 else "✅"
            print(f"{status} {check_name}: {count}")
        
        # 3. 获取所有用户的详细信息
        print("\n" + "=" * 50)
        print("👥 3. 用户详细信息")
        print("=" * 50)
        
        users = await conn.fetch("""
            SELECT id, username, email, is_active, is_verified, 
                   created_at, updated_at, last_login
            FROM users 
            ORDER BY id
        """)
        
        print(f"获取到 {len(users)} 个用户:")
        for user in users:
            print(f"  ID: {user['id']}")
            print(f"    用户名: {user['username']}")
            print(f"    邮箱: {user['email']}")
            print(f"    状态: {'活跃' if user['is_active'] else '禁用'} | "
                  f"{'已验证' if user['is_verified'] else '未验证'}")
            print(f"    创建时间: {user['created_at']}")
            print(f"    最后登录: {user['last_login'] or '从未登录'}")
            print()
        
        # 4. 测试分页查询
        print("\n" + "=" * 50)
        print("📄 4. 测试分页查询")
        print("=" * 50)
        
        # 测试不同的分页参数
        test_cases = [
            (20, 0, "第1页，每页20条"),
            (10, 0, "第1页，每页10条"),
            (5, 0, "第1页，每页5条"),
            (5, 5, "第2页，每页5条"),
        ]
        
        for limit, offset, description in test_cases:
            query = "SELECT id, username, email FROM users ORDER BY id LIMIT $1 OFFSET $2"
            result = await conn.fetch(query, limit, offset)
            print(f"  {description}: 返回 {len(result)} 条记录")
            if result:
                ids = [str(r['id']) for r in result]
                print(f"    用户ID: {', '.join(ids)}")
        
        # 5. 测试搜索功能
        print("\n" + "=" * 50)
        print("🔍 5. 测试搜索功能")
        print("=" * 50)
        
        search_tests = [
            ("test", "搜索包含'test'的用户"),
            ("admin", "搜索包含'admin'的用户"),
            ("@", "搜索包含'@'的邮箱"),
        ]
        
        for search_term, description in search_tests:
            query = """
                SELECT COUNT(*) FROM users 
                WHERE username ILIKE $1 OR email ILIKE $1
            """
            count = await conn.fetchval(query, f"%{search_term}%")
            print(f"  {description}: {count} 个结果")
        
        # 6. 检查索引
        print("\n" + "=" * 50)
        print("🗂️ 6. 检查数据库索引")
        print("=" * 50)
        
        indexes = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'users'
        """)
        
        print("用户表索引:")
        for idx in indexes:
            print(f"  - {idx['indexname']}")
            print(f"    {idx['indexdef']}")
        
        # 7. 检查数据库连接池
        print("\n" + "=" * 50)
        print("🔗 7. 数据库连接信息")
        print("=" * 50)
        
        db_info = await conn.fetchrow("SELECT version(), current_database(), current_user")
        print(f"数据库版本: {db_info['version']}")
        print(f"当前数据库: {db_info['current_database']}")
        print(f"当前用户: {db_info['current_user']}")
        
        await conn.close()
        print("\n✅ 诊断完成，数据库连接已关闭")
        
    except Exception as e:
        print(f"❌ 诊断过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(comprehensive_diagnosis())