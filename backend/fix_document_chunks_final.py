#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复document_chunks表的最终脚本
使用正确的数据库连接配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgresql_config import get_db_connection, return_db_connection, init_connection_pool
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_document_chunks_table():
    """修复document_chunks表"""
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
        
        print("\n2. 检查表中数据数量...")
        cursor.execute("SELECT COUNT(*) as count FROM document_chunks;")
        count = cursor.fetchone()['count']
        print(f"表中有 {count} 行数据")
        
        if count > 0:
            print("\n3. 查看前3行数据...")
            cursor.execute("SELECT document_id, chunk_index, content FROM document_chunks LIMIT 3;")
            rows = cursor.fetchall()
            for i, row in enumerate(rows, 1):
                print(f"  行 {i}: document_id={row['document_id']}, chunk_index={row['chunk_index']}")
                content_preview = row['content'][:50] + "..." if len(row['content']) > 50 else row['content']
                print(f"         content={content_preview}")
        
        print("\n4. 删除现有表...")
        cursor.execute("DROP TABLE IF EXISTS document_chunks CASCADE;")
        
        print("5. 重新创建表...")
        cursor.execute("""
            CREATE TABLE document_chunks (
                id SERIAL PRIMARY KEY,
                document_id VARCHAR(255) NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR(1536),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_id, chunk_index)
            );
        """)
        
        print("6. 创建索引...")
        cursor.execute("CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);")
        cursor.execute("CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);")
        
        # 提交事务
        conn.commit()
        
        print("\n7. 验证新表结构...")
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
        
        print("\n✅ document_chunks表修复完成!")
        
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
    success = fix_document_chunks_table()
    if success:
        print("\n🎉 表修复成功，可以继续测试文档上传功能")
    else:
        print("\n💥 表修复失败，请检查错误信息")