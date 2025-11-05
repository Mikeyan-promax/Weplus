#!/usr/bin/env python3
"""
添加login_count列到users表
"""

import psycopg2
from database.config import get_db_connection

def add_login_count_column():
    """添加login_count列到users表"""
    try:
        with get_db_connection() as conn, conn.cursor() as cursor:
            # 检查login_count列是否存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'login_count'
            """)
            
            if not cursor.fetchone():
                print('添加login_count列...')
                cursor.execute('ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0')
                conn.commit()
                print('✅ login_count列添加成功')
            else:
                print('✅ login_count列已存在')
                
            # 验证列是否存在
            cursor.execute('SELECT login_count FROM users LIMIT 1')
            print('✅ login_count列验证成功')
            
    except Exception as e:
        print(f'❌ 错误: {e}')
        return False
    
    return True

if __name__ == "__main__":
    add_login_count_column()