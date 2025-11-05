#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复向量维度不匹配问题
将document_chunks表的embedding字段从1536维调整为2560维
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgresql_config import get_db_connection, return_db_connection, init_connection_pool
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_vector_dimension():
    """修复向量维度问题"""
    conn = None
    try:
        # 初始化连接池
        init_connection_pool()
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("1. 检查当前表结构...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"当前表有 {len(columns)} 列:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        print("\n2. 检查向量维度...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            AND column_name = 'embedding';
        """)
        embedding_info = cursor.fetchone()
        if embedding_info:
            print(f"当前embedding字段: {embedding_info['data_type']}")
        
        print("\n3. 删除现有表...")
        cursor.execute("DROP TABLE IF EXISTS document_chunks CASCADE;")
        
        print("4. 重新创建表（使用2560维向量）...")
        cursor.execute("""
            CREATE TABLE document_chunks (
                id SERIAL PRIMARY KEY,
                document_id VARCHAR(255) NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR(2560),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_id, chunk_index)
            );
        """)
        
        print("5. 创建索引...")
        cursor.execute("CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);")
        # 注意：PostgreSQL向量索引限制为2000维，2560维向量暂时不创建向量索引
        print("   注意：2560维向量超过PostgreSQL索引限制，跳过向量索引创建")
        
        # 提交事务
        conn.commit()
        
        print("\n6. 验证新表结构...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            ORDER BY ordinal_position;
        """)
        new_columns = cursor.fetchall()
        print(f"新表有 {len(new_columns)} 列:")
        for col in new_columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        print("\n7. 验证向量维度...")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            AND column_name = 'embedding';
        """)
        new_embedding_info = cursor.fetchone()
        if new_embedding_info:
            print(f"新embedding字段: {new_embedding_info['data_type']}")
        
        print("\n✅ 向量维度修复完成! (1536 → 2560)")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            return_db_connection(conn)
    
    return True

if __name__ == "__main__":
    success = fix_vector_dimension()
    if success:
        print("\n🎉 向量维度修复成功，现在可以正常存储2560维的嵌入向量")
    else:
        print("\n💥 向量维度修复失败，请检查错误信息")