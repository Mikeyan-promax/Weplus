
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
    """SQLite数据库配置类"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "users.db"
    
    def get_connection(self):
        """获取数据库连接"""
        return get_db_connection())
    
    @asynccontextmanager
    async def get_async_connection(self):
        """异步上下文管理器获取连接"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

# 全局配置实例
sqlite_config = SQLiteConfig()
