"""
PostgreSQL向量存储服务
使用pgvector扩展提供文档向量存储和检索功能
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

# 数据库相关导入
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from database.config import get_db_connection

# 本地服务导入
from .rag_service import rag_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLVectorService:
    """PostgreSQL向量存储服务类"""
    
    def __init__(self):
        # 配置参数
        self.embedding_dimension = 2560  # 豆包嵌入模型doubao-embedding-text-240715的向量维度
        
        logger.info("PostgreSQL向量存储服务初始化完成")
    
    async def add_document(self, document_id: str, chunks: List[str], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        添加文档到向量存储
        
        Args:
            document_id: 文档ID
            chunks: 文档分块列表
            metadata: 文档元数据
            
        Returns:
            Dict: 添加结果
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 为每个分块生成嵌入向量并存储
                    for i, chunk in enumerate(chunks):
                        # 生成嵌入向量
                        embedding = await rag_service.get_embedding(chunk)
                        if embedding is None:
                            logger.warning(f"无法为文档 {document_id} 的分块 {i} 生成嵌入向量")
                            continue
                        
                        # 确保向量维度正确
                        if len(embedding) != self.embedding_dimension:
                            logger.error(f"向量维度不匹配: 期望 {self.embedding_dimension}, 实际 {len(embedding)}")
                            continue
                        
                        # 插入到数据库
                        query = """
                            INSERT INTO document_chunks (document_id, chunk_index, content, embedding, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(
                            query,
                            (document_id, i, chunk, embedding, json.dumps(metadata or {}))
                        )
                    
                    conn.commit()
                    logger.info(f"成功添加文档 {document_id} 的 {len(chunks)} 个分块到向量存储")
                    return {
                        "success": True,
                        "document_id": document_id,
                        "chunks_count": len(chunks)
                    }
                
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_similar(self, query: str, top_k: int = 10, similarity_threshold: float = 0.7, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        语义搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            filters: 过滤条件
            
        Returns:
            List[Dict]: 搜索结果
        """
        try:
            # 生成查询向量
            query_embedding = await rag_service.get_embedding(query)
            if query_embedding is None:
                logger.error("无法生成查询向量")
                return []
            
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 使用余弦相似度搜索
                    search_query = """
                        SELECT 
                            dc.document_id,
                            dc.content,
                            dc.metadata,
                            1 - (dc.embedding <=> %s::vector) as similarity
                        FROM document_chunks dc
                        WHERE 1 - (dc.embedding <=> %s::vector) > %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                    """
                    
                    cursor.execute(search_query, (query_embedding, query_embedding, similarity_threshold, query_embedding, top_k))
                    results = cursor.fetchall()
                    
                    # 格式化结果
                    formatted_results = []
                    for row in results:
                        # 处理metadata字段 - 可能是字符串或已经是字典
                        metadata = row[2]
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except (json.JSONDecodeError, TypeError):
                                metadata = {}
                        elif not isinstance(metadata, dict):
                            metadata = {}
                        
                        formatted_results.append({
                            "document_id": row[0],
                            "content": row[1],
                            "metadata": metadata,
                            "similarity": float(row[3])
                        })
                    
                    return formatted_results
                
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            Dict: 删除结果
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 删除文档的所有分块
                    delete_query = "DELETE FROM document_chunks WHERE document_id = %s"
                    cursor.execute(delete_query, (document_id,))
                    deleted_count = cursor.rowcount
                    
                    conn.commit()
                    logger.info(f"成功删除文档 {document_id} 的 {deleted_count} 个分块")
                    
                    return {
                        "success": True,
                        "document_id": document_id,
                        "deleted_chunks": deleted_count
                    }
                
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取向量存储统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取总分块数
                    cursor.execute("SELECT COUNT(*) FROM document_chunks")
                    total_chunks = cursor.fetchone()[0]
                    
                    # 获取文档数
                    cursor.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks")
                    total_documents = cursor.fetchone()[0]
                    
                    # 获取总内容长度 (通过计算content字段长度)
                    cursor.execute("SELECT SUM(LENGTH(content)) FROM document_chunks")
                    total_content_length = cursor.fetchone()[0] or 0
                    
                    return {
                        "total_documents": total_documents,
                        "total_vectors": total_chunks,  # 向量数量等于分块数量
                        "total_chunks": total_chunks,
                        "total_content_length": total_content_length,
                        "embedding_dimension": self.embedding_dimension,
                        "vector_dimension": self.embedding_dimension,
                        "embedding_model": "豆包嵌入模型",
                        "index_size_mb": round(total_content_length / (1024 * 1024), 2),  # 估算索引大小
                        "last_updated": datetime.now().isoformat(),
                        "timestamp": datetime.now().isoformat()
                    }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_document_chunks(self) -> List[Dict[str, Any]]:
        """
        获取所有文档块信息
        
        Returns:
            List[Dict]: 文档块列表
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取所有文档块信息
                    cursor.execute("""
                        SELECT 
                            document_id,
                            chunk_index,
                            content,
                            LENGTH(content) as content_length,
                            metadata,
                            created_at
                        FROM document_chunks
                        ORDER BY document_id, chunk_index
                    """)
                    
                    chunks = []
                    for row in cursor.fetchall():
                        try:
                            # 安全处理metadata
                            metadata = {}
                            if row[4]:
                                try:
                                    metadata = json.loads(row[4])
                                except (json.JSONDecodeError, TypeError):
                                    metadata = {}
                            
                            chunk_data = {
                                "document_id": row[0],
                                "chunk_index": row[1],
                                "content": row[2],
                                "content_length": row[3],
                                "metadata": metadata,
                                "created_at": row[5] if row[5] else datetime.now()  # 使用数据库中的created_at或当前时间
                            }
                            chunks.append(chunk_data)
                        except Exception as chunk_error:
                            logger.warning(f"处理文档块时出错: {chunk_error}")
                            continue
                    
                    return chunks
                
        except Exception as e:
            logger.error(f"获取文档块失败: {str(e)}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 健康状态
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 测试数据库连接
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    
                    # 检查pgvector扩展
                    cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    vector_ext = cursor.fetchone()
                    
                    return {
                        "database": True,
                        "pgvector": vector_ext is not None,
                        "overall": vector_ext is not None,
                        "timestamp": datetime.now().isoformat()
                    }
                
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                "database": False,
                "pgvector": False,
                "overall": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# 全局PostgreSQL向量服务实例
postgresql_vector_service = PostgreSQLVectorService()