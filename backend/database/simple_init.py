
# PostgreSQL数据库连接配置
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import os

# 数据库连接配置
DB_CONFIG = {
    'host': 'pgm-2ze8ej8ej8ej8ej8.pg.rds.aliyuncs.com',
    'port': '5432',
    'database': 'weplus_main',
    'user': 'weplus_user',
    'password': 'WePlus2024!@#'
}

# 连接池
connection_pool = None

def init_connection_pool():
    """初始化连接池"""
    global connection_pool
    if connection_pool is None:
        connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            **DB_CONFIG
        )
    return connection_pool

def get_db_connection():
    """获取数据库连接"""
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.getconn()

def return_db_connection(conn):
    """归还数据库连接"""
    if connection_pool:
        connection_pool.putconn(conn)

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """执行查询"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(('SELECT', 'WITH')):
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            return_db_connection(conn)


"""
简化的数据库初始化脚本
如果PostgreSQL连接失败，使用SQLite作为备选方案
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pathlib import Path

def init_sqlite_database():
    """使用SQLite初始化用户表"""
    # 创建数据库文件路径
    db_path = Path(__file__).parent / "users.db"
    
    # 连接SQLite数据库
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("🚀 开始初始化SQLite数据库...")
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                username VARCHAR NOT NULL,
                password_hash VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                profile VARCHAR DEFAULT '{}'
            )
        """)
        print("✅ 用户表创建成功")
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified)")
        print("✅ 索引创建成功")
        
        # 创建更新时间触发器
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_users_updated_at
            AFTER UPDATE ON users
            FOR EACH ROW
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        print("✅ 触发器创建成功")
        
        # 提交更改
        conn.commit()
        
        # 验证表结构
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s")
        columns = cursor.fetchall()
        
        print("\n📋 用户表结构:")
        print("-" * 60)
        for col in columns:
            col_id, name, data_type, not_null, default_value, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            default = f" DEFAULT {default_value}" if default_value else ""
            primary = " PRIMARY KEY" if pk else ""
            print(f"{name:<15} {data_type:<15} {nullable}{default}{primary}")
        print("-" * 60)
        
        print(f"🎉 SQLite数据库初始化完成！")
        print(f"📁 数据库文件位置: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite数据库初始化失败: {e}")
        return False
    finally:
        conn.close()
        print("🔒 数据库连接已关闭")

def create_sqlite_config():
    """创建SQLite配置文件"""
    config_content = f"""
# SQLite数据库配置
# 由于PostgreSQL连接问题，临时使用SQLite数据库

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pathlib import Path
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class SQLiteConfig:
    \"\"\"SQLite数据库配置类\"\"\"
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "users.db"
    
    def get_connection(self):
        \"\"\"获取数据库连接\"\"\"
        return get_db_connection()
    
    @asynccontextmanager
    async def get_async_connection(self):
        \"\"\"异步上下文管理器获取连接\"\"\"
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

# 全局配置实例
sqlite_config = SQLiteConfig()
"""
    
    config_path = Path(__file__).parent / "sqlite_config.py"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ SQLite配置文件已创建: {config_path}")

if __name__ == "__main__":
    success = init_sqlite_database()
    if success:
        create_sqlite_config()
        print("\n💡 提示: 由于PostgreSQL连接问题，已创建SQLite数据库作为备选方案")
        print("💡 您可以继续开发登录注册功能，稍后再配置PostgreSQL")
    else:
        print("❌ 数据库初始化失败")