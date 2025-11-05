#!/usr/bin/env python3
"""
验证文档在PostgreSQL向量数据库中的存储格式和完整性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.config import get_db_connection
import json
from datetime import datetime

def verify_document_storage():
    """验证文档存储的完整性"""
    try:
        print("=== 验证文档存储完整性 ===\n")
        
        # 使用现有的数据库连接
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                
                # 1. 检查documents表结构
                print("1. 检查documents表结构:")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                for col in columns:
                    nullable = 'NULL' if col[2] == 'YES' else 'NOT NULL'
                    print(f"   {col[0]}: {col[1]} ({nullable})")
                
                # 2. 检查document_chunks表结构
                print("\n2. 检查document_chunks表结构:")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                for col in columns:
                    nullable = 'NULL' if col[2] == 'YES' else 'NOT NULL'
                    print(f"   {col[0]}: {col[1]} ({nullable})")
                
                # 3. 检查数据完整性
                print("\n3. 检查数据完整性:")
                
                # 文档总数
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                print(f"   文档总数: {doc_count}")
                
                # 文档块总数
                cursor.execute("SELECT COUNT(*) FROM document_chunks")
                chunk_count = cursor.fetchone()[0]
                print(f"   文档块总数: {chunk_count}")
                
                # 有向量的文档块数
                cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
                vector_count = cursor.fetchone()[0]
                print(f"   有向量的文档块数: {vector_count}")
                
                # 4. 检查孤立的文档块（没有对应文档记录的块）
                print("\n4. 检查孤立的文档块:")
                cursor.execute("""
                    SELECT dc.document_id, COUNT(*) as chunk_count
                    FROM document_chunks dc
                    LEFT JOIN documents d ON dc.document_id = CAST(d.id AS VARCHAR)
                    WHERE d.id IS NULL
                    GROUP BY dc.document_id
                """)
                orphaned_chunks = cursor.fetchall()
                
                if orphaned_chunks:
                    print(f"   发现 {len(orphaned_chunks)} 个孤立的文档ID:")
                    for doc_id, count in orphaned_chunks:
                        print(f"     文档ID: {doc_id}, 块数: {count}")
                        
                        # 查看这些孤立块的详细信息
                        cursor.execute("""
                            SELECT id, content, metadata, created_at
                            FROM document_chunks 
                            WHERE document_id = %s 
                            LIMIT 1
                        """, (doc_id,))
                        chunk_info = cursor.fetchone()
                        if chunk_info:
                            metadata = chunk_info[2]
                            if isinstance(metadata, str):
                                try:
                                    metadata = json.loads(metadata)
                                except:
                                    pass
                            print(f"       示例块ID: {chunk_info[0]}")
                            content_preview = str(chunk_info[1])[:100] if chunk_info[1] else "无内容"
                            print(f"       内容预览: {content_preview}...")
                            print(f"       元数据: {metadata}")
                            print(f"       创建时间: {chunk_info[3]}")
                else:
                    print("   没有发现孤立的文档块")
                
                # 5. 检查文档记录但没有块的情况
                print("\n5. 检查有文档记录但没有块的情况:")
                cursor.execute("""
                    SELECT d.id, d.filename, d.status
                    FROM documents d
                    LEFT JOIN document_chunks dc ON CAST(d.id AS VARCHAR) = dc.document_id
                    WHERE dc.document_id IS NULL
                """)
                docs_without_chunks = cursor.fetchall()
                
                if docs_without_chunks:
                    print(f"   发现 {len(docs_without_chunks)} 个没有块的文档:")
                    for doc_id, filename, status in docs_without_chunks:
                        print(f"     文档ID: {doc_id}, 文件名: {filename}, 状态: {status}")
                else:
                    print("   所有文档都有对应的块")
                
                # 6. 检查向量维度一致性
                print("\n6. 检查向量维度一致性:")
                cursor.execute("""
                    SELECT 
                        vector_dims(embedding) as dimension,
                        COUNT(*) as count
                    FROM document_chunks 
                    WHERE embedding IS NOT NULL
                    GROUP BY vector_dims(embedding)
                """)
                dimensions = cursor.fetchall()
                
                if dimensions:
                    print("   向量维度分布:")
                    for dim, count in dimensions:
                        print(f"     {dim}维: {count}个块")
                else:
                    print("   没有找到向量数据")
                
                # 7. 检查最近的文档块样本
                print("\n7. 最近的文档块样本:")
                cursor.execute("""
                    SELECT 
                        dc.id,
                        dc.document_id,
                        dc.content,
                        dc.metadata,
                        dc.created_at,
                        vector_dims(dc.embedding) as vector_dim
                    FROM document_chunks dc
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.created_at DESC
                    LIMIT 3
                """)
                recent_chunks = cursor.fetchall()
                
                for i, chunk in enumerate(recent_chunks, 1):
                    chunk_id, doc_id, content, metadata, created_at, vector_dim = chunk
                    
                    # 解析元数据
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            pass
                    
                    print(f"   样本 {i}:")
                    print(f"     块ID: {chunk_id}")
                    print(f"     文档ID: {doc_id}")
                    print(f"     向量维度: {vector_dim}")
                    content_preview = str(content)[:100] if content else "无内容"
                    print(f"     内容: {content_preview}...")
                    print(f"     元数据: {metadata}")
                    print(f"     创建时间: {created_at}")
                    print()
        
        print("文档存储验证完成")
        
    except Exception as e:
        print(f"验证失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_document_storage()