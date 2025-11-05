"""
WePlus 后台管理系统 - RAG数据库管理API
提供知识条目CRUD、向量化处理、知识库管理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
import json
import hashlib
import numpy as np
from pathlib import Path
import asyncio
from app.core.config import settings

# 导入数据库配置和认证
from database.rag_models import Document, DocumentChunk, ChatSession, ChatMessage, RetrievalLog, RAGDatabaseManager
from app.api.admin_user_api import verify_token, get_current_user, require_admin

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/admin/rag", tags=["RAG知识库管理"])

# 初始化RAG数据库管理器
rag_manager = RAGDatabaseManager()

# Pydantic模型定义
class DocumentCreateRequest(BaseModel):
    """文档创建请求模型"""
    title: str
    content: str
    source_type: str = "manual"  # manual, file, web
    source_url: Optional[str] = None
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('title')
    def validate_title(cls, v):
        if len(v) < 1 or len(v) > 200:
            raise ValueError('标题长度必须在1-200个字符之间')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if len(v) < 10:
            raise ValueError('内容长度至少10个字符')
        return v

class DocumentUpdateRequest(BaseModel):
    """文档更新请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: int
    title: str
    content: str
    source_type: str
    source_url: Optional[str]
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: int
    chunk_count: int
    processing_status: str

class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    documents: List[DocumentResponse]
    total: int
    page: int
    limit: int
    total_pages: int

class ChunkResponse(BaseModel):
    """文档块响应模型"""
    id: int
    document_id: int
    content: str
    chunk_index: int
    token_count: int
    embedding_status: str
    created_at: datetime

class ChatSessionResponse(BaseModel):
    """聊天会话响应模型"""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class ChatMessageResponse(BaseModel):
    """聊天消息响应模型"""
    id: int
    session_id: int
    role: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

class RAGStatsResponse(BaseModel):
    """RAG统计响应模型"""
    total_documents: int
    total_chunks: int
    total_sessions: int
    total_messages: int
    documents_by_category: Dict[str, int]
    recent_activity: Dict[str, int]

# API端点
@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """创建新文档"""
    try:
        # 创建文档
        document = Document.create(
            title=document_data.title,
            content=document_data.content,
            source_type=document_data.source_type,
            source_url=document_data.source_url,
            category=document_data.category,
            tags=document_data.tags,
            metadata=document_data.metadata,
            created_by=current_user["user_id"]
        )
        
        # 后台任务：处理文档分块和向量化
        background_tasks.add_task(process_document_chunks, document.id)
        
        logger.info(f"文档创建成功: {document_data.title} by user {current_user['user_id']}")
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            source_type=document.source_type,
            source_url=document.source_url,
            category=document.category,
            tags=document.tags,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            created_by=document.created_by,
            chunk_count=0,
            processing_status="processing"
        )
    except Exception as e:
        logger.error(f"创建文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建文档失败"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    source_type: Optional[str] = Query(None, description="来源类型筛选"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取文档列表"""
    try:
        # 构建筛选条件
        filters = {}
        if category:
            filters['category'] = category
        if source_type:
            filters['source_type'] = source_type
        
        # 非管理员只能看到自己创建的文档
        if current_user.get("role") not in ["admin", "super_admin"]:
            filters['created_by'] = current_user["user_id"]
        
        # 获取文档列表
        documents, total = Document.get_paginated(
            page=page,
            limit=limit,
            search=search,
            filters=filters
        )
        
        # 转换为响应模型
        document_responses = []
        for doc in documents:
            chunk_count = DocumentChunk.count_by_document(doc.id)
            document_responses.append(DocumentResponse(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                source_type=doc.source_type,
                source_url=doc.source_url,
                category=doc.category,
                tags=doc.tags,
                metadata=doc.metadata,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                created_by=doc.created_by,
                chunk_count=chunk_count,
                processing_status="completed"
            ))
        
        total_pages = (total + limit - 1) // limit
        
        return DocumentListResponse(
            documents=document_responses,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        # 根据安全模式决定行为：关闭则抛错，开启则返回空列表兜底
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return DocumentListResponse(
            documents=[],
            total=0,
            page=page,
            limit=limit,
            total_pages=0
        )

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取文档详情"""
    try:
        document = Document.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            document.created_by != current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限访问此文档"
            )
        
        chunk_count = DocumentChunk.count_by_document(document.id)
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            source_type=document.source_type,
            source_url=document.source_url,
            category=document.category,
            tags=document.tags,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            created_by=document.created_by,
            chunk_count=chunk_count,
            processing_status="completed"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文档详情失败"
        )

@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更新文档"""
    try:
        document = Document.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            document.created_by != current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限修改此文档"
            )
        
        # 更新文档
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            document.update(**update_dict)
            
            # 如果内容发生变化，重新处理分块
            if 'content' in update_dict:
                background_tasks.add_task(process_document_chunks, document.id)
        
        chunk_count = DocumentChunk.count_by_document(document.id)
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            source_type=document.source_type,
            source_url=document.source_url,
            category=document.category,
            tags=document.tags,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            created_by=document.created_by,
            chunk_count=chunk_count,
            processing_status="completed"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新文档失败"
        )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """删除文档"""
    try:
        document = Document.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            document.created_by != current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限删除此文档"
            )
        
        # 删除文档及其相关数据
        document.delete()
        
        logger.info(f"文档删除成功: {document.title} by user {current_user['user_id']}")
        
        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除文档失败"
        )

@router.get("/documents/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取文档的分块信息"""
    try:
        document = Document.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            document.created_by != current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限访问此文档"
            )
        
        chunks = DocumentChunk.get_by_document(document_id)
        
        return [
            ChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                token_count=chunk.token_count,
                embedding_status="completed" if chunk.embedding else "pending",
                created_at=chunk.created_at
            )
            for chunk in chunks
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档分块失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文档分块失败"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取聊天会话列表（管理员权限）"""
    try:
        filters = {}
        if user_id:
            filters['user_id'] = user_id
        
        sessions, total = ChatSession.get_paginated(
            page=page,
            limit=limit,
            filters=filters
        )
        
        session_responses = []
        for session in sessions:
            message_count = ChatMessage.count_by_session(session.id)
            session_responses.append(ChatSessionResponse(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count
            ))
        
        return session_responses
    except Exception as e:
        logger.error(f"获取聊天会话列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取聊天会话列表失败"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取会话消息（管理员权限）"""
    try:
        session = ChatSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        messages = ChatMessage.get_by_session(session_id)
        
        return [
            ChatMessageResponse(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                metadata=message.metadata,
                created_at=message.created_at
            )
            for message in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话消息失败"
        )

@router.get("/stats", response_model=RAGStatsResponse)
async def get_rag_stats(
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取RAG系统统计信息（管理员权限）"""
    try:
        stats = rag_manager.get_stats()
        return RAGStatsResponse(**stats)
    except Exception as e:
        logger.error(f"获取RAG统计失败: {e}")
        # 根据安全模式决定行为：关闭则抛错，开启则返回空统计兜底
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return RAGStatsResponse(
            total_documents=0,
            total_chunks=0,
            total_sessions=0,
            total_messages=0,
            documents_by_category={},
            recent_activity={}
        )

@router.post("/search")
async def search_documents(
    query: str,
    limit: int = Query(10, ge=1, le=50, description="返回结果数量"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="相似度阈值"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """搜索相关文档"""
    try:
        # 使用RAG管理器进行向量搜索
        results = rag_manager.search_similar_chunks(
            query=query,
            limit=limit,
            threshold=threshold
        )
        
        # 记录检索日志
        RetrievalLog.create(
            user_id=current_user["user_id"],
            query=query,
            results_count=len(results),
            metadata={"threshold": threshold, "limit": limit}
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"文档搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档搜索失败"
        )

# 后台任务函数
async def process_document_chunks(document_id: int):
    """处理文档分块和向量化"""
    try:
        document = Document.get_by_id(document_id)
        if not document:
            return
        
        # 删除现有分块
        DocumentChunk.delete_by_document(document_id)
        
        # 重新分块
        chunks = rag_manager.chunk_text(document.content)
        
        # 创建分块记录
        for i, chunk_content in enumerate(chunks):
            chunk = DocumentChunk.create(
                document_id=document_id,
                content=chunk_content,
                chunk_index=i,
                token_count=len(chunk_content.split())
            )
            
            # 生成向量嵌入
            try:
                embedding = rag_manager.generate_embedding(chunk_content)
                chunk.update_embedding(embedding)
            except Exception as e:
                logger.error(f"生成嵌入失败 chunk {chunk.id}: {e}")
        
        logger.info(f"文档分块处理完成: document_id={document_id}, chunks={len(chunks)}")
    except Exception as e:
        logger.error(f"处理文档分块失败: {e}")

@router.post("/reprocess/{document_id}")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """重新处理文档分块（管理员权限）"""
    try:
        document = Document.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 后台任务：重新处理文档分块
        background_tasks.add_task(process_document_chunks, document_id)
        
        return {"message": "文档重新处理任务已启动"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新处理文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新处理文档失败"
        )
