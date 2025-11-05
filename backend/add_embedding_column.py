#!/usr/bin/env python3
"""
为document_chunks表添加embedding列
"""
from database.config import get_db_connection

def add_embedding_column():
    """为document_chunks表添加embedding列"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                print("开始为document_chunks表添加embedding列...")
                
                # 检查embedding列是否已存在
                cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'document_chunks' AND column_name = 'embedding'
                """)
                
                if cursor.fetchone():
                    print("embedding列已存在，无需添加")
                    return
                
                # 添加embedding列 (使用2560维度，对应豆包嵌入模型)
                cursor.execute("""
                ALTER TABLE document_chunks 
                ADD COLUMN embedding VECTOR(2560)
                """)
                
                print("embedding列添加成功")
                
                # 创建向量索引 (先跳过，因为可能有维度限制)
                try:
                    cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
                    ON document_chunks USING hnsw (embedding vector_cosine_ops)
                    """)
                    print("向量索引创建成功")
                except Exception as idx_error:
                    print(f"向量索引创建失败，但这不影响基本功能: {idx_error}")
                    # 尝试创建普通索引
                    try:
                        cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_btree 
                        ON document_chunks (embedding)
                        """)
                        print("普通索引创建成功")
                    except Exception as btree_error:
                        print(f"普通索引也创建失败: {btree_error}")
                
                # 提交更改
                conn.commit()
                print("数据库更改已提交")
                
    except Exception as e:
        print(f"添加embedding列失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_embedding_column()