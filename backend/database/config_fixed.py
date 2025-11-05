"""
数据库配置模块
包含PostgreSQL连接配置和连接池管理
"""

import os
import asyncpg
import asyncio
import psycopg2
import psycopg2.pool
from typing import Optional
from contextlib import asynccontextmanager, contextmanager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        # 从环境变量获取数据库配置，提供默认值
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'weplus_rag')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        
        # 连接池配置
        self.min_connections = int(os.getenv('DB_MIN_CONNECTIONS', '5'))
        self.max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '20'))
        self.connection_timeout = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
        
        # 连接池实例
        self._pool: Optional[asyncpg.Pool] = None
    
    @property
    def connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    async def create_pool(self) -> asyncpg.Pool:
        """创建数据库连接池"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    command_timeout=self.connection_timeout,
                    server_settings={
                        'application_name': 'rag_system',
                        'timezone': 'UTC'
                    }
                )
                logger.info(f"数据库连接池创建成功: {self.host}:{self.port}/{self.database}")
            except Exception as e:
                logger.error(f"创建数据库连接池失败: {e}")
                raise
        return self._pool
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("数据库连接池已关闭")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if self._pool is None:
            await self.create_pool()
        
        async with self._pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"数据库操作错误: {e}")
                raise
    
    async def execute_query(self, query: str, *args):
        """执行查询语句"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """执行命令语句（INSERT, UPDATE, DELETE）"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def execute_many(self, command: str, args_list):
        """批量执行命令"""
        async with self.get_connection() as conn:
            return await conn.executemany(command, args_list)
    
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.info("数据库连接测试成功")
                    return True
                else:
                    logger.error("数据库连接测试失败")
                    return False
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    async def check_pgvector_extension(self) -> bool:
        """检查pgvector扩展是否已安装"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                if result:
                    logger.info("pgvector扩展已安装")
                    return True
                else:
                    logger.warning("pgvector扩展未安装")
                    return False
        except Exception as e:
            logger.error(f"检查pgvector扩展失败: {e}")
            return False
    
    async def get_database_stats(self) -> dict:
        """获取数据库统计信息"""
        try:
            async with self.get_connection() as conn:
                # 获取表统计信息
                tables_stats = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    ORDER BY tablename
                """)
                
                # 获取数据库大小
                db_size = await conn.fetchval(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                )
                
                # 获取连接数
                connections = await conn.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                )
                
                return {
                    'database_size': db_size,
                    'active_connections': connections,
                    'tables_stats': [dict(row) for row in tables_stats]
                }
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {e}")
            return {}

# 全局数据库配置实例
db_config = DatabaseConfig()

# 同步数据库连接池（用于兼容性）
_sync_connection_pool = None

def init_sync_connection_pool():
    """初始化同步数据库连接池"""
    global _sync_connection_pool
    if _sync_connection_pool is None:
        try:
            _sync_connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=db_config.min_connections,
                maxconn=db_config.max_connections,
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.user,
                password=db_config.password
            )
            logger.info("同步数据库连接池创建成功")
        except Exception as e:
            logger.error(f"创建同步数据库连接池失败: {e}")
            raise
    return _sync_connection_pool

@contextmanager
def get_db_connection():
    """获取同步数据库连接（用于兼容性）"""
    if _sync_connection_pool is None:
        init_sync_connection_pool()
    
    conn = None
    try:
        conn = _sync_connection_pool.getconn()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"数据库操作错误: {e}")
        raise
    finally:
        if conn:
            _sync_connection_pool.putconn(conn)

def execute_query(query: str, params=None):
    """执行同步查询"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

def execute_command(command: str, params=None):
    """执行同步命令"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(command, params)
            conn.commit()
            return cursor.rowcount

# 便捷函数
async def init_database():
    """初始化数据库连接"""
    await db_config.create_pool()
    
    # 测试连接
    if not await db_config.test_connection():
        raise Exception("数据库连接失败")
    
    # 检查pgvector扩展
    if not await db_config.check_pgvector_extension():
        logger.warning("请确保已安装pgvector扩展")

async def close_database():
    """关闭数据库连接"""
    await db_config.close_pool()

# 数据库操作装饰器
def with_db_connection(func):
    """数据库连接装饰器"""
    async def wrapper(*args, **kwargs):
        async with db_config.get_connection() as conn:
            return await func(conn, *args, **kwargs)
    return wrapper

if __name__ == "__main__":
    # 测试数据库配置
    async def test_db():
        await init_database()
        stats = await db_config.get_database_stats()
        print("数据库统计信息:", stats)
        await close_database()
    
    asyncio.run(test_db())