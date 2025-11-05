"""
数据库模型类
提供ORM风格的数据操作接口
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

from .config import db_config

@dataclass
class User:
    """用户模型"""
    id: Optional[int] = None
    email: str = ""
    username: str = ""
    password_hash: str = ""
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    profile: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.profile is None:
            self.profile = {}
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @classmethod
    async def create(cls, email: str, username: str, password: str, 
                    profile: Dict[str, Any] = None) -> 'User':
        """创建新用户"""
        password_hash = cls.hash_password(password)
        
        user = cls(
            email=email,
            username=username,
            password_hash=password_hash,
            profile=profile or {}
        )
        
        # 插入数据库
        query = """
            INSERT INTO users (email, username, password_hash, is_active, is_verified, profile)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        
        conn = await db_config.get_connection()
        try:
            result = await conn.fetchrow(
                query, 
                user.email, 
                user.username, 
                user.password_hash,
                user.is_active,
                user.is_verified,
                json.dumps(user.profile)
            )
            user.id = result['id']
            user.created_at = result['created_at']
            user.updated_at = result['updated_at']
            return user
        finally:
            await conn.close()
    
    @classmethod
    async def get_by_email(cls, email: str) -> Optional['User']:
        """根据邮箱获取用户"""
        query = """
            SELECT id, email, username, password_hash, is_active, is_verified,
                   created_at, updated_at, last_login, profile
            FROM users WHERE email = %s
        """
        
        conn = await db_config.get_connection()
        try:
            result = await conn.fetchrow(query, email)
            if result:
                return cls(
                    id=result['id'],
                    email=result['email'],
                    username=result['username'],
                    password_hash=result['password_hash'],
                    is_active=result['is_active'],
                    is_verified=result['is_verified'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    last_login=result['last_login'],
                    profile=json.loads(result['profile']) if result['profile'] else {}
                )
            return None
        finally:
            await conn.close()
    
    @classmethod
    async def get_by_id(cls, user_id: int) -> Optional['User']:
        """根据ID获取用户"""
        query = """
            SELECT id, email, username, password_hash, is_active, is_verified,
                   created_at, updated_at, last_login, profile
            FROM users WHERE id = %s
        """
        
        conn = await db_config.get_connection()
        try:
            result = await conn.fetchrow(query, user_id)
            if result:
                return cls(
                    id=result['id'],
                    email=result['email'],
                    username=result['username'],
                    password_hash=result['password_hash'],
                    is_active=result['is_active'],
                    is_verified=result['is_verified'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    last_login=result['last_login'],
                    profile=json.loads(result['profile']) if result['profile'] else {}
                )
            return None
        finally:
            await conn.close()
    
    async def update_verification_status(self, is_verified: bool = True):
        """更新验证状态"""
        query = """
            UPDATE users SET is_verified = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        conn = await db_config.get_connection()
        try:
            await conn.execute(query, is_verified, self.id)
            self.is_verified = is_verified
        finally:
            await conn.close()
    
    async def update_last_login(self):
        """更新最后登录时间"""
        query = """
            UPDATE users SET last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        conn = await db_config.get_connection()
        try:
            await conn.execute(query, self.id)
            self.last_login = datetime.now()
        finally:
            await conn.close()
    
    async def update_profile(self, profile: Dict[str, Any]):
        """更新用户资料"""
        query = """
            UPDATE users SET profile = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        conn = await db_config.get_connection()
        try:
            await conn.execute(query, json.dumps(profile), self.id)
            self.profile = profile
        finally:
            await conn.close()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'profile': self.profile
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    @classmethod
    async def get_paginated(cls, page: int = 1, limit: int = 10, 
                           search: Optional[str] = None, 
                           filters: Optional[Dict[str, Any]] = None) -> Tuple[List['User'], int]:
        """获取分页用户列表（管理员使用）"""
        offset = (page - 1) * limit
        
        # 构建查询条件
        where_conditions = []
        params = []
        param_count = 0
        
        if search:
            param_count += 2
            where_conditions.append(f"(email ILIKE ${param_count-1} OR username ILIKE ${param_count})")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        if filters:
            if 'is_active' in filters:
                param_count += 1
                where_conditions.append(f"is_active = ${param_count}")
                params.append(filters['is_active'])
            if 'is_verified' in filters:
                param_count += 1
                where_conditions.append(f"is_verified = ${param_count}")
                params.append(filters['is_verified'])
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM users {where_clause}"
        
        # 获取用户列表
        limit_param = param_count + 1
        offset_param = param_count + 2
        users_query = f"""
            SELECT id, email, username, password_hash, is_active, is_verified,
                   created_at, updated_at, last_login, profile
            FROM users {where_clause}
            ORDER BY created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        
        async with db_config.get_connection() as conn:
            # 获取总数
            total_count = await conn.fetchval(count_query, *params)
            
            # 获取用户列表 - 添加limit和offset参数
            list_params = list(params) + [limit, offset]
            results = await conn.fetch(users_query, *list_params)
            
            users = []
            for result in results:
                user = cls(
                    id=result['id'],
                    email=result['email'],
                    username=result['username'],
                    password_hash=result['password_hash'],
                    is_active=result['is_active'],
                    is_verified=result['is_verified'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    last_login=result['last_login'],
                    profile=json.loads(result['profile']) if result['profile'] else {}
                )
                users.append(user)
            
            return users, total_count
    
    @classmethod
    async def get_all_users(cls, page: int = 1, page_size: int = 20, 
                           search: Optional[str] = None) -> Tuple[List['User'], int]:
        """获取所有用户列表（分页）"""
        offset = (page - 1) * page_size
        
        # 构建查询条件
        where_clause = ""
        params = []
        if search:
            where_clause = "WHERE email ILIKE $1 OR username ILIKE $2"
            search_pattern = f"%{search}%"
            params = [search_pattern, search_pattern]
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM users {where_clause}"
        
        # 获取用户列表
        limit_param = len(params) + 1
        offset_param = len(params) + 2
        users_query = f"""
            SELECT id, email, username, password_hash, is_active, is_verified,
                   created_at, updated_at, last_login, profile
            FROM users {where_clause}
            ORDER BY created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        
        async with db_config.get_connection() as conn:
            # 获取总数
            total_count = await conn.fetchval(count_query, *params)
            
            # 获取用户列表
            results = await conn.fetch(users_query, *params, page_size, offset)
            
            users = []
            for result in results:
                user = cls(
                    id=result['id'],
                    email=result['email'],
                    username=result['username'],
                    password_hash=result['password_hash'],
                    is_active=result['is_active'],
                    is_verified=result['is_verified'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    last_login=result['last_login'],
                    profile=json.loads(result['profile']) if result['profile'] else {}
                )
                users.append(user)
            
            return users, total_count
    
    @classmethod
    async def get_user_statistics(cls) -> Dict[str, Any]:
        """获取用户统计信息"""
        query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_users,
                COUNT(CASE WHEN is_verified = true THEN 1 END) as verified_users,
                COUNT(CASE WHEN last_login >= NOW() - INTERVAL '7 days' THEN 1 END) as recent_active_users,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as new_users_this_month
            FROM users
        """
        
        conn = await db_config.get_connection()
        try:
            result = await conn.fetchrow(query)
            return dict(result) if result else {}
        finally:
            await conn.close()

@dataclass
class Document:
    """文档模型"""
    id: Optional[int] = None
    filename: str = ""
    file_type: str = ""
    file_size: int = 0
    upload_time: Optional[datetime] = None
    content_hash: str = ""
    metadata: Dict[str, Any] = None
    status: str = "uploaded"
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    async def create(cls, filename: str, file_type: str, file_size: int, 
                    content: bytes, metadata: Dict[str, Any] = None) -> 'Document':
        """创建新文档"""
        # 计算内容哈希
        content_hash = hashlib.sha256(content).hexdigest()
        
        doc = cls(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            content_hash=content_hash,
            metadata=metadata or {}
        )
        
        # 插入数据库
        query = """
            INSERT INTO documents (filename, file_type, file_size, content_hash, metadata, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, upload_time
        """
        
        async with db_config.get_connection() as conn:
            result = await conn.fetchrow(
                query, filename, file_type, file_size, content_hash, 
                json.dumps(metadata or {}), "uploaded"
            )
            doc.id = result['id']
            doc.upload_time = result['upload_time']
        
        return doc
    
    @classmethod
    async def get_by_id(cls, doc_id: int) -> Optional['Document']:
        """根据ID获取文档"""
        query = "SELECT * FROM documents WHERE id = $1"
        
        async with db_config.get_connection() as conn:
            result = await conn.fetchrow(query, doc_id)
            if result:
                return cls(
                    id=result['id'],
                    filename=result['filename'],
                    file_type=result['file_type'],
                    file_size=result['file_size'],
                    upload_time=result['upload_time'],
                    content_hash=result['content_hash'],
                    metadata=json.loads(result['metadata']) if result['metadata'] else {},
                    status=result['status']
                )
        return None
    
    @classmethod
    async def list_all(cls, status: Optional[str] = None) -> List['Document']:
        """获取所有文档列表"""
        if status:
            query = "SELECT * FROM documents WHERE status = $1 ORDER BY upload_time DESC"
            params = [status]
        else:
            query = "SELECT * FROM documents ORDER BY upload_time DESC"
            params = []
        
        async with db_config.get_connection() as conn:
            results = await conn.fetch(query, *params)
            return [
                cls(
                    id=row['id'],
                    filename=row['filename'],
                    file_type=row['file_type'],
                    file_size=row['file_size'],
                    upload_time=row['upload_time'],
                    content_hash=row['content_hash'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    status=row['status']
                ) for row in results
            ]
    
    async def update_status(self, status: str):
        """更新文档状态"""
        query = "UPDATE documents SET status = $1 WHERE id = $2"
        async with db_config.get_connection() as conn:
            await conn.execute(query, status, self.id)
        self.status = status
    
    async def delete(self):
        """删除文档（级联删除相关的chunks）"""
        query = "DELETE FROM documents WHERE id = $1"
        async with db_config.get_connection() as conn:
            await conn.execute(query, self.id)

@dataclass
class DocumentChunk:
    """文档块模型"""
    id: Optional[int] = None
    document_id: int = 0
    chunk_index: int = 0
    content: str = ""
    content_length: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.content_length == 0 and self.content:
            self.content_length = len(self.content)
    
    @classmethod
    async def create_batch(cls, chunks: List['DocumentChunk']) -> List['DocumentChunk']:
        """批量创建文档块"""
        if not chunks:
            return []
        
        query = """
            INSERT INTO document_chunks 
            (document_id, chunk_index, content, content_length, embedding, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, created_at
        """
        
        async with db_config.get_connection() as conn:
            # 准备批量插入数据
            insert_data = []
            for chunk in chunks:
                embedding_str = f"[{','.join(map(str, chunk.embedding))}]" if chunk.embedding else None
                insert_data.append((
                    chunk.document_id,
                    chunk.chunk_index,
                    chunk.content,
                    chunk.content_length,
                    embedding_str,
                    json.dumps(chunk.metadata)
                ))
            
            # 批量插入
            results = await conn.fetch(
                "INSERT INTO document_chunks (document_id, chunk_index, content, content_length, embedding, metadata) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, created_at",
                *insert_data[0]  # 先插入第一个，然后循环插入其他的
            )
            
            # 为了简化，这里使用循环插入（在生产环境中应该使用真正的批量插入）
            created_chunks = []
            for i, chunk in enumerate(chunks):
                embedding_str = f"[{','.join(map(str, chunk.embedding))}]" if chunk.embedding else None
                result = await conn.fetchrow(
                    query,
                    chunk.document_id,
                    chunk.chunk_index,
                    chunk.content,
                    chunk.content_length,
                    embedding_str,
                    json.dumps(chunk.metadata)
                )
                chunk.id = result['id']
                chunk.created_at = result['created_at']
                created_chunks.append(chunk)
            
            return created_chunks
    
    @classmethod
    async def get_by_document_id(cls, document_id: int) -> List['DocumentChunk']:
        """根据文档ID获取所有块"""
        query = """
            SELECT id, document_id, chunk_index, content, content_length, 
                   embedding, metadata, created_at
            FROM document_chunks 
            WHERE document_id = $1 
            ORDER BY chunk_index
        """
        
        async with db_config.get_connection() as conn:
            results = await conn.fetch(query, document_id)
            chunks = []
            for row in results:
                # 解析向量数据
                embedding = None
                if row['embedding']:
                    # pgvector返回的是字符串格式，需要解析
                    embedding_str = str(row['embedding'])
                    if embedding_str.startswith('[') and embedding_str.endswith(']'):
                        embedding = [float(x) for x in embedding_str[1:-1].split(',')]
                
                chunks.append(cls(
                    id=row['id'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    content=row['content'],
                    content_length=row['content_length'],
                    embedding=embedding,
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at']
                ))
            return chunks
    
    @classmethod
    async def search_similar(cls, query_embedding: List[float], 
                           similarity_threshold: float = 0.7,
                           max_results: int = 10) -> List[Tuple['DocumentChunk', float]]:
        """相似度搜索"""
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        query = """
            SELECT dc.*, d.filename,
                   1 - (dc.embedding <=> $1::vector) as similarity_score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.status = 'processed'
            AND 1 - (dc.embedding <=> $1::vector) > $2
            ORDER BY dc.embedding <=> $1::vector
            LIMIT $3
        """
        
        async with db_config.get_connection() as conn:
            results = await conn.fetch(query, embedding_str, similarity_threshold, max_results)
            
            chunks_with_scores = []
            for row in results:
                # 解析向量数据
                embedding = None
                if row['embedding']:
                    embedding_str = str(row['embedding'])
                    if embedding_str.startswith('[') and embedding_str.endswith(']'):
                        embedding = [float(x) for x in embedding_str[1:-1].split(',')]
                
                chunk = cls(
                    id=row['id'],
                    document_id=row['document_id'],
                    chunk_index=row['chunk_index'],
                    content=row['content'],
                    content_length=row['content_length'],
                    embedding=embedding,
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at']
                )
                
                chunks_with_scores.append((chunk, float(row['similarity_score'])))
            
            return chunks_with_scores

@dataclass
class ChatSession:
    """对话会话模型"""
    id: Optional[int] = None
    session_id: str = ""
    user_id: Optional[str] = None
    title: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.session_id:
            self.session_id = str(uuid4())
    
    @classmethod
    async def create(cls, user_id: Optional[str] = None, title: str = "新对话") -> 'ChatSession':
        """创建新的对话会话"""
        session = cls(user_id=user_id, title=title)
        
        query = """
            INSERT INTO chat_sessions (session_id, user_id, title, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id, created_at, updated_at
        """
        
        async with db_config.get_connection() as conn:
            result = await conn.fetchrow(
                query, session.session_id, user_id, title, json.dumps({})
            )
            session.id = result['id']
            session.created_at = result['created_at']
            session.updated_at = result['updated_at']
        
        return session
    
    @classmethod
    async def get_by_session_id(cls, session_id: str) -> Optional['ChatSession']:
        """根据session_id获取会话"""
        query = "SELECT * FROM chat_sessions WHERE session_id = $1"
        
        async with db_config.get_connection() as conn:
            result = await conn.fetchrow(query, session_id)
            if result:
                return cls(
                    id=result['id'],
                    session_id=result['session_id'],
                    user_id=result['user_id'],
                    title=result['title'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    metadata=json.loads(result['metadata']) if result['metadata'] else {}
                )
        return None
    
    async def add_message(self, message_type: str, content: str, 
                         metadata: Dict[str, Any] = None) -> 'ChatMessage':
        """添加消息到会话"""
        return await ChatMessage.create(
            session_id=self.session_id,
            message_type=message_type,
            content=content,
            metadata=metadata
        )
    
    async def get_messages(self, limit: int = 50) -> List['ChatMessage']:
        """获取会话的所有消息"""
        return await ChatMessage.get_by_session_id(self.session_id, limit)
    
    @classmethod
    async def get_all_sessions(cls, page: int = 1, page_size: int = 20, 
                              user_id: Optional[str] = None) -> Tuple[List['ChatSession'], int]:
        """获取所有聊天会话（分页）"""
        offset = (page - 1) * page_size
        
        # 构建查询条件
        where_clause = ""
        params = []
        if user_id:
            where_clause = "WHERE user_id = %s"
            params = [user_id]
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM chat_sessions {where_clause}"
        
        # 获取会话列表
        sessions_query = f"""
            SELECT id, session_id, user_id, title, created_at, updated_at, metadata
            FROM chat_sessions {where_clause}
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """
        
        conn = await db_config.get_connection()
        try:
            # 获取总数
            total_count = await conn.fetchval(count_query, *params)
            
            # 获取会话列表
            results = await conn.fetch(sessions_query, *params, page_size, offset)
            
            sessions = []
            for result in results:
                session = cls(
                    id=result['id'],
                    session_id=result['session_id'],
                    user_id=result['user_id'],
                    title=result['title'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    metadata=json.loads(result['metadata']) if result['metadata'] else {}
                )
                sessions.append(session)
            
            return sessions, total_count
        finally:
            await conn.close()
    
    @classmethod
    async def get_chat_statistics(cls) -> Dict[str, Any]:
        """获取聊天统计信息"""
        query = """
            SELECT 
                COUNT(DISTINCT cs.session_id) as total_sessions,
                COUNT(cm.id) as total_messages,
                COUNT(CASE WHEN cs.created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as sessions_this_week,
                COUNT(CASE WHEN cm.created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as messages_this_week,
                AVG(message_counts.msg_count) as avg_messages_per_session
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
            LEFT JOIN (
                SELECT session_id, COUNT(*) as msg_count 
                FROM chat_messages 
                GROUP BY session_id
            ) message_counts ON cs.session_id = message_counts.session_id
        """
        
        conn = await db_config.get_connection()
        try:
            result = await conn.fetchrow(query)
            return dict(result) if result else {}
        finally:
            await conn.close()

@dataclass
class ChatMessage:
    """对话消息模型"""
    id: Optional[int] = None
    session_id: str = ""
    message_type: str = "user"  # user, assistant, system
    content: str = ""
    metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    async def create(cls, session_id: str, message_type: str, content: str,
                    metadata: Dict[str, Any] = None) -> 'ChatMessage':
        """创建新消息"""
        message = cls(
            session_id=session_id,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
        
        query = """
            INSERT INTO chat_messages (session_id, message_type, content, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING id, created_at
        """
        
        async with db_config.get_connection() as conn:
            result = await conn.fetchrow(
                query, session_id, message_type, content, json.dumps(metadata or {})
            )
            message.id = result['id']
            message.created_at = result['created_at']
        
        return message
    
    @classmethod
    async def get_by_session_id(cls, session_id: str, limit: int = 50) -> List['ChatMessage']:
        """根据会话ID获取消息列表"""
        query = """
            SELECT * FROM chat_messages 
            WHERE session_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """
        
        async with db_config.get_connection() as conn:
            results = await conn.fetch(query, session_id, limit)
            messages = []
            for row in results:
                messages.append(cls(
                    id=row['id'],
                    session_id=row['session_id'],
                    message_type=row['message_type'],
                    content=row['content'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at']
                ))
            return list(reversed(messages))  # 返回时间正序

# 数据库操作工具函数
async def get_database_statistics() -> Dict[str, Any]:
    """获取数据库统计信息"""
    async with db_config.get_connection() as conn:
        # 文档统计
        doc_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_documents,
                COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed_documents,
                SUM(file_size) as total_file_size
            FROM documents
        """)
        
        # 文档块统计
        chunk_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_chunks,
                AVG(content_length) as avg_chunk_length,
                SUM(content_length) as total_content_length
            FROM document_chunks
        """)
        
        # 对话统计
        chat_stats = await conn.fetchrow("""
            SELECT 
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(*) as total_messages
            FROM chat_messages
        """)
        
        return {
            'documents': dict(doc_stats) if doc_stats else {},
            'chunks': dict(chunk_stats) if chunk_stats else {},
            'chats': dict(chat_stats) if chat_stats else {}
        }

if __name__ == "__main__":
    # 测试模型
    async def test_models():
        from .config import init_database, close_database
        
        await init_database()
        
        # 测试统计信息
        stats = await get_database_statistics()
        print("数据库统计:", stats)
        
        await close_database()
    
    asyncio.run(test_models())