#!/usr/bin/env python3
"""
修复document_chunks表结构 - 将document_id改为VARCHAR类型
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
    print('🔧 修复document_chunks表结构...')
    
    # 检查当前表结构
    cursor.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'document_chunks' AND column_name = 'document_id'
    """)
    current_type = cursor.fetchone()[0]
    print(f'当前document_id字段类型: {current_type}')
    
    if current_type == 'integer':
        print('需要修改字段类型为VARCHAR...')
        
        # 备份现有数据（如果有的话）
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]
        print(f'当前表中有 {count} 条记录')
        
        if count > 0:
            print('⚠️  表中有数据，先清空表...')
            cursor.execute("DELETE FROM document_chunks")
            print('✅ 表已清空')
        
        # 修改字段类型
        cursor.execute("""
            ALTER TABLE document_chunks 
            ALTER COLUMN document_id TYPE VARCHAR(255)
        """)
        
        conn.commit()
        print('✅ document_id字段类型已修改为VARCHAR(255)')
        
        # 验证修改结果
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'document_id'
        """)
        new_type = cursor.fetchone()[0]
        print(f'修改后document_id字段类型: {new_type}')
        
    else:
        print('✅ document_id字段类型已经是VARCHAR，无需修改')
    
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