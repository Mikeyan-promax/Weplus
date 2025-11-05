#!/usr/bin/env python3
"""
修复向量搜索中的类型转换问题
"""

import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_vector_search_with_proper_casting():
    """测试正确的向量搜索类型转换"""
    print("=== 测试向量搜索类型转换 ===")
    
    try:
        # 连接数据库
        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            client_encoding='utf8'
        )
        
        with conn.cursor() as cursor:
            # 创建一个测试向量（2560维，全为0.1）
            test_vector = [0.1] * 2560
            
            print(f"测试向量维度: {len(test_vector)}")
            
            # 方法1: 使用CAST转换
            print("\n方法1: 使用CAST转换")
            search_query1 = """
                SELECT 
                    dc.document_id,
                    dc.content,
                    1 - (dc.embedding <=> CAST(%s AS vector)) as similarity
                FROM document_chunks dc
                WHERE embedding IS NOT NULL
                ORDER BY dc.embedding <=> CAST(%s AS vector)
                LIMIT 3
            """
            
            cursor.execute(search_query1, (test_vector, test_vector))
            results1 = cursor.fetchall()
            
            print(f"✓ CAST方法成功，找到 {len(results1)} 个结果")
            
            for i, (doc_id, content, similarity) in enumerate(results1):
                print(f"  {i+1}. 文档ID: {doc_id}")
                print(f"     相似度: {similarity:.4f}")
                print(f"     内容: {content[:100]}...")
                print()
            
            # 方法2: 使用::vector转换
            print("方法2: 使用::vector转换")
            search_query2 = """
                SELECT 
                    dc.document_id,
                    dc.content,
                    1 - (dc.embedding <=> %s::vector) as similarity
                FROM document_chunks dc
                WHERE embedding IS NOT NULL
                ORDER BY dc.embedding <=> %s::vector
                LIMIT 3
            """
            
            cursor.execute(search_query2, (test_vector, test_vector))
            results2 = cursor.fetchall()
            
            print(f"✓ ::vector方法成功，找到 {len(results2)} 个结果")
            
            # 测试带阈值的搜索
            print("\n方法3: 带阈值的搜索")
            threshold = 0.5
            search_query3 = """
                SELECT 
                    dc.document_id,
                    dc.content,
                    1 - (dc.embedding <=> %s::vector) as similarity
                FROM document_chunks dc
                WHERE embedding IS NOT NULL 
                AND 1 - (dc.embedding <=> %s::vector) > %s
                ORDER BY dc.embedding <=> %s::vector
                LIMIT 5
            """
            
            cursor.execute(search_query3, (test_vector, test_vector, threshold, test_vector))
            results3 = cursor.fetchall()
            
            print(f"✓ 阈值搜索成功，阈值 {threshold}，找到 {len(results3)} 个结果")
            
            # 测试不同阈值
            print("\n测试不同阈值:")
            thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
            
            for threshold in thresholds:
                cursor.execute(search_query3, (test_vector, test_vector, threshold, test_vector))
                results = cursor.fetchall()
                print(f"  阈值 {threshold}: {len(results)} 个结果")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 向量搜索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_postgresql_vector_service():
    """更新PostgreSQL向量服务代码"""
    print("\n=== 更新PostgreSQL向量服务代码 ===")
    
    service_file = "app/services/postgresql_vector_service.py"
    
    try:
        # 读取当前文件
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找需要修复的搜索查询
        old_query = '''search_query = """
                        SELECT 
                            dc.document_id,
                            dc.content,
                            dc.metadata,
                            1 - (dc.embedding <=> %s) as similarity
                        FROM document_chunks dc
                        WHERE 1 - (dc.embedding <=> %s) > %s
                        ORDER BY dc.embedding <=> %s
                        LIMIT %s
                    """"'''
        
        new_query = '''search_query = """
                        SELECT 
                            dc.document_id,
                            dc.content,
                            dc.metadata,
                            1 - (dc.embedding <=> %s::vector) as similarity
                        FROM document_chunks dc
                        WHERE 1 - (dc.embedding <=> %s::vector) > %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """"'''
        
        # 替换查询
        if "dc.embedding <=> %s) as similarity" in content and "::vector" not in content:
            # 更精确的替换
            content = content.replace(
                "1 - (dc.embedding <=> %s) as similarity",
                "1 - (dc.embedding <=> %s::vector) as similarity"
            )
            content = content.replace(
                "WHERE 1 - (dc.embedding <=> %s) > %s",
                "WHERE 1 - (dc.embedding <=> %s::vector) > %s"
            )
            content = content.replace(
                "ORDER BY dc.embedding <=> %s",
                "ORDER BY dc.embedding <=> %s::vector"
            )
            
            # 写回文件
            with open(service_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ 已更新 {service_file}")
            return True
        else:
            print(f"✓ {service_file} 已经包含正确的类型转换")
            return True
            
    except Exception as e:
        print(f"✗ 更新 {service_file} 失败: {e}")
        return False

if __name__ == "__main__":
    print("开始修复向量搜索类型转换问题...")
    
    # 1. 测试向量搜索
    if test_vector_search_with_proper_casting():
        print("\n向量搜索测试成功！")
        
        # 2. 更新服务代码
        if update_postgresql_vector_service():
            print("\n✓ 向量搜索修复完成！")
        else:
            print("\n✗ 服务代码更新失败")
    else:
        print("\n✗ 向量搜索测试失败")
    
    print("\n修复完成！")