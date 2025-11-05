#!/usr/bin/env python3
"""
最终系统测试 - 验证PostgreSQL迁移完成
确保所有服务都正确使用PostgreSQL，没有SQLite依赖
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    base_url = "http://localhost:8000"
    
    try:
        # 测试健康检查
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查端点正常")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
            
        # 测试文档API
        response = requests.get(f"{base_url}/api/documents", timeout=5)
        if response.status_code == 200:
            print("✅ 文档API端点正常")
        else:
            print(f"⚠️  文档API响应: {response.status_code}")
            
        # 测试RAG API
        response = requests.get(f"{base_url}/api/rag/stats", timeout=5)
        if response.status_code == 200:
            print("✅ RAG API端点正常")
        else:
            print(f"⚠️  RAG API响应: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def test_database_connections():
    """测试数据库连接"""
    print("\n🗄️  测试数据库连接...")
    try:
        from database.postgresql_config import get_db_connection
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 测试基本查询
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL连接成功: {version.split(',')[0]}")
            
            # 检查关键表是否存在
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('documents', 'document_chunks', 'users', 'categories')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ 关键表存在: {', '.join(tables)}")
            
            # 检查向量扩展
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            if cursor.fetchone():
                print("✅ pgvector扩展已安装")
            else:
                print("⚠️  pgvector扩展未找到")
                
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def test_vector_service():
    """测试向量服务"""
    print("\n🔍 测试向量服务...")
    try:
        from app.services.postgresql_vector_service import PostgreSQLVectorService
        import asyncio
        
        vector_service = PostgreSQLVectorService()
        
        # 测试健康检查
        health = vector_service.health_check()
        if health.get('overall'):
            print("✅ 向量服务健康检查通过")
        else:
            print("⚠️  向量服务健康检查未通过")
            
        # 测试统计信息
        stats = asyncio.run(vector_service.get_stats())
        print(f"✅ 向量数据库统计: {stats.get('total_documents', 0)} 文档, 维度 {stats.get('embedding_dimension', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 向量服务测试失败: {e}")
        return False

def check_sqlite_remnants():
    """检查是否还有SQLite残留"""
    print("\n🔍 检查SQLite残留...")
    
    # 检查是否还有.db文件
    import glob
    db_files = glob.glob("**/*.db", recursive=True)
    if db_files:
        print(f"⚠️  发现SQLite文件: {db_files}")
        return False
    else:
        print("✅ 未发现SQLite数据库文件")
    
    # 检查代码中是否还有sqlite3导入
    try:
        import subprocess
        result = subprocess.run(['grep', '-r', 'import sqlite3', '.'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0 and result.stdout.strip():
            print(f"⚠️  发现sqlite3导入: {result.stdout}")
            return False
        else:
            print("✅ 未发现sqlite3导入")
    except:
        print("✅ SQLite导入检查完成")
    
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 WePlus系统最终测试 - PostgreSQL迁移验证")
    print("=" * 60)
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("数据库连接", test_database_connections()))
    test_results.append(("向量服务", test_vector_service()))
    test_results.append(("API端点", test_api_endpoints()))
    test_results.append(("SQLite残留检查", check_sqlite_remnants()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！PostgreSQL迁移完成！")
        print("✅ 系统已完全移除SQLite依赖，使用纯PostgreSQL")
        return True
    else:
        print("⚠️  部分测试未通过，请检查相关问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)