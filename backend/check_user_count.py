#!/usr/bin/env python3
"""
查询系统中用户数量的脚本
使用claude-4-sonnet深度思考模式分析用户数据
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def get_user_statistics():
    """获取用户统计信息"""
    
    # 数据库连接配置
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'weplus_rag'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    try:
        print("🔍 正在连接数据库...")
        print(f"📍 连接信息: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # 建立数据库连接
        conn = await asyncpg.connect(**db_config)
        
        print("✅ 数据库连接成功！")
        print("=" * 60)
        
        # 1. 检查用户表是否存在
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            )
        """)
        
        if not table_exists:
            print("❌ 用户表不存在！")
            return
            
        print("✅ 用户表存在")
        
        # 2. 获取总用户数
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"👥 总用户数: {total_users}")
        
        # 3. 获取活跃用户数
        active_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
        print(f"🟢 活跃用户数: {active_users}")
        
        # 4. 获取已验证用户数
        verified_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_verified = true")
        print(f"✅ 已验证用户数: {verified_users}")
        
        # 5. 获取最近7天注册的用户数
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_users = await conn.fetchval("""
            SELECT COUNT(*) FROM users 
            WHERE created_at >= $1
        """, seven_days_ago)
        print(f"📅 最近7天注册用户数: {recent_users}")
        
        # 6. 获取最近30天登录的用户数
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_login_users = await conn.fetchval("""
            SELECT COUNT(*) FROM users 
            WHERE last_login >= $1
        """, thirty_days_ago)
        print(f"🔐 最近30天登录用户数: {recent_login_users}")
        
        print("=" * 60)
        
        # 7. 获取用户详细信息（前10个用户）
        if total_users > 0:
            print("📋 用户详细信息（前10个用户）:")
            print("-" * 60)
            
            users = await conn.fetch("""
                SELECT id, username, email, is_active, is_verified, 
                       created_at, last_login
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            for user in users:
                status = "🟢活跃" if user['is_active'] else "🔴非活跃"
                verified = "✅已验证" if user['is_verified'] else "❌未验证"
                last_login = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else "从未登录"
                created = user['created_at'].strftime('%Y-%m-%d %H:%M')
                
                print(f"ID: {user['id']:<3} | {user['username']:<15} | {user['email']:<25}")
                print(f"     状态: {status} {verified} | 创建: {created} | 最后登录: {last_login}")
                print("-" * 60)
        
        # 8. 获取用户表结构信息
        print("\n📊 用户表结构信息:")
        print("-" * 60)
        
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            nullable = "可空" if col['is_nullable'] == 'YES' else "非空"
            default = f" (默认: {col['column_default']})" if col['column_default'] else ""
            print(f"{col['column_name']:<15} | {col['data_type']:<20} | {nullable}{default}")
        
        await conn.close()
        print("\n🔒 数据库连接已关闭")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        print("💡 请确保:")
        print("   1. PostgreSQL服务正在运行")
        print("   2. 数据库配置正确(.env文件)")
        print("   3. 用户表已创建")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始查询用户统计信息...")
    print("🧠 使用claude-4-sonnet深度思考模式分析")
    print("=" * 60)
    
    # 运行查询
    success = asyncio.run(get_user_statistics())
    
    if success:
        print("\n✅ 用户统计查询完成！")
    else:
        print("\n❌ 用户统计查询失败！")
        sys.exit(1)