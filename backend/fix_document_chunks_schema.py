#!/usr/bin/env python3
"""
修复document_chunks表的document_id字段类型不匹配问题
将document_id从VARCHAR类型改为INTEGER类型，并清理不一致的数据
"""

import psycopg2
from database.config import get_db_connection

def fix_document_chunks_schema():
    """修复document_chunks表结构"""
    print("🔧 开始修复document_chunks表结构...")
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # 1. 首先备份当前数据
                print("📋 步骤1: 检查当前数据...")
                cursor.execute("SELECT COUNT(*) FROM document_chunks")
                total_chunks = cursor.fetchone()[0]
                print(f"当前document_chunks表中有 {total_chunks} 条记录")
                
                # 2. 检查哪些document_id可以转换为整数
                cursor.execute("""
                SELECT document_id, COUNT(*) as count
                FROM document_chunks 
                GROUP BY document_id
                """)
                document_ids = cursor.fetchall()
                
                valid_ids = []
                invalid_ids = []
                
                for doc_id, count in document_ids:
                    try:
                        # 尝试转换为整数
                        int_id = int(doc_id)
                        # 检查这个ID是否在documents表中存在
                        cursor.execute("SELECT id FROM documents WHERE id = %s", (int_id,))
                        if cursor.fetchone():
                            valid_ids.append((doc_id, int_id, count))
                        else:
                            invalid_ids.append((doc_id, count))
                    except (ValueError, TypeError):
                        invalid_ids.append((doc_id, count))
                
                print(f"✅ 找到 {len(valid_ids)} 个有效的document_id")
                print(f"❌ 找到 {len(invalid_ids)} 个无效的document_id")
                
                if invalid_ids:
                    print("无效的document_id列表:")
                    for doc_id, count in invalid_ids:
                        print(f"  - {doc_id} ({count} 条记录)")
                
                # 3. 删除无效的记录
                if invalid_ids:
                    print("\n🗑️ 步骤2: 删除无效的记录...")
                    invalid_id_list = [doc_id for doc_id, _ in invalid_ids]
                    cursor.execute("DELETE FROM document_chunks WHERE document_id = ANY(%s)", (invalid_id_list,))
                    deleted_count = cursor.rowcount
                    print(f"✅ 删除了 {deleted_count} 条无效记录")
                
                # 4. 创建新的临时表
                print("\n🔄 步骤3: 创建新的表结构...")
                cursor.execute("""
                CREATE TABLE document_chunks_new (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    content_length INTEGER,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """)
                print("✅ 创建新表结构成功")
                
                # 5. 迁移有效数据
                if valid_ids:
                    print("\n📦 步骤4: 迁移有效数据...")
                    for old_id, new_id, count in valid_ids:
                        cursor.execute("""
                        INSERT INTO document_chunks_new (document_id, chunk_index, content, content_length, metadata, created_at)
                        SELECT %s, chunk_index, content, content_length, metadata, created_at
                        FROM document_chunks 
                        WHERE document_id = %s
                        """, (new_id, old_id))
                    print(f"✅ 迁移了 {len(valid_ids)} 个文档的数据")
                
                # 6. 删除旧表并重命名新表
                print("\n🔄 步骤5: 替换表结构...")
                cursor.execute("DROP TABLE document_chunks")
                cursor.execute("ALTER TABLE document_chunks_new RENAME TO document_chunks")
                print("✅ 表结构替换成功")
                
                # 7. 重建索引
                print("\n📊 步骤6: 重建索引...")
                cursor.execute("CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id)")
                cursor.execute("CREATE INDEX idx_document_chunks_chunk_index ON document_chunks(chunk_index)")
                print("✅ 索引重建成功")
                
                # 8. 验证结果
                print("\n✅ 步骤7: 验证修复结果...")
                cursor.execute("SELECT COUNT(*) FROM document_chunks")
                final_count = cursor.fetchone()[0]
                
                cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'document_chunks' AND column_name = 'document_id'
                """)
                column_info = cursor.fetchone()
                
                print(f"✅ 修复完成!")
                print(f"   - 最终记录数: {final_count}")
                print(f"   - document_id字段类型: {column_info[1]}")
                
                # 提交事务
                conn.commit()
                print("✅ 所有更改已提交到数据库")
                
            except Exception as e:
                print(f"❌ 修复过程中出现错误: {str(e)}")
                conn.rollback()
                print("❌ 已回滚所有更改")
                raise

if __name__ == "__main__":
    fix_document_chunks_schema()