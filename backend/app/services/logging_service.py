"""
WePlus 后台管理系统 - 日志服务
提供用户操作记录、系统错误记录、审计日志等功能
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import traceback
import os
from pathlib import Path
import asyncio
from functools import wraps

# 导入数据库配置
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from database.postgresql_config import get_db_connection

class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(str, Enum):
    """日志分类枚举"""
    USER_ACTION = "USER_ACTION"          # 用户操作
    SYSTEM_ERROR = "SYSTEM_ERROR"        # 系统错误
    SECURITY = "SECURITY"                # 安全相关
    DATABASE = "DATABASE"                # 数据库操作
    FILE_OPERATION = "FILE_OPERATION"    # 文件操作
    API_ACCESS = "API_ACCESS"            # API访问
    AUTHENTICATION = "AUTHENTICATION"    # 认证相关
    ADMIN_ACTION = "ADMIN_ACTION"        # 管理员操作

class LoggingService:
    """日志服务类"""
    
    def __init__(self):
        """初始化日志服务（不在导入阶段触发数据库连接）。

        说明：
        - 仅设置文件/控制台日志；
        - 移除导入时对数据库的访问，避免在应用启动阶段因数据库不可达导致健康检查失败；
        - 若需要，可由外部在应用启动完成后显式调用 initialize() 以确保日志表存在。
        """
        self.setup_logging()
        self._initialized = False

    # 内部工具：检查列是否存在
    def _column_exists(self, cursor, table_name: str, column_name: str) -> bool:
        """检查指定表的列是否存在"""
        try:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                LIMIT 1
                """,
                (table_name, column_name)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"检查列是否存在失败: {table_name}.{column_name} - {str(e)}")
            return False

    # 内部工具：安全添加缺失列
    def _ensure_column(self, cursor, table_name: str, column_name: str, definition: str):
        """如果列缺失则添加该列（definition 为完整类型定义）"""
        try:
            if not self._column_exists(cursor, table_name, column_name):
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
                self.logger.info(f"已为表 {table_name} 添加缺失列: {column_name} {definition}")
        except Exception as e:
            self.logger.error(f"添加列失败: {table_name}.{column_name} - {str(e)}")

    # 内部工具：检查索引是否存在
    def _index_exists(self, cursor, index_name: str) -> bool:
        """检查索引是否存在"""
        try:
            cursor.execute(
                """
                SELECT 1
                FROM pg_indexes
                WHERE indexname = %s
                LIMIT 1
                """,
                (index_name,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"检查索引是否存在失败: {index_name} - {str(e)}")
            return False

    # 内部工具：仅在列存在时创建索引
    def _create_index_safe(self, cursor, index_name: str, table_name: str, column_name: str):
        """仅当列存在且索引不存在时创建索引，避免因缺列报错"""
        try:
            if not self._column_exists(cursor, table_name, column_name):
                self.logger.warning(f"跳过创建索引 {index_name}，原因：表 {table_name} 不存在列 {column_name}")
                return
            if not self._index_exists(cursor, index_name):
                cursor.execute(f"CREATE INDEX {index_name} ON {table_name}({column_name})")
                self.logger.info(f"已创建索引: {index_name} 于 {table_name}({column_name})")
        except Exception as e:
            self.logger.error(f"创建索引失败: {index_name} - {str(e)}")
    
    def setup_logging(self):
        """设置日志配置"""
        # 创建logs目录
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 配置文件日志
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / "weplus.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def ensure_log_tables(self):
        """确保日志表存在"""
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                
                # 创建系统日志表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(20) NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        details JSONB DEFAULT '{}',
                        user_id INTEGER,
                        ip_address INET,
                        user_agent TEXT,
                        request_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 旧表结构可能缺列，这里进行自愈补齐
                self._ensure_column(cursor, "system_logs", "details", "JSONB DEFAULT '{}'")
                self._ensure_column(cursor, "system_logs", "user_id", "INTEGER")
                self._ensure_column(cursor, "system_logs", "ip_address", "INET")
                self._ensure_column(cursor, "system_logs", "user_agent", "TEXT")
                self._ensure_column(cursor, "system_logs", "request_id", "VARCHAR(100)")
                self._ensure_column(cursor, "system_logs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                # 创建索引（仅在列存在的前提下）
                self._create_index_safe(cursor, "idx_system_logs_level", "system_logs", "level")
                self._create_index_safe(cursor, "idx_system_logs_category", "system_logs", "category")
                self._create_index_safe(cursor, "idx_system_logs_user_id", "system_logs", "user_id")
                self._create_index_safe(cursor, "idx_system_logs_created_at", "system_logs", "created_at")
                
                # 创建用户操作日志表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_action_logs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        resource_type VARCHAR(50),
                        resource_id INTEGER,
                        old_values JSONB DEFAULT '{}',
                        new_values JSONB DEFAULT '{}',
                        ip_address INET,
                        user_agent TEXT,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 自愈缺列
                self._ensure_column(cursor, "user_action_logs", "resource_type", "VARCHAR(50)")
                self._ensure_column(cursor, "user_action_logs", "resource_id", "INTEGER")
                self._ensure_column(cursor, "user_action_logs", "old_values", "JSONB DEFAULT '{}'")
                self._ensure_column(cursor, "user_action_logs", "new_values", "JSONB DEFAULT '{}'")
                self._ensure_column(cursor, "user_action_logs", "ip_address", "INET")
                self._ensure_column(cursor, "user_action_logs", "user_agent", "TEXT")
                self._ensure_column(cursor, "user_action_logs", "success", "BOOLEAN DEFAULT TRUE")
                self._ensure_column(cursor, "user_action_logs", "error_message", "TEXT")
                self._ensure_column(cursor, "user_action_logs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                # 安全索引
                self._create_index_safe(cursor, "idx_user_action_logs_user_id", "user_action_logs", "user_id")
                self._create_index_safe(cursor, "idx_user_action_logs_action", "user_action_logs", "action")
                self._create_index_safe(cursor, "idx_user_action_logs_resource_type", "user_action_logs", "resource_type")
                self._create_index_safe(cursor, "idx_user_action_logs_created_at", "user_action_logs", "created_at")
                
                # 创建API访问日志表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_access_logs (
                        id SERIAL PRIMARY KEY,
                        method VARCHAR(10) NOT NULL,
                        path VARCHAR(500) NOT NULL,
                        status_code INTEGER NOT NULL,
                        response_time FLOAT,
                        user_id INTEGER,
                        ip_address INET,
                        user_agent TEXT,
                        request_body TEXT,
                        response_body TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 自愈缺列
                self._ensure_column(cursor, "api_access_logs", "response_time", "FLOAT")
                self._ensure_column(cursor, "api_access_logs", "user_id", "INTEGER")
                self._ensure_column(cursor, "api_access_logs", "ip_address", "INET")
                self._ensure_column(cursor, "api_access_logs", "user_agent", "TEXT")
                self._ensure_column(cursor, "api_access_logs", "request_body", "TEXT")
                self._ensure_column(cursor, "api_access_logs", "response_body", "TEXT")
                self._ensure_column(cursor, "api_access_logs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                # 安全索引
                self._create_index_safe(cursor, "idx_api_access_logs_method", "api_access_logs", "method")
                self._create_index_safe(cursor, "idx_api_access_logs_path", "api_access_logs", "path")
                self._create_index_safe(cursor, "idx_api_access_logs_status_code", "api_access_logs", "status_code")
                self._create_index_safe(cursor, "idx_api_access_logs_user_id", "api_access_logs", "user_id")
                self._create_index_safe(cursor, "idx_api_access_logs_created_at", "api_access_logs", "created_at")
                
                conn.commit()
            
        except Exception as e:
            self.logger.error(f"创建日志表失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def initialize(self):
        """初始化数据库相关资源（可在应用启动完成后调用）。

        - 调用 ensure_log_tables()，若失败则记录错误但不抛出异常，避免影响主流程；
        - 仅执行一次初始化。
        """
        if getattr(self, "_initialized", False):
            return
        try:
            self.ensure_log_tables()
        except Exception as e:
            self.logger.error(f"日志服务初始化失败: {str(e)}")
        finally:
            self._initialized = True
    
    def log_system_event(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """记录系统事件"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_logs 
                (level, category, message, details, user_id, ip_address, user_agent, request_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                level.value,
                category.value,
                message,
                json.dumps(details or {}, ensure_ascii=False),
                user_id,
                ip_address,
                user_agent,
                request_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # 同时写入文件日志
            log_msg = f"[{category.value}] {message}"
            if details:
                log_msg += f" - Details: {json.dumps(details, ensure_ascii=False)}"
            
            if level == LogLevel.DEBUG:
                self.logger.debug(log_msg)
            elif level == LogLevel.INFO:
                self.logger.info(log_msg)
            elif level == LogLevel.WARNING:
                self.logger.warning(log_msg)
            elif level == LogLevel.ERROR:
                self.logger.error(log_msg)
            elif level == LogLevel.CRITICAL:
                self.logger.critical(log_msg)
                
        except Exception as e:
            self.logger.error(f"记录系统日志失败: {str(e)}")
    
    def log_user_action(
        self,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """记录用户操作"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_action_logs 
                (user_id, action, resource_type, resource_id, old_values, new_values, 
                 ip_address, user_agent, success, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                action,
                resource_type,
                resource_id,
                json.dumps(old_values or {}, ensure_ascii=False),
                json.dumps(new_values or {}, ensure_ascii=False),
                ip_address,
                user_agent,
                success,
                error_message
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # 记录到系统日志
            self.log_system_event(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                f"用户 {user_id} 执行操作: {action}",
                {
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "success": success
                },
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except Exception as e:
            self.logger.error(f"记录用户操作失败: {str(e)}")
    
    def log_api_access(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: Optional[float] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_body: Optional[str] = None,
        response_body: Optional[str] = None
    ):
        """记录API访问"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO api_access_logs 
                (method, path, status_code, response_time, user_id, ip_address, 
                 user_agent, request_body, response_body)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                method,
                path,
                status_code,
                response_time,
                user_id,
                ip_address,
                user_agent,
                request_body,
                response_body
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"记录API访问失败: {str(e)}")
    
    def get_system_logs(
        self,
        level: Optional[LogLevel] = None,
        category: Optional[LogCategory] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取系统日志"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            conditions = []
            params = []
            
            if level:
                conditions.append("level = %s")
                params.append(level.value)
            
            if category:
                conditions.append("category = %s")
                params.append(category.value)
            
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)
            
            if start_date:
                conditions.append("created_at >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("created_at <= %s")
                params.append(end_date)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT * FROM system_logs 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(log) for log in logs]
            
        except Exception as e:
            self.logger.error(f"获取系统日志失败: {str(e)}")
            return []
    
    def get_user_action_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户操作日志"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            conditions = []
            params = []
            
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)
            
            if action:
                conditions.append("action = %s")
                params.append(action)
            
            if resource_type:
                conditions.append("resource_type = %s")
                params.append(resource_type)
            
            if start_date:
                conditions.append("created_at >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("created_at <= %s")
                params.append(end_date)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT * FROM user_action_logs 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(log) for log in logs]
            
        except Exception as e:
            self.logger.error(f"获取用户操作日志失败: {str(e)}")
            return []
    
    def get_api_access_logs(
        self,
        method: Optional[str] = None,
        path_pattern: Optional[str] = None,
        status_code: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取API访问日志"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            conditions = []
            params = []
            
            if method:
                conditions.append("method = %s")
                params.append(method)
            
            if path_pattern:
                conditions.append("path LIKE %s")
                params.append(f"%{path_pattern}%")
            
            if status_code:
                conditions.append("status_code = %s")
                params.append(status_code)
            
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)
            
            if start_date:
                conditions.append("created_at >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("created_at <= %s")
                params.append(end_date)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT * FROM api_access_logs 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(log) for log in logs]
            
        except Exception as e:
            self.logger.error(f"获取API访问日志失败: {str(e)}")
            return []
    
    def get_log_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 默认查询最近7天
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            # 系统日志统计
            cursor.execute("""
                SELECT 
                    level,
                    COUNT(*) as count
                FROM system_logs 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY level
            """, (start_date, end_date))
            system_stats = {row['level']: row['count'] for row in cursor.fetchall()}
            
            # 用户操作统计
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT user_id) as active_users
                FROM user_action_logs 
                WHERE created_at BETWEEN %s AND %s
            """, (start_date, end_date))
            user_stats = cursor.fetchone()
            
            # API访问统计
            cursor.execute("""
                SELECT 
                    status_code,
                    COUNT(*) as count
                FROM api_access_logs 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY status_code
                ORDER BY status_code
            """, (start_date, end_date))
            api_stats = {str(row['status_code']): row['count'] for row in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "system_logs": system_stats,
                "user_actions": {
                    "total_actions": user_stats['total_actions'] if user_stats else 0,
                    "active_users": user_stats['active_users'] if user_stats else 0
                },
                "api_access": api_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取日志统计失败: {str(e)}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """清理旧日志"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 清理系统日志
            cursor.execute("""
                DELETE FROM system_logs 
                WHERE created_at < %s
            """, (cutoff_date,))
            system_deleted = cursor.rowcount
            
            # 清理用户操作日志
            cursor.execute("""
                DELETE FROM user_action_logs 
                WHERE created_at < %s
            """, (cutoff_date,))
            user_deleted = cursor.rowcount
            
            # 清理API访问日志
            cursor.execute("""
                DELETE FROM api_access_logs 
                WHERE created_at < %s
            """, (cutoff_date,))
            api_deleted = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.log_system_event(
                LogLevel.INFO,
                LogCategory.SYSTEM_ERROR,
                f"日志清理完成",
                {
                    "days_to_keep": days_to_keep,
                    "system_logs_deleted": system_deleted,
                    "user_action_logs_deleted": user_deleted,
                    "api_access_logs_deleted": api_deleted
                }
            )
            
            return {
                "success": True,
                "deleted_counts": {
                    "system_logs": system_deleted,
                    "user_action_logs": user_deleted,
                    "api_access_logs": api_deleted
                }
            }
            
        except Exception as e:
            self.logger.error(f"清理日志失败: {str(e)}")
            return {"success": False, "error": str(e)}

# 创建全局日志服务实例
logging_service = LoggingService()

# 装饰器函数
def log_user_action(action: str, resource_type: Optional[str] = None):
    """用户操作日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里需要从请求中获取用户信息，具体实现依赖于认证系统
            user_id = kwargs.get('user_id') or getattr(kwargs.get('request'), 'user_id', None)
            ip_address = getattr(kwargs.get('request'), 'client.host', None)
            
            try:
                result = await func(*args, **kwargs)
                
                logging_service.log_user_action(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    success=True,
                    ip_address=ip_address
                )
                
                return result
                
            except Exception as e:
                logging_service.log_user_action(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    success=False,
                    error_message=str(e),
                    ip_address=ip_address
                )
                raise
                
        return wrapper
    return decorator

def log_api_access():
    """API访问日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                logging_service.log_api_access(
                    method=request.method if request else "UNKNOWN",
                    path=str(request.url.path) if request else "UNKNOWN",
                    status_code=200,  # 假设成功
                    response_time=response_time,
                    user_id=getattr(request, 'user_id', None) if request else None,
                    ip_address=request.client.host if request else None,
                    user_agent=request.headers.get('user-agent') if request else None
                )
                
                return result
                
            except Exception as e:
                response_time = (datetime.now() - start_time).total_seconds()
                
                logging_service.log_api_access(
                    method=request.method if request else "UNKNOWN",
                    path=str(request.url.path) if request else "UNKNOWN",
                    status_code=500,  # 错误状态码
                    response_time=response_time,
                    user_id=getattr(request, 'user_id', None) if request else None,
                    ip_address=request.client.host if request else None,
                    user_agent=request.headers.get('user-agent') if request else None
                )
                
                raise
                
        return wrapper
    return decorator
