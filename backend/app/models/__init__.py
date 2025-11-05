"""
Models package for WePlus RAG system
"""
from .rag_models import (
    DocumentProcessRequest,
    DocumentProcessResponse,
    QueryRequest,
    QueryResponse,
    DocumentChunk,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DocumentMetadata,
    VectorStoreStats,
    HealthCheckResponse,
    SystemStats,
    ErrorResponse
)

__all__ = [
    "DocumentProcessRequest",
    "DocumentProcessResponse", 
    "QueryRequest",
    "QueryResponse",
    "DocumentChunk",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "DocumentMetadata",
    "VectorStoreStats",
    "HealthCheckResponse",
    "SystemStats",
    "ErrorResponse"
]