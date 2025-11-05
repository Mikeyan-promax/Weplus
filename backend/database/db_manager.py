"""
统一的PostgreSQL数据库连接管理器
替换项目中所有的SQLite连接，提供统一的数据库操作接口
"""

import os
import logging
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import psycopg2.errors
from datetime import datetime
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """PostgreSQL数据库管理器"""
    
    def __init__(self):
        self.pool: Optional[SimpleConnectionPool] = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, str]:
        """从环境变量加载数据库配置"""
        return {
            'host': os.getenv('DB_HOST', 'pgm-2ze58b40mdfqec4zwo.pg.rds.aliyuncs.com'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'weplus_db'),
            'user': os.getenv('DB_USER', 'weplus_db'),
            'password': os.getenv('DB_PASSWORD', '123456yzlA')
        }
    
    def init_pool(self, minconn: int = 1, maxconn: int = 20) -> None:
        """初始化连接池"""
        try:
            if self.pool is None:
                self.pool = SimpleConnectionPool(
                    minconn=minconn,
                    maxconn=maxconn,
                    **self.config
                )
                logger.info(f"PostgreSQL连接池初始化成功: {self.config['host']}:{self.config['port']}/{self.config['database']}")
        except Exception as e:
            logger.error(f"连接池初始化失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if self.pool is None:
            self.init_pool()
        
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库连接错误: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, 
                     query: str, 
                     params: Optional[tuple] = None, 
                     fetch_one: bool = False, 
                     fetch_all: bool = True) -> Union[List[Dict], Dict, int, None]:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否只获取一条记录
            fetch_all: 是否获取所有记录
            
        Returns:
            查询结果或影响的行数
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    cursor.execute(query, params)
                    
                    # 判断是否为查询语句或包含RETURNING子句
                    query_upper = query.strip().upper()
                    if query_upper.startswith(('SELECT', 'WITH')) or 'RETURNING' in query_upper:
                        if fetch_one:
                            result = cursor.fetchone()
                            return dict(result) if result else None
                        elif fetch_all:
                            results = cursor.fetchall()
                            return [dict(row) for row in results]
                        else:
                            return cursor
                    else:
                        # 对于INSERT, UPDATE, DELETE等语句
                        conn.commit()
                        return cursor.rowcount
                        
                except Exception as e:
                    conn.rollback()
                    logger.error(f"查询执行失败: {query[:100]}... 错误: {e}")
                    raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行SQL语句"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return cursor.rowcount
                except Exception as e:
                    conn.rollback()
                    logger.error(f"批量执行失败: {e}")
                    raise
    
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """执行事务"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    for query, params in queries:
                        cursor.execute(query, params)
                    conn.commit()
                    return True
                except Exception as e:
                    conn.rollback()
                    logger.error(f"事务执行失败: {e}")
                    raise
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    logger.info("数据库连接测试成功")
                    return result[0] == 1
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def close_pool(self) -> None:
        """关闭连接池"""
        if self.pool:
            self.pool.closeall()
            self.pool = None
            logger.info("数据库连接池已关闭")
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """获取表结构信息"""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name,))
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        )
        """
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result['exists'] if result else False
    
    def create_table_from_sql(self, sql_file_path: str) -> bool:
        """从SQL文件创建表"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_content)
                    conn.commit()
            
            logger.info(f"成功执行SQL文件: {sql_file_path}")
            return True
        except Exception as e:
            logger.error(f"执行SQL文件失败 {sql_file_path}: {e}")
            return False

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 兼容性函数，用于替换sqlite3.connect()调用
def get_db_connection():
    """获取数据库连接 - 兼容性函数"""
    return db_manager.get_connection()

def execute_query(query: str, params: Optional[tuple] = None, fetch_one: bool = False, fetch_all: bool = True):
    """执行查询 - 兼容性函数"""
    return db_manager.execute_query(query, params, fetch_one, fetch_all)

def init_connection_pool(minconn: int = 1, maxconn: int = 20):
    """初始化连接池 - 兼容性函数"""
    return db_manager.init_pool(minconn, maxconn)

def close_connection_pool():
    """关闭连接池 - 兼容性函数"""
    return db_manager.close_pool()

# SQLite到PostgreSQL的数据类型映射
SQLITE_TO_POSTGRESQL_TYPES = {
    'INTEGER': 'INTEGER',
    'TEXT': 'TEXT',
    'REAL': 'REAL',
    'BLOB': 'BYTEA',
    'NUMERIC': 'NUMERIC',
    'BOOLEAN': 'BOOLEAN',
    'DATETIME': 'TIMESTAMP',
    'DATE': 'DATE',
    'TIME': 'TIME',
    'VARCHAR': 'VARCHAR',
    'CHAR': 'CHAR',
    'DECIMAL': 'DECIMAL',
    'FLOAT': 'FLOAT',
    'DOUBLE': 'DOUBLE PRECISION'
}

def convert_sqlite_type_to_postgresql(sqlite_type: str) -> str:
    """将SQLite数据类型转换为PostgreSQL数据类型"""
    sqlite_type_upper = sqlite_type.upper()
    
    # 处理带长度的类型，如VARCHAR(255)
    if '(' in sqlite_type_upper:
        base_type = sqlite_type_upper.split('(')[0]
        length_part = sqlite_type_upper.split('(')[1]
        if base_type in SQLITE_TO_POSTGRESQL_TYPES:
            return f"{SQLITE_TO_POSTGRESQL_TYPES[base_type]}({length_part}"
    
    # 处理特殊情况
    if 'INTEGER PRIMARY KEY' in sqlite_type_upper:
        return 'SERIAL PRIMARY KEY'
    
    return SQLITE_TO_POSTGRESQL_TYPES.get(sqlite_type_upper, sqlite_type)

class SQLiteToPostgreSQLConverter:
    """SQLite到PostgreSQL的SQL语句转换器"""
    
    @staticmethod
    def convert_create_table(sqlite_sql: str) -> str:
        """转换CREATE TABLE语句"""
        postgresql_sql = sqlite_sql
        
        # 替换数据类型
        replacements = {
            'INTEGER PRIMARY KEY AUTOINCREMENT': 'SERIAL PRIMARY KEY',
            'DATETIME DEFAULT CURRENT_TIMESTAMP': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'BOOLEAN DEFAULT 1': 'BOOLEAN DEFAULT TRUE',
            'BOOLEAN DEFAULT 0': 'BOOLEAN DEFAULT FALSE',
            'VARCHAR DEFAULT': 'TEXT DEFAULT'
        }
        
        for sqlite_syntax, postgresql_syntax in replacements.items():
            postgresql_sql = postgresql_sql.replace(sqlite_syntax, postgresql_syntax)
        
        return postgresql_sql
    
    @staticmethod
    def convert_insert(sqlite_sql: str) -> str:
        """转换INSERT语句"""
        # PostgreSQL使用ON CONFLICT而不是INSERT OR IGNORE
        postgresql_sql = sqlite_sql.replace(
            'INSERT OR IGNORE INTO', 
            'INSERT INTO'
        )
        
        # 如果需要忽略冲突，添加ON CONFLICT DO NOTHING
        if 'INSERT OR IGNORE' in sqlite_sql:
            postgresql_sql += ' ON CONFLICT DO NOTHING'
        
        return postgresql_sql
    
    @staticmethod
    def convert_query(sqlite_sql: str) -> str:
        """通用SQL查询转换"""
        postgresql_sql = sqlite_sql
        
        # 替换LIMIT语法
        postgresql_sql = postgresql_sql.replace('LIMIT -1', '')
        
        # 替换日期函数
        postgresql_sql = postgresql_sql.replace('datetime()', 'NOW()')
        postgresql_sql = postgresql_sql.replace('date()', 'CURRENT_DATE')
        
        return postgresql_sql

# 导出主要接口
__all__ = [
    'DatabaseManager',
    'db_manager',
    'get_db_connection',
    'execute_query',
    'init_connection_pool',
    'close_connection_pool',
    'SQLiteToPostgreSQLConverter',
    'convert_sqlite_type_to_postgresql'
]