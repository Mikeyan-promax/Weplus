"""
RAG系统数据库模型 - PostgreSQL版本
包含文档处理、向量存储、聊天会话等相关模型
"""
import os
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

# 使用新的PostgreSQL连接管理器
from .db_manager import DatabaseManager as PostgreSQLManager

class DocumentStatus(Enum):
    """文档处理状态枚举"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class Document:
    """文档模型 - PostgreSQL版本"""
    id: Optional[int] = None
    filename: str = ""
    file_type: str = ""
    file_size: int = 0
    upload_time: Optional[datetime] = None
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.UPLOADED
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    async def create(cls, filename: str, file_type: str, file_size: int, 
                    content_hash: str, metadata: Dict[str, Any] = None) -> 'Document':
        """创建新文档记录"""
        # 使用PostgreSQL管理器插入数据
        db_manager = PostgreSQLManager()
        
        query = """
        INSERT INTO documents (filename, file_type, file_size, content_hash, metadata, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, upload_time
        """
        
        params = (
            filename,
            file_type,
            file_size,
            content_hash,
            json.dumps(metadata or {}),
            DocumentStatus.UPLOADED.value
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                upload_time=result['upload_time'],
                content_hash=content_hash,
                metadata=metadata or {},
                status=DocumentStatus.UPLOADED
            )
        return None
    
    @classmethod
    async def get_by_id(cls, document_id: int) -> Optional['Document']:
        """根据ID获取文档"""
        db_manager = PostgreSQLManager()
        
        query = "SELECT * FROM documents WHERE id = %s"
        result = await db_manager.execute_query(query, (document_id,), fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                filename=result['filename'],
                file_type=result['file_type'],
                file_size=result['file_size'],
                upload_time=result['upload_time'],
                content_hash=result['content_hash'],
                metadata=json.loads(result['metadata']) if result['metadata'] else {},
                status=DocumentStatus(result['status'])
            )
        return None
    
    @classmethod
    async def get_by_hash(cls, content_hash: str) -> Optional['Document']:
        """根据内容哈希获取文档"""
        db_manager = PostgreSQLManager()
        
        query = "SELECT * FROM documents WHERE content_hash = %s"
        result = await db_manager.execute_query(query, (content_hash,), fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                filename=result['filename'],
                file_type=result['file_type'],
                file_size=result['file_size'],
                upload_time=result['upload_time'],
                content_hash=result['content_hash'],
                metadata=json.loads(result['metadata']) if result['metadata'] else {},
                status=DocumentStatus(result['status'])
            )
        return None
    
    async def update_status(self, status: DocumentStatus):
        """更新文档状态"""
        db_manager = PostgreSQLManager()
        
        query = "UPDATE documents SET status = %s WHERE id = %s"
        await db_manager.execute_query(query, (status.value, self.id))
        self.status = status
    
    async def save(self):
        """保存文档更新"""
        if not self.id:
            return
        
        db_manager = PostgreSQLManager()
        
        query = """
        UPDATE documents 
        SET filename = %s, file_type = %s, file_size = %s, 
            content_hash = %s, metadata = %s, status = %s
        WHERE id = %s
        """
        
        params = (
            self.filename,
            self.file_type,
            self.file_size,
            self.content_hash,
            json.dumps(self.metadata),
            self.status.value,
            self.id
        )
        
        await db_manager.execute_query(query, params)

@dataclass
class DocumentChunk:
    """文档块模型 - PostgreSQL版本"""
    id: Optional[int] = None
    document_id: int = 0
    chunk_index: int = 0
    content: str = ""
    content_length: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.content_length == 0 and self.content:
            self.content_length = len(self.content)
    
    @classmethod
    async def create(cls, document_id: int, chunk_index: int, content: str,
                    embedding: List[float] = None, metadata: Dict[str, Any] = None) -> 'DocumentChunk':
        """创建新文档块记录"""
        db_manager = PostgreSQLManager()
        
        # 将embedding转换为PostgreSQL向量格式
        embedding_str = None
        if embedding:
            embedding_str = f"[{','.join(map(str, embedding))}]"
        
        query = """
        INSERT INTO document_chunks (document_id, chunk_index, content, content_length, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s::vector, %s)
        RETURNING id, created_at
        """
        
        params = (
            document_id,
            chunk_index,
            content,
            len(content),
            embedding_str,
            json.dumps(metadata or {})
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                document_id=document_id,
                chunk_index=chunk_index,
                content=content,
                content_length=len(content),
                embedding=embedding,
                metadata=metadata or {},
                created_at=result['created_at']
            )
        return None
    
    @classmethod
    async def get_by_document_id(cls, document_id: int) -> List['DocumentChunk']:
        """获取文档的所有块"""
        db_manager = PostgreSQLManager()
        
        query = """
        SELECT id, document_id, chunk_index, content, content_length, 
               embedding::text, metadata, created_at
        FROM document_chunks 
        WHERE document_id = %s 
        ORDER BY chunk_index
        """
        
        results = await db_manager.execute_query(query, (document_id,))
        
        chunks = []
        for result in results:
            # 解析向量数据
            embedding = None
            if result['embedding']:
                try:
                    # 移除方括号并分割
                    embedding_str = result['embedding'].strip('[]')
                    embedding = [float(x) for x in embedding_str.split(',')]
                except:
                    embedding = None
            
            chunks.append(cls(
                id=result['id'],
                document_id=result['document_id'],
                chunk_index=result['chunk_index'],
                content=result['content'],
                content_length=result['content_length'],
                embedding=embedding,
                metadata=json.loads(result['metadata']) if result['metadata'] else {},
                created_at=result['created_at']
            ))
        
        return chunks
    
    @classmethod
    async def search_similar(cls, query_embedding: List[float], limit: int = 5, 
                           similarity_threshold: float = 0.7) -> List[Tuple['DocumentChunk', float]]:
        """向量相似度搜索"""
        db_manager = PostgreSQLManager()
        
        # 将查询向量转换为PostgreSQL向量格式
        query_vector = f"[{','.join(map(str, query_embedding))}]"
        
        query = """
        SELECT id, document_id, chunk_index, content, content_length, 
               embedding::text, metadata, created_at,
               1 - (embedding <=> %s::vector) as similarity
        FROM document_chunks 
        WHERE embedding IS NOT NULL
        AND 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        
        params = (query_vector, query_vector, similarity_threshold, query_vector, limit)
        results = await db_manager.execute_query(query, params)
        
        chunks_with_scores = []
        for result in results:
            # 解析向量数据
            embedding = None
            if result['embedding']:
                try:
                    embedding_str = result['embedding'].strip('[]')
                    embedding = [float(x) for x in embedding_str.split(',')]
                except:
                    embedding = None
            
            chunk = cls(
                id=result['id'],
                document_id=result['document_id'],
                chunk_index=result['chunk_index'],
                content=result['content'],
                content_length=result['content_length'],
                embedding=embedding,
                metadata=json.loads(result['metadata']) if result['metadata'] else {},
                created_at=result['created_at']
            )
            
            chunks_with_scores.append((chunk, result['similarity']))
        
        return chunks_with_scores

@dataclass
class ChatSession:
    """聊天会话模型 - PostgreSQL版本"""
    id: Optional[int] = None
    session_id: str = ""
    user_id: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    async def create(cls, session_id: str, user_id: str = None, title: str = None,
                    metadata: Dict[str, Any] = None) -> 'ChatSession':
        """创建新聊天会话"""
        db_manager = PostgreSQLManager()
        
        query = """
        INSERT INTO chat_sessions (session_id, user_id, title, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        
        params = (
            session_id,
            user_id,
            title,
            json.dumps(metadata or {})
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                session_id=session_id,
                user_id=user_id,
                title=title,
                created_at=result['created_at'],
                updated_at=result['updated_at'],
                metadata=metadata or {}
            )
        return None
    
    @classmethod
    async def get_by_session_id(cls, session_id: str) -> Optional['ChatSession']:
        """根据会话ID获取聊天会话"""
        db_manager = PostgreSQLManager()
        
        query = "SELECT * FROM chat_sessions WHERE session_id = %s"
        result = await db_manager.execute_query(query, (session_id,), fetch_one=True)
        
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
    
    async def update_title(self, title: str):
        """更新会话标题"""
        db_manager = PostgreSQLManager()
        
        query = "UPDATE chat_sessions SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        await db_manager.execute_query(query, (title, self.id))
        self.title = title

@dataclass
class ChatMessage:
    """聊天消息模型 - PostgreSQL版本"""
    id: Optional[int] = None
    session_id: int = 0
    role: MessageRole = MessageRole.USER
    content: str = ""
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    async def create(cls, session_id: int, role: MessageRole, content: str,
                    metadata: Dict[str, Any] = None) -> 'ChatMessage':
        """创建新聊天消息"""
        db_manager = PostgreSQLManager()
        
        query = """
        INSERT INTO chat_messages (session_id, role, content, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at
        """
        
        params = (
            session_id,
            role.value,
            content,
            json.dumps(metadata or {})
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                session_id=session_id,
                role=role,
                content=content,
                created_at=result['created_at'],
                metadata=metadata or {}
            )
        return None
    
    @classmethod
    async def get_by_session_id(cls, session_id: int, limit: int = 50) -> List['ChatMessage']:
        """获取会话的所有消息"""
        db_manager = PostgreSQLManager()
        
        query = """
        SELECT * FROM chat_messages 
        WHERE session_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        
        results = await db_manager.execute_query(query, (session_id, limit))
        
        messages = []
        for result in results:
            messages.append(cls(
                id=result['id'],
                session_id=result['session_id'],
                role=MessageRole(result['role']),
                content=result['content'],
                created_at=result['created_at'],
                metadata=json.loads(result['metadata']) if result['metadata'] else {}
            ))
        
        return list(reversed(messages))  # 返回正序

@dataclass
class RetrievalLog:
    """检索日志模型 - PostgreSQL版本"""
    id: Optional[int] = None
    session_id: Optional[int] = None
    query: str = ""
    retrieved_chunks: List[int] = field(default_factory=list)
    similarity_scores: List[float] = field(default_factory=list)
    response_time: float = 0.0
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.retrieved_chunks is None:
            self.retrieved_chunks = []
        if self.similarity_scores is None:
            self.similarity_scores = []
    
    @classmethod
    async def create(cls, session_id: int, query: str, retrieved_chunks: List[int],
                    similarity_scores: List[float], response_time: float,
                    metadata: Dict[str, Any] = None) -> 'RetrievalLog':
        """创建新检索日志"""
        db_manager = PostgreSQLManager()
        
        query_sql = """
        INSERT INTO retrieval_logs (session_id, query, retrieved_chunks, similarity_scores, response_time, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
        """
        
        params = (
            session_id,
            query,
            json.dumps(retrieved_chunks),
            json.dumps(similarity_scores),
            response_time,
            json.dumps(metadata or {})
        )
        
        result = await db_manager.execute_query(query_sql, params, fetch_one=True)
        
        if result:
            return cls(
                id=result['id'],
                session_id=session_id,
                query=query,
                retrieved_chunks=retrieved_chunks,
                similarity_scores=similarity_scores,
                response_time=response_time,
                created_at=result['created_at'],
                metadata=metadata or {}
            )
        return None

@dataclass
class RAGStats:
    """RAG系统统计信息模型"""
    total_documents: int = 0
    total_chunks: int = 0
    total_sessions: int = 0
    total_messages: int = 0
    avg_response_time: float = 0.0
    documents_by_type: Dict[str, int] = field(default_factory=dict)
    recent_activity: Dict[str, int] = field(default_factory=dict)
    
    @classmethod
    async def calculate_stats(cls) -> 'RAGStats':
        """计算RAG系统统计信息"""
        db_manager = PostgreSQLManager()
        
        # 文档统计
        doc_query = "SELECT COUNT(*) as count FROM documents"
        doc_result = await db_manager.execute_query(doc_query, fetch_one=True)
        total_documents = doc_result['count'] if doc_result else 0
        
        # 文档块统计
        chunk_query = "SELECT COUNT(*) as count FROM document_chunks"
        chunk_result = await db_manager.execute_query(chunk_query, fetch_one=True)
        total_chunks = chunk_result['count'] if chunk_result else 0
        
        # 会话统计
        session_query = "SELECT COUNT(*) as count FROM chat_sessions"
        session_result = await db_manager.execute_query(session_query, fetch_one=True)
        total_sessions = session_result['count'] if session_result else 0
        
        # 消息统计
        message_query = "SELECT COUNT(*) as count FROM chat_messages"
        message_result = await db_manager.execute_query(message_query, fetch_one=True)
        total_messages = message_result['count'] if message_result else 0
        
        # 平均响应时间
        response_time_query = "SELECT AVG(response_time) as avg_time FROM retrieval_logs"
        response_time_result = await db_manager.execute_query(response_time_query, fetch_one=True)
        avg_response_time = float(response_time_result['avg_time']) if response_time_result and response_time_result['avg_time'] else 0.0
        
        # 按类型统计文档
        type_query = "SELECT file_type, COUNT(*) as count FROM documents GROUP BY file_type"
        type_results = await db_manager.execute_query(type_query)
        documents_by_type = {result['file_type']: result['count'] for result in type_results}
        
        # 最近活动统计（最近7天）
        recent_query = """
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM chat_messages 
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        recent_results = await db_manager.execute_query(recent_query)
        recent_activity = {str(result['date']): result['count'] for result in recent_results}
        
        return cls(
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_sessions=total_sessions,
            total_messages=total_messages,
            avg_response_time=avg_response_time,
            documents_by_type=documents_by_type,
            recent_activity=recent_activity
        )

class RAGDatabaseManager:
    """RAG数据库管理器 - PostgreSQL版本"""
    
    def __init__(self):
        self.pg_manager = PostgreSQLManager()
    
    async def init_tables(self):
        """初始化RAG系统数据库表"""
        # 读取并执行PostgreSQL初始化脚本
        try:
            script_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # 分割SQL语句并执行
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            for statement in statements:
                if statement and not statement.startswith('--'):
                    await self.pg_manager.execute_query(statement)
            
            print("✅ RAG系统数据库表初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ RAG系统数据库表初始化失败: {e}")
            return False
    
    async def get_stats(self) -> RAGStats:
        """获取RAG系统统计信息"""
        return await RAGStats.calculate_stats()

# 全局数据库管理器实例
rag_db_manager = RAGDatabaseManager()