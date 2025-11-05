"""
向量存储服务
集成ChromaDB和FAISS，提供文档向量存储和检索功能
"""

import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

# ChromaDB相关导入
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# FAISS相关导入
import faiss

# 本地服务导入
from .rag_service import rag_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreService:
    """向量存储服务类"""
    
    def __init__(self):
        # 初始化ChromaDB客户端
        self.chroma_client = None
        self.chroma_collection = None
        
        # 初始化FAISS索引
        self.faiss_index = None
        self.faiss_id_map = {}  # 映射FAISS ID到文档ID
        
        # 配置参数
        self.embedding_dimension = 2560  # 豆包嵌入模型doubao-embedding-text-240715的向量维度
        self.collection_name = "weplus_documents"
        self.vector_store_path = "data/vector_store"
        
        # 确保数据目录存在
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        # 初始化向量存储
        self._initialize_vector_stores()
        
        logger.info("向量存储服务初始化完成")
    
    def _initialize_vector_stores(self):
        """初始化向量存储系统"""
        try:
            # 初始化ChromaDB
            self._initialize_chromadb()
            
            # 初始化FAISS
            self._initialize_faiss()
            
            logger.info("向量存储系统初始化成功")
        except Exception as e:
            logger.error(f"向量存储系统初始化失败: {str(e)}")
            raise
    
    def _initialize_chromadb(self):
        """初始化ChromaDB"""
        try:
            # 创建ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(
                path=os.path.join(self.vector_store_path, "chromadb")
            )
            
            # 获取或创建集合
            try:
                self.chroma_collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"加载现有ChromaDB集合: {self.collection_name}")
            except:
                # 集合不存在，创建新集合
                self.chroma_collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "WePlus文档向量存储"}
                )
                logger.info(f"创建新ChromaDB集合: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {str(e)}")
            raise
    
    def _initialize_faiss(self):
        """初始化FAISS索引"""
        try:
            faiss_index_path = os.path.join(self.vector_store_path, "faiss_index.bin")
            faiss_map_path = os.path.join(self.vector_store_path, "faiss_id_map.json")
            
            if os.path.exists(faiss_index_path) and os.path.exists(faiss_map_path):
                # 加载现有索引
                self.faiss_index = faiss.read_index(faiss_index_path)
                with open(faiss_map_path, 'r', encoding='utf-8') as f:
                    self.faiss_id_map = json.load(f)
                logger.info("加载现有FAISS索引")
            else:
                # 创建新索引
                self.faiss_index = faiss.IndexFlatIP(self.embedding_dimension)  # 内积相似度
                self.faiss_id_map = {}
                logger.info("创建新FAISS索引")
                
        except Exception as e:
            logger.error(f"FAISS初始化失败: {str(e)}")
            raise
    
    async def add_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加文档到向量存储
        
        Args:
            document_data: 包含文档完整信息的字典
                - id: 文档ID
                - title: 文档标题
                - content: 原始内容
                - chunks: 文档分块列表
                - embeddings: 嵌入向量列表
                - metadata: 文档元数据
                
        Returns:
            添加结果
        """
        try:
            document_id = document_data["id"]
            chunks = document_data["chunks"]
            embeddings = document_data["embeddings"]
            metadata = document_data.get("metadata", {})
            
            if not chunks:
                raise ValueError("文档分块不能为空")
            
            if not embeddings or len(embeddings) != len(chunks):
                raise ValueError("嵌入向量与分块数量不匹配")
            
            # 添加到ChromaDB
            chroma_result = await self._add_to_chromadb(
                document_id, chunks, embeddings, metadata
            )
            
            # 添加到FAISS
            faiss_result = await self._add_to_faiss(
                document_id, chunks, embeddings, metadata
            )
            
            # 保存FAISS索引
            await self._save_faiss_index()
            
            result = {
                "document_id": document_id,
                "title": document_data.get("title", "未命名文档"),
                "chunks_count": len(chunks),
                "embeddings_count": len(embeddings),
                "chromadb_status": chroma_result,
                "faiss_status": faiss_result,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"文档 {document_id} 添加到向量存储成功，块数: {len(chunks)}")
            return result
            
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {str(e)}")
            raise
    
    async def _add_to_chromadb(
        self, 
        document_id: str, 
        chunks: List[str], 
        embeddings: List[List[float]], 
        metadata: Dict[str, Any] = None
    ) -> str:
        """添加到ChromaDB"""
        try:
            # 生成唯一ID，避免重复
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ids = [f"{document_id}_{i}_{timestamp}" for i in range(len(chunks))]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_length": len(chunk),
                    "timestamp": datetime.now().isoformat()
                }
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)
            
            # 添加到集合
            self.chroma_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            
            return "success"
            
        except Exception as e:
            logger.error(f"ChromaDB添加失败: {str(e)}")
            return f"error: {str(e)}"
    
    async def _add_to_faiss(
        self, 
        document_id: str, 
        chunks: List[str], 
        embeddings: List[List[float]], 
        metadata: Dict[str, Any] = None
    ) -> str:
        """添加到FAISS"""
        try:
            # 转换嵌入向量为numpy数组
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # 检查向量维度
            if embeddings_array.shape[1] != self.embedding_dimension:
                raise ValueError(f"向量维度不匹配: 期望 {self.embedding_dimension}, 实际 {embeddings_array.shape[1]}")
            
            # 归一化向量（用于内积相似度）
            faiss.normalize_L2(embeddings_array)
            
            # 添加到索引
            start_id = self.faiss_index.ntotal
            self.faiss_index.add(embeddings_array)
            
            # 更新ID映射，使用时间戳避免重复
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for i, chunk in enumerate(chunks):
                faiss_id = start_id + i
                unique_key = f"{document_id}_{i}_{timestamp}"
                self.faiss_id_map[str(faiss_id)] = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk,
                    "unique_key": unique_key,
                    "metadata": metadata or {}
                }
            
            return "success"
            
        except Exception as e:
            logger.error(f"FAISS添加失败: {str(e)}")
            logger.error(f"FAISS错误详情: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"FAISS错误堆栈: {traceback.format_exc()}")
            return f"error: {str(e)}"
    
    async def search_similar(
        self, 
        query: str, 
        top_k: int = 5, 
        use_chromadb: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_chromadb: 是否使用ChromaDB（否则使用FAISS）
            
        Returns:
            相似文档列表
        """
        try:
            logger.info(f"开始向量搜索，查询: {query[:50]}...")
            logger.info(f"使用{'ChromaDB' if use_chromadb else 'FAISS'}，top_k: {top_k}")
            
            # 生成查询向量
            logger.info("正在生成查询向量...")
            query_embeddings = await rag_service.generate_embeddings([query])
            if not query_embeddings:
                logger.error("查询向量生成失败：返回空列表")
                raise ValueError("查询向量生成失败")
            
            query_embedding = query_embeddings[0]
            logger.info(f"查询向量生成成功，维度: {len(query_embedding)}")
            
            if use_chromadb:
                logger.info("使用ChromaDB进行搜索...")
                results = await self._search_chromadb(query_embedding, top_k)
                logger.info(f"ChromaDB搜索完成，找到 {len(results)} 个结果")
                return results
            else:
                logger.info("使用FAISS进行搜索...")
                results = await self._search_faiss(query_embedding, top_k)
                logger.info(f"FAISS搜索完成，找到 {len(results)} 个结果")
                return results
                
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return []
    
    async def _search_chromadb(
        self, 
        query_embedding: List[float], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """使用ChromaDB搜索"""
        try:
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            similar_docs = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    similar_docs.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "similarity": 1 - results["distances"][0][i],  # 转换为相似度
                        "source": "chromadb"
                    })
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"ChromaDB搜索失败: {str(e)}")
            return []
    
    async def _search_faiss(
        self, 
        query_embedding: List[float], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """使用FAISS搜索"""
        try:
            # 转换查询向量
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # 搜索
            similarities, indices = self.faiss_index.search(query_vector, top_k)
            
            similar_docs = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and str(idx) in self.faiss_id_map:
                    doc_info = self.faiss_id_map[str(idx)]
                    similar_docs.append({
                        "content": doc_info["content"],
                        "metadata": doc_info["metadata"],
                        "similarity": float(similarities[0][i]),
                        "source": "faiss"
                    })
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"FAISS搜索失败: {str(e)}")
            return []
    
    async def _save_faiss_index(self):
        """保存FAISS索引"""
        try:
            faiss_index_path = os.path.join(self.vector_store_path, "faiss_index.bin")
            faiss_map_path = os.path.join(self.vector_store_path, "faiss_id_map.json")
            
            # 保存索引
            faiss.write_index(self.faiss_index, faiss_index_path)
            
            # 保存ID映射
            with open(faiss_map_path, 'w', encoding='utf-8') as f:
                json.dump(self.faiss_id_map, f, ensure_ascii=False, indent=2)
            
            logger.info("FAISS索引保存成功")
            
        except Exception as e:
            logger.error(f"FAISS索引保存失败: {str(e)}")
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除结果
        """
        try:
            # 从ChromaDB删除
            chroma_result = await self._delete_from_chromadb(document_id)
            
            # 从FAISS删除（重建索引）
            faiss_result = await self._delete_from_faiss(document_id)
            
            result = {
                "document_id": document_id,
                "chromadb_status": chroma_result,
                "faiss_status": faiss_result,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"文档 {document_id} 删除成功")
            return result
            
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            raise
    
    async def _delete_from_chromadb(self, document_id: str) -> str:
        """从ChromaDB删除文档"""
        try:
            # 查询文档的所有分块ID
            results = self.chroma_collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                self.chroma_collection.delete(ids=results["ids"])
                return f"deleted {len(results['ids'])} chunks"
            else:
                return "no chunks found"
                
        except Exception as e:
            logger.error(f"ChromaDB删除失败: {str(e)}")
            return f"error: {str(e)}"
    
    async def _delete_from_faiss(self, document_id: str) -> str:
        """从FAISS删除文档（通过重建索引）"""
        try:
            # 找到要删除的文档分块
            ids_to_delete = []
            for faiss_id, doc_info in self.faiss_id_map.items():
                if doc_info["document_id"] == document_id:
                    ids_to_delete.append(faiss_id)
            
            if not ids_to_delete:
                return "no chunks found"
            
            # 从映射中删除
            for faiss_id in ids_to_delete:
                del self.faiss_id_map[faiss_id]
            
            # 重建FAISS索引
            await self._rebuild_faiss_index()
            
            return f"deleted {len(ids_to_delete)} chunks"
            
        except Exception as e:
            logger.error(f"FAISS删除失败: {str(e)}")
            return f"error: {str(e)}"
    
    async def _rebuild_faiss_index(self):
        """重建FAISS索引"""
        try:
            # 创建新索引
            new_index = faiss.IndexFlatIP(self.embedding_dimension)
            new_id_map = {}
            
            # 重新添加所有向量
            if self.faiss_id_map:
                contents = [info["content"] for info in self.faiss_id_map.values()]
                embeddings = await rag_service.generate_embeddings(contents)
                
                if embeddings:
                    embeddings_array = np.array(embeddings, dtype=np.float32)
                    faiss.normalize_L2(embeddings_array)
                    new_index.add(embeddings_array)
                    
                    # 重建ID映射
                    for i, (old_id, doc_info) in enumerate(self.faiss_id_map.items()):
                        new_id_map[str(i)] = doc_info
            
            # 替换索引和映射
            self.faiss_index = new_index
            self.faiss_id_map = new_id_map
            
            # 保存新索引
            await self._save_faiss_index()
            
            logger.info("FAISS索引重建完成")
            
        except Exception as e:
            logger.error(f"FAISS索引重建失败: {str(e)}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取向量存储统计信息"""
        try:
            # ChromaDB统计
            chroma_count = self.chroma_collection.count() if self.chroma_collection else 0
            
            # FAISS统计
            faiss_count = self.faiss_index.ntotal if self.faiss_index else 0
            
            # 文档统计
            document_ids = set()
            for doc_info in self.faiss_id_map.values():
                document_ids.add(doc_info["document_id"])
            
            stats = {
                "chromadb_chunks": chroma_count,
                "faiss_chunks": faiss_count,
                "total_documents": len(document_ids),
                "vector_dimension": self.embedding_dimension,
                "storage_path": self.vector_store_path,
                "timestamp": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
    
    async def get_collection_stats(self, collection_name: str = None) -> Dict[str, Any]:
        """获取ChromaDB集合统计信息"""
        try:
            if not self.chroma_collection:
                return {
                    "name": collection_name or self.collection_name,
                    "count": 0,
                    "document_count": 0,
                    "vector_count": 0,
                    "size_mb": 0,
                    "status": "not_initialized"
                }
            
            count = self.chroma_collection.count()
            return {
                "name": collection_name or self.collection_name,
                "count": count,
                "document_count": count,
                "vector_count": count,
                "size_mb": 0,  # ChromaDB doesn't provide size info easily
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"获取ChromaDB集合统计失败: {str(e)}")
            return {
                "name": collection_name or self.collection_name,
                "count": 0,
                "document_count": 0,
                "vector_count": 0,
                "size_mb": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def get_faiss_stats(self) -> Dict[str, Any]:
        """获取FAISS索引统计信息"""
        try:
            if not self.faiss_index:
                return {
                    "index_type": "IVFFlat",
                    "dimension": self.embedding_dimension,
                    "count": 0,
                    "document_count": 0,
                    "vector_count": 0,
                    "size_mb": 0,
                    "status": "not_initialized"
                }
            
            count = self.faiss_index.ntotal
            index_size = os.path.getsize(os.path.join(self.vector_store_path, "faiss_index.index")) if os.path.exists(os.path.join(self.vector_store_path, "faiss_index.index")) else 0
            
            return {
                "index_type": "IVFFlat",
                "dimension": self.embedding_dimension,
                "count": count,
                "document_count": len(set(doc_info["document_id"] for doc_info in self.faiss_id_map.values())),
                "vector_count": count,
                "size_mb": round(index_size / (1024 * 1024), 2),
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"获取FAISS索引统计失败: {str(e)}")
            return {
                "index_type": "IVFFlat",
                "dimension": self.embedding_dimension,
                "count": 0,
                "document_count": 0,
                "vector_count": 0,
                "size_mb": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "chromadb": False,
                "faiss": False,
                "overall": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # 检查ChromaDB
            try:
                if self.chroma_collection:
                    self.chroma_collection.count()
                    health_status["chromadb"] = True
            except Exception as e:
                logger.error(f"ChromaDB健康检查失败: {str(e)}")
            
            # 检查FAISS
            try:
                if self.faiss_index:
                    _ = self.faiss_index.ntotal
                    health_status["faiss"] = True
            except Exception as e:
                logger.error(f"FAISS健康检查失败: {str(e)}")
            
            health_status["overall"] = health_status["chromadb"] and health_status["faiss"]
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {"overall": False, "error": str(e)}

# 全局向量存储服务实例
vector_store_service = VectorStoreService()