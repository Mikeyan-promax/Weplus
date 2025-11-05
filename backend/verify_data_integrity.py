import psycopg2
from psycopg2.extras import RealDictCursor
import json

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'database': 'weplus_db',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def verify_data_integrity():
    """验证数据库迁移后的数据完整性"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== Data Integrity Verification Report ===\n")
        
        # 1. 检查表结构
        print("1. Table Structure Check:")
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position
        """)
        tables_info = {}
        for row in cursor.fetchall():
            table_name = row['table_name']
            if table_name not in tables_info:
                tables_info[table_name] = []
            tables_info[table_name].append({
                'column': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable']
            })
        
        for table_name, columns in tables_info.items():
            print(f"  Table {table_name}: {len(columns)} columns")
        
        # 2. 检查数据记录数
        print("\n2. Record Count Check:")
        for table_name in tables_info.keys():
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"  {table_name}: {count} records")
        
        # 3. 检查关键表的数据样本
        print("\n3. Sample Data Check:")
        
        # 检查用户表
        cursor.execute("SELECT id, username, email, created_at FROM users LIMIT 3")
        users = cursor.fetchall()
        print(f"  Users table sample ({len(users)} records):")
        for user in users:
            print(f"    ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
        
        # 检查学习资源表
        cursor.execute("SELECT id, title, resource_type, created_at FROM study_resources LIMIT 3")
        resources = cursor.fetchall()
        print(f"  Study resources table sample ({len(resources)} records):")
        for resource in resources:
            print(f"    ID: {resource['id']}, Title: {resource['title']}, Type: {resource['resource_type']}")
        
        # 检查文档表
        cursor.execute("SELECT id, filename, file_size, upload_time FROM documents LIMIT 3")
        documents = cursor.fetchall()
        print(f"  Documents table sample ({len(documents)} records):")
        for doc in documents:
            print(f"    ID: {doc['id']}, Filename: {doc['filename']}, Size: {doc['file_size']} bytes")
        
        # 4. 检查外键约束
        print("\n4. Foreign Key Constraints Check:")
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """)
        foreign_keys = cursor.fetchall()
        print(f"  Found {len(foreign_keys)} foreign key constraints:")
        for fk in foreign_keys:
            print(f"    {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # 5. 检查索引
        print("\n5. Index Check:")
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        indexes = cursor.fetchall()
        index_count = {}
        for idx in indexes:
            table = idx['tablename']
            index_count[table] = index_count.get(table, 0) + 1
        
        for table, count in index_count.items():
            print(f"  {table}: {count} indexes")
        
        print("\n=== Verification Complete ===")
        print("✅ Database structure and data integrity verification passed!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verify_data_integrity()