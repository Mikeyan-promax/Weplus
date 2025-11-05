#!/usr/bin/env python3
"""
修复document_chunks表的外键约束问题
"""
import psycopg2
from urllib.parse import quote_plus

DB_CONFIG = {
    'host': 'pgm-2ze58b40mdfqec4zwo.pg.rds.aliyuncs.com',
    'port': '5432',
    'database': 'weplus_db',
    'user': 'weplus_db',
    'password': '123456yzlA'
}

password_encoded = quote_plus(DB_CONFIG['password'])
dsn = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['database']} user={DB_CONFIG['user']} password={password_encoded} client_encoding=utf8"

conn = psycopg2.connect(dsn)
with conn.cursor() as cursor:
    print('🔧 检查和修复document_chunks表的约束...')
    
    # 检查外键约束
    cursor.execute("""
        SELECT 
            tc.constraint_name, 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name='document_chunks'
    """)
    constraints = cursor.fetchall()
    
    print('当前外键约束:')
    for constraint in constraints:
        print(f'  - {constraint[0]}: {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}')
    
    # 删除外键约束
    for constraint in constraints:
        constraint_name = constraint[0]
        print(f'删除外键约束: {constraint_name}')
        cursor.execute(f"ALTER TABLE document_chunks DROP CONSTRAINT {constraint_name}")
    
    # 修改字段类型
    print('修改document_id字段类型为VARCHAR(255)...')
    cursor.execute("""
        ALTER TABLE document_chunks 
        ALTER COLUMN document_id TYPE VARCHAR(255)
    """)
    
    conn.commit()
    print('✅ 字段类型修改成功')
    
    # 验证修改结果
    cursor.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks' AND column_name = 'document_id'
    """)
    new_type = cursor.fetchone()[0]
    print(f'修改后document_id字段类型: {new_type}')
    
    # 检查完整的表结构
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks' 
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    print('\n修复后的document_chunks表结构:')
    for col in columns:
        print(f'  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})')

conn.close()
print('\n🎉 表结构修复完成！')