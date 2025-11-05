"""
RAG系统数据模型定义
包含文档处理、查询请求、响应等相关模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentProcessRequest(BaseModel):
    """文档处理请求模型"""
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="文档元数据")

class DocumentProcessResponse(BaseModel):
    """文档处理响应模型"""
    success: bool = Field(default=True, description="处理是否成功")
    document_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    chunk_count: int = Field(..., description="文档块数量")
    processing_time: float = Field(..., description="处理时间(秒)")
    processed_at: str = Field(..., description="处理时间戳")
    message: str = Field(..., description="处理结果消息")

class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., description="查询内容")
    top_k: Optional[int] = Field(default=5, description="返回结果数量")
    similarity_threshold: Optional[float] = Field(default=0.0, description="相似度阈值")

class QueryResponse(BaseModel):
    """查询响应模型"""
    query: str = Field(..., description="原始查询")
    results: List[Dict[str, Any]] = Field(..., description="查询结果")
    total_results: int = Field(..., description="结果总数")
    search_time: float = Field(..., description="搜索耗时(秒)")
    message: str = Field(..., description="查询结果消息")

class DocumentChunk(BaseModel):
    """文档块模型"""
    content: str = Field(..., description="块内容")
    chunk_index: int = Field(..., description="块索引")
    document_id: str = Field(..., description="所属文档ID")
    embedding: Optional[List[float]] = Field(default=None, description="嵌入向量")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="块元数据")

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[str] = Field(default=None, description="时间戳")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="对话历史")
    use_rag: bool = Field(default=True, description="是否使用RAG")
    stream: bool = Field(default=False, description="是否流式输出")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str = Field(..., description="助手回复")
    timestamp: str = Field(..., description="响应时间戳")
    token_usage: Optional[Dict[str, int]] = Field(default=None, description="Token使用统计")
    sources_used: Optional[List[Dict[str, Any]]] = Field(default=None, description="使用的文档来源")
    conversation_id: Optional[str] = Field(default=None, description="对话ID")

class DocumentMetadata(BaseModel):
    """文档元数据模型"""
    title: str = Field(..., description="文档标题")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    upload_time: str = Field(..., description="上传时间")
    processed_time: Optional[str] = Field(default=None, description="处理时间")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    category: Optional[str] = Field(default=None, description="分类")

class VectorStoreStats(BaseModel):
    """向量存储统计模型"""
    total_documents: int = Field(..., description="文档总数")
    total_chunks: int = Field(..., description="文档块总数")
    total_vectors: int = Field(..., description="向量总数")
    index_size: int = Field(..., description="索引大小(字节)")
    last_updated: str = Field(..., description="最后更新时间")

class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    overall: bool = Field(..., description="整体健康状态")
    deepseek_api: bool = Field(..., description="DeepSeek API状态")
    embedding_service: bool = Field(..., description="嵌入服务状态")
    vector_store: bool = Field(..., description="向量存储状态")
    database: bool = Field(..., description="数据库状态")
    timestamp: str = Field(..., description="检查时间戳")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="详细信息")

class SystemStats(BaseModel):
    """系统统计模型"""
    total_documents: int = Field(..., description="文档总数")
    total_chunks: int = Field(..., description="文档块总数")
    total_content_length: int = Field(..., description="内容总长度")
    average_chunks_per_doc: float = Field(..., description="平均每文档块数")
    rag_service_config: Dict[str, Any] = Field(..., description="RAG服务配置")
    timestamp: str = Field(..., description="统计时间戳")

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: str = Field(..., description="错误时间戳")
    request_id: Optional[str] = Field(default=None, description="请求ID")