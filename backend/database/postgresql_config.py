"""
PostgreSQL数据库配置
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# 数据库连接配置 - 阿里云RDS PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'pgm-2zekusmdjl0o3782ao.pg.rds.aliyuncs.com'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'weplus_db'),
    'user': os.getenv('DB_USER', 'weplus_db'),
    'password': os.getenv('DB_PASSWORD', '123456yzlA'),
    'client_encoding': 'utf8'
}

# 全局连接池
connection_pool = None

def init_connection_pool(minconn=1, maxconn=20):
    """初始化连接池"""
    global connection_pool
    try:
        if connection_pool is None:
            # 使用连接字符串方式，对密码进行URL编码避免编码问题
            password_encoded = quote_plus(DB_CONFIG['password'])
            dsn = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['database']} user={DB_CONFIG['user']} password={password_encoded} client_encoding=utf8"
            connection_pool = SimpleConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                dsn=dsn
            )
            logger.info("PostgreSQL连接池初始化成功")
        return connection_pool
    except Exception as e:
        logger.error(f"连接池初始化失败: {e}")
        raise

def get_db_connection():
    """获取数据库连接"""
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.getconn()

def return_db_connection(conn):
    """归还数据库连接"""
    if connection_pool and conn:
        connection_pool.putconn(conn)

def close_connection_pool():
    """关闭连接池"""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
        logger.info("连接池已关闭")

class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
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
                        return cursor
                else:
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"查询执行失败: {e}")
            raise
        finally:
            if conn:
                return_db_connection(conn)
    
    @staticmethod
    def execute_transaction(queries):
        """执行事务"""
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for query, params in queries:
                    cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"事务执行失败: {e}")
            raise
        finally:
            if conn:
                return_db_connection(conn)

# 便捷函数
def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """执行查询的便捷函数"""
    return DatabaseManager.execute_query(query, params, fetch_one, fetch_all)

def execute_transaction(queries):
    """执行事务的便捷函数"""
    return DatabaseManager.execute_transaction(queries)
