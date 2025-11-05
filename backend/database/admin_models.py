"""
WePlus 后台管理系统数据库模型
包含用户管理、文件管理和RAG知识库管理的完整数据模型
"""

import asyncio
import json
import hashlib
import bcrypt
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from uuid import uuid4
import numpy as np
from enum import Enum

# 使用新的PostgreSQL连接管理器
from .db_manager import DatabaseManager as PostgreSQLManager

class FileType(Enum):
    """文件类型枚举"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    JPG = "jpg"
    PNG = "png"
    JPEG = "jpeg"
    OTHER = "other"

class ProcessingStatus(Enum):
    """文件处理状态枚举"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 处理失败
    VECTORIZED = "vectorized"   # 已向量化

class UserRole(Enum):
    """用户角色枚举"""
    USER = "user"               # 普通用户
    ADMIN = "admin"             # 管理员
    SUPER_ADMIN = "super_admin" # 超级管理员

@dataclass
class AdminUser:
    """管理员用户模型 - PostgreSQL版本"""
    id: Optional[int] = None
    email: str = ""
    username: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    profile: Dict[str, Any] = None
    
    # 新增字段
    real_name: str = ""          # 真实姓名
    phone: str = ""              # 电话号码
    department: str = ""         # 部门
    student_id: str = ""         # 学号/工号
    avatar_url: str = ""         # 头像URL
    
    def __post_init__(self):
        if self.profile is None:
            self.profile = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def reset_password(self, new_password: str) -> bool:
        """重置用户密码"""
        try:
            self.password_hash = self.hash_password(new_password)
            self.updated_at = datetime.now()
            return True
        except Exception as e:
            print(f"重置密码失败: {e}")
            return False
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now()
        self.login_count += 1
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，排除敏感信息"""
        data = asdict(self)
        data.pop('password_hash', None)  # 移除密码哈希
        return data
    
    @classmethod
    async def create(cls, email: str, username: str, password: str, 
                    role: UserRole = UserRole.USER,
                    real_name: str = "", phone: str = "", 
                    department: str = "", student_id: str = "") -> 'AdminUser':
        """创建新用户"""
        password_hash = cls.hash_password(password)
        
        user = cls(
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
            real_name=real_name,
            phone=phone,
            department=department,
            student_id=student_id
        )
        
        # 使用PostgreSQL管理器插入数据
        db_manager = PostgreSQLManager()
        query = """
        INSERT INTO admin_users (email, username, password_hash, role, is_active, is_verified,
                                real_name, phone, department, student_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            user.email, user.username, user.password_hash, user.role.value,
            user.is_active, user.is_verified, user.real_name, user.phone,
            user.department, user.student_id, user.created_at, user.updated_at
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        user.id = result['id']
        
        return user

    @classmethod
    async def get_by_email(cls, email: str) -> Optional['AdminUser']:
        """根据邮箱获取用户"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM admin_users WHERE email = %s"
        result = await db_manager.execute_query(query, (email,), fetch_one=True)
        
        if result:
            return cls(**result)
        return None

    @classmethod
    async def get_by_id(cls, user_id: int) -> Optional['AdminUser']:
        """根据ID获取用户"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM admin_users WHERE id = %s"
        result = await db_manager.execute_query(query, (user_id,), fetch_one=True)
        
        if result:
            return cls(**result)
        return None

    async def save(self):
        """保存用户信息"""
        db_manager = PostgreSQLManager()
        if self.id:
            # 更新现有用户
            query = """
            UPDATE admin_users SET email = %s, username = %s, password_hash = %s,
                   role = %s, is_active = %s, is_verified = %s, real_name = %s,
                   phone = %s, department = %s, student_id = %s, updated_at = %s
            WHERE id = %s
            """
            params = (
                self.email, self.username, self.password_hash, self.role.value,
                self.is_active, self.is_verified, self.real_name, self.phone,
                self.department, self.student_id, datetime.now(), self.id
            )
        else:
            # 创建新用户
            query = """
            INSERT INTO admin_users (email, username, password_hash, role, is_active, is_verified,
                                    real_name, phone, department, student_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            params = (
                self.email, self.username, self.password_hash, self.role.value,
                self.is_active, self.is_verified, self.real_name, self.phone,
                self.department, self.student_id, self.created_at, self.updated_at
            )
            result = await db_manager.execute_query(query, params, fetch_one=True)
            self.id = result['id']
            return
        
        await db_manager.execute_query(query, params)

    async def delete(self) -> bool:
        """删除用户及其相关数据（级联删除）"""
        try:
            db_manager = PostgreSQLManager()
            
            # 开始事务
            async with db_manager.get_connection() as conn:
                async with conn.transaction():
                    # 1. 删除用户上传的文件记录
                    await conn.execute(
                        "DELETE FROM file_records WHERE user_id = $1", 
                        self.id
                    )
                    
                    # 2. 删除用户创建的文档
                    await conn.execute(
                        "DELETE FROM documents WHERE created_by = $1", 
                        self.id
                    )
                    
                    # 3. 删除用户的学习资源
                    await conn.execute(
                        "DELETE FROM study_resources WHERE uploader_id = $1", 
                        self.id
                    )
                    
                    # 4. 删除用户的操作日志（可选，根据需求决定是否保留）
                    # await conn.execute(
                    #     "DELETE FROM user_logs WHERE user_id = $1", 
                    #     self.id
                    # )
                    
                    # 5. 最后删除用户记录
                    result = await conn.execute(
                        "DELETE FROM admin_users WHERE id = $1", 
                        self.id
                    )
                    
                    return result == "DELETE 1"
                    
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False

@dataclass
class FileRecord:
    """文件记录模型 - PostgreSQL版本"""
    id: Optional[int] = None
    filename: str = ""
    original_filename: str = ""   # 原始文件名
    file_path: str = ""
    file_size: int = 0            # 文件大小（字节）
    file_type: FileType = FileType.OTHER
    mime_type: str = ""           # MIME类型
    upload_time: Optional[datetime] = None
    content_summary: str = ""     # 内容摘要
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    user_id: Optional[int] = None # 上传用户ID
    
    # 新增字段
    file_hash: str = ""           # 文件哈希值（用于去重）
    download_count: int = 0       # 下载次数
    is_public: bool = False       # 是否公开
    tags: List[str] = None        # 标签
    category: str = ""            # 分类
    description: str = ""         # 描述
    
    # 处理相关字段
    extracted_text: str = ""      # 提取的文本内容
    processing_error: str = ""    # 处理错误信息
    processed_at: Optional[datetime] = None  # 处理完成时间
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.upload_time is None:
            self.upload_time = datetime.now()
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.md5(file_content).hexdigest()
    
    def update_processing_status(self, status: ProcessingStatus, error: str = ""):
        """更新处理状态"""
        self.processing_status = status
        if error:
            self.processing_error = error
        if status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.VECTORIZED]:
            self.processed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举为字符串
        data['file_type'] = self.file_type.value
        data['processing_status'] = self.processing_status.value
        return data
    
    @classmethod
    async def create(cls, filename: str, file_path: str, file_size: int,
                    file_type: FileType, user_id: int, 
                    file_content: bytes = None) -> 'FileRecord':
        """创建新文件记录"""
        file_record = cls(
            filename=filename,
            original_filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            user_id=user_id
        )
        
        if file_content:
            file_record.file_hash = file_record.calculate_file_hash(file_content)
        
        # 使用PostgreSQL管理器插入数据
        db_manager = PostgreSQLManager()
        query = """
        INSERT INTO file_records (filename, original_filename, file_path, file_size,
                                 file_type, mime_type, upload_time, user_id, file_hash,
                                 is_public, category, description, processing_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            file_record.filename, file_record.original_filename, file_record.file_path,
            file_record.file_size, file_record.file_type.value, file_record.mime_type,
            file_record.upload_time, file_record.user_id, file_record.file_hash,
            file_record.is_public, file_record.category, file_record.description,
            file_record.processing_status.value
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        file_record.id = result['id']
        
        return file_record

    @classmethod
    async def get_by_id(cls, file_id: int) -> Optional['FileRecord']:
        """根据ID获取文件记录"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM file_records WHERE id = %s"
        result = await db_manager.execute_query(query, (file_id,), fetch_one=True)
        
        if result:
            # 转换枚举字段
            result['file_type'] = FileType(result['file_type'])
            result['processing_status'] = ProcessingStatus(result['processing_status'])
            return cls(**result)
        return None

    @classmethod
    async def get_paginated(cls, page: int = 1, limit: int = 10, user_id: int = None) -> Tuple[List['FileRecord'], int]:
        """分页获取文件列表"""
        db_manager = PostgreSQLManager()
        offset = (page - 1) * limit
        
        # 构建查询条件
        where_clause = ""
        params = []
        if user_id:
            where_clause = "WHERE user_id = %s"
            params.append(user_id)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) as total FROM file_records {where_clause}"
        count_result = await db_manager.execute_query(count_query, params, fetch_one=True)
        total = count_result['total']
        
        # 获取分页数据
        query = f"""
        SELECT * FROM file_records {where_clause}
        ORDER BY upload_time DESC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        results = await db_manager.execute_query(query, params)
        
        files = []
        for result in results:
            result['file_type'] = FileType(result['file_type'])
            result['processing_status'] = ProcessingStatus(result['processing_status'])
            files.append(cls(**result))
        
        return files, total

    async def save(self):
        """保存文件记录"""
        db_manager = PostgreSQLManager()
        if self.id:
            # 更新现有记录
            query = """
            UPDATE file_records SET filename = %s, file_path = %s, file_size = %s,
                   file_type = %s, mime_type = %s, content_summary = %s,
                   processing_status = %s, download_count = %s, is_public = %s,
                   category = %s, description = %s, extracted_text = %s,
                   processing_error = %s, processed_at = %s
            WHERE id = %s
            """
            params = (
                self.filename, self.file_path, self.file_size, self.file_type.value,
                self.mime_type, self.content_summary, self.processing_status.value,
                self.download_count, self.is_public, self.category, self.description,
                self.extracted_text, self.processing_error, self.processed_at, self.id
            )
        else:
            # 创建新记录
            query = """
            INSERT INTO file_records (filename, original_filename, file_path, file_size,
                                     file_type, mime_type, upload_time, user_id, file_hash,
                                     is_public, category, description, processing_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            params = (
                self.filename, self.original_filename, self.file_path, self.file_size,
                self.file_type.value, self.mime_type, self.upload_time, self.user_id,
                self.file_hash, self.is_public, self.category, self.description,
                self.processing_status.value
            )
            result = await db_manager.execute_query(query, params, fetch_one=True)
            self.id = result['id']
            return
        
        await db_manager.execute_query(query, params)

@dataclass
class KnowledgeEntry:
    """RAG知识库条目模型 - PostgreSQL版本"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    source_file_id: Optional[int] = None  # 来源文件ID
    vector_id: str = ""                   # 向量存储ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category: str = ""
    
    # 新增字段
    keywords: List[str] = None            # 关键词
    summary: str = ""                     # 摘要
    importance_score: float = 0.0         # 重要性评分
    access_count: int = 0                 # 访问次数
    is_active: bool = True                # 是否激活
    
    # 向量化相关
    embedding_model: str = ""             # 使用的嵌入模型
    vector_dimension: int = 0             # 向量维度
    similarity_threshold: float = 0.7     # 相似度阈值
    
    # 元数据
    metadata: Dict[str, Any] = None       # 额外元数据
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def update_access_count(self):
        """更新访问次数"""
        self.access_count += 1
        self.updated_at = datetime.now()
    
    def update_content(self, new_content: str, new_title: str = None):
        """更新内容"""
        self.content = new_content
        if new_title:
            self.title = new_title
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    async def create(cls, title: str, content: str, category: str = "",
                    source_file_id: int = None, keywords: List[str] = None) -> 'KnowledgeEntry':
        """创建新知识条目"""
        entry = cls(
            title=title,
            content=content,
            category=category,
            source_file_id=source_file_id,
            keywords=keywords or []
        )
        
        # 使用PostgreSQL管理器插入数据
        db_manager = PostgreSQLManager()
        query = """
        INSERT INTO knowledge_entries (title, content, category, source_file_id,
                                      keywords, summary, importance_score, is_active,
                                      embedding_model, vector_dimension, similarity_threshold,
                                      metadata, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            entry.title, entry.content, entry.category, entry.source_file_id,
            json.dumps(entry.keywords), entry.summary, entry.importance_score,
            entry.is_active, entry.embedding_model, entry.vector_dimension,
            entry.similarity_threshold, json.dumps(entry.metadata),
            entry.created_at, entry.updated_at
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        entry.id = result['id']
        
        return entry

    @classmethod
    async def get_by_id(cls, entry_id: int) -> Optional['KnowledgeEntry']:
        """根据ID获取知识条目"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM knowledge_entries WHERE id = %s"
        result = await db_manager.execute_query(query, (entry_id,), fetch_one=True)
        
        if result:
            # 解析JSON字段
            if result.get('keywords'):
                result['keywords'] = json.loads(result['keywords'])
            if result.get('metadata'):
                result['metadata'] = json.loads(result['metadata'])
            return cls(**result)
        return None

    async def save(self):
        """保存知识条目"""
        db_manager = PostgreSQLManager()
        if self.id:
            # 更新现有条目
            query = """
            UPDATE knowledge_entries SET title = %s, content = %s, category = %s,
                   keywords = %s, summary = %s, importance_score = %s, is_active = %s,
                   embedding_model = %s, vector_dimension = %s, similarity_threshold = %s,
                   metadata = %s, updated_at = %s, access_count = %s
            WHERE id = %s
            """
            params = (
                self.title, self.content, self.category, json.dumps(self.keywords),
                self.summary, self.importance_score, self.is_active,
                self.embedding_model, self.vector_dimension, self.similarity_threshold,
                json.dumps(self.metadata), datetime.now(), self.access_count, self.id
            )
        else:
            # 创建新条目
            query = """
            INSERT INTO knowledge_entries (title, content, category, source_file_id,
                                          keywords, summary, importance_score, is_active,
                                          embedding_model, vector_dimension, similarity_threshold,
                                          metadata, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            params = (
                self.title, self.content, self.category, self.source_file_id,
                json.dumps(self.keywords), self.summary, self.importance_score,
                self.is_active, self.embedding_model, self.vector_dimension,
                self.similarity_threshold, json.dumps(self.metadata),
                self.created_at, self.updated_at
            )
            result = await db_manager.execute_query(query, params, fetch_one=True)
            self.id = result['id']
            return
        
        await db_manager.execute_query(query, params)

@dataclass
class SystemStats:
    """系统统计信息模型 - PostgreSQL版本"""
    total_users: int = 0
    active_users: int = 0
    total_files: int = 0
    total_file_size: int = 0          # 总文件大小（字节）
    total_knowledge_entries: int = 0
    processed_files: int = 0
    pending_files: int = 0
    failed_files: int = 0
    
    # 按类型统计
    file_type_stats: Dict[str, int] = None
    category_stats: Dict[str, int] = None
    
    # 时间统计
    today_uploads: int = 0
    this_week_uploads: int = 0
    this_month_uploads: int = 0
    
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.file_type_stats is None:
            self.file_type_stats = {}
        if self.category_stats is None:
            self.category_stats = {}
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    async def calculate_stats(cls) -> 'SystemStats':
        """计算系统统计信息"""
        db_manager = PostgreSQLManager()
        stats = cls()
        
        # 用户统计
        user_query = "SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE is_active = true) as active FROM admin_users"
        user_result = await db_manager.execute_query(user_query, fetch_one=True)
        stats.total_users = user_result['total']
        stats.active_users = user_result['active']
        
        # 文件统计
        file_query = """
        SELECT COUNT(*) as total, 
               COALESCE(SUM(file_size), 0) as total_size,
               COUNT(*) FILTER (WHERE processing_status = 'completed') as processed,
               COUNT(*) FILTER (WHERE processing_status = 'pending') as pending,
               COUNT(*) FILTER (WHERE processing_status = 'failed') as failed
        FROM file_records
        """
        file_result = await db_manager.execute_query(file_query, fetch_one=True)
        stats.total_files = file_result['total']
        stats.total_file_size = file_result['total_size']
        stats.processed_files = file_result['processed']
        stats.pending_files = file_result['pending']
        stats.failed_files = file_result['failed']
        
        # 知识库统计
        knowledge_query = "SELECT COUNT(*) as total FROM knowledge_entries WHERE is_active = true"
        knowledge_result = await db_manager.execute_query(knowledge_query, fetch_one=True)
        stats.total_knowledge_entries = knowledge_result['total']
        
        # 文件类型统计
        type_query = "SELECT file_type, COUNT(*) as count FROM file_records GROUP BY file_type"
        type_results = await db_manager.execute_query(type_query)
        stats.file_type_stats = {row['file_type']: row['count'] for row in type_results}
        
        # 分类统计
        category_query = "SELECT category, COUNT(*) as count FROM file_records WHERE category != '' GROUP BY category"
        category_results = await db_manager.execute_query(category_query)
        stats.category_stats = {row['category']: row['count'] for row in category_results}
        
        # 时间统计
        today_query = "SELECT COUNT(*) as count FROM file_records WHERE DATE(upload_time) = CURRENT_DATE"
        today_result = await db_manager.execute_query(today_query, fetch_one=True)
        stats.today_uploads = today_result['count']
        
        week_query = "SELECT COUNT(*) as count FROM file_records WHERE upload_time >= CURRENT_DATE - INTERVAL '7 days'"
        week_result = await db_manager.execute_query(week_query, fetch_one=True)
        stats.this_week_uploads = week_result['count']
        
        month_query = "SELECT COUNT(*) as count FROM file_records WHERE upload_time >= CURRENT_DATE - INTERVAL '30 days'"
        month_result = await db_manager.execute_query(month_query, fetch_one=True)
        stats.this_month_uploads = month_result['count']
        
        stats.last_updated = datetime.now()
        return stats

# 数据库操作类
class DatabaseManager:
    """数据库管理器 - PostgreSQL版本"""
    
    def __init__(self):
        self.pg_manager = PostgreSQLManager()
    
    async def init_tables(self):
        """初始化数据库表"""
        # 读取并执行PostgreSQL初始化脚本
        import os
        script_path = os.path.join(os.path.dirname(__file__), 'postgresql_complete_schema.sql')
        
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # 分割并执行SQL语句
            statements = sql_script.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    await self.pg_manager.execute_query(statement)
    
    async def create_user(self, user_data: Dict[str, Any]) -> AdminUser:
        """创建用户"""
        return await AdminUser.create(**user_data)
    
    async def get_user_by_email(self, email: str) -> Optional[AdminUser]:
        """根据邮箱获取用户"""
        return await AdminUser.get_by_email(email)
    
    async def create_file_record(self, file_data: Dict[str, Any]) -> FileRecord:
        """创建文件记录"""
        return await FileRecord.create(**file_data)
    
    async def get_files_paginated(self, page: int = 1, limit: int = 10, user_id: int = None) -> Tuple[List[FileRecord], int]:
        """分页获取文件列表"""
        return await FileRecord.get_paginated(page, limit, user_id)
    
    async def create_knowledge_entry(self, entry_data: Dict[str, Any]) -> KnowledgeEntry:
        """创建知识条目"""
        return await KnowledgeEntry.create(**entry_data)
    
    async def get_system_stats(self) -> SystemStats:
        """获取系统统计信息"""
        return await SystemStats.calculate_stats()

# 全局数据库管理器实例
db_manager = DatabaseManager()