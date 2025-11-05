#!/usr/bin/env python3
"""
修复document_chunks表的embedding列维度
"""
from database.config import get_db_connection

def fix_embedding_dimension():
    """修复embedding列维度为2560"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                print("开始修复embedding列维度...")
                
                # 删除现有的embedding列
                cursor.execute("""
                ALTER TABLE document_chunks 
                DROP COLUMN IF EXISTS embedding
                """)
                print("删除现有embedding列")
                
                # 添加新的embedding列 (2560维度)
                cursor.execute("""
                ALTER TABLE document_chunks 
                ADD COLUMN embedding VECTOR(2560)
                """)
                print("添加新的embedding列 (2560维度)")
                
                # 提交更改
                conn.commit()
                print("数据库更改已提交")
                
    except Exception as e:
        print(f"修复embedding列维度失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_embedding_dimension()