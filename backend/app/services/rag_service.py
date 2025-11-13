"""
RAG系统核心服务
集成DeepSeek聊天API和豆包嵌入模型
使用PostgreSQL pgvector替代ChromaDB
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import numpy as np
from datetime import datetime, timedelta
import logging
import hashlib
import json
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入性能监控
try:
    from .performance_monitor import performance_monitor
except ImportError:
    performance_monitor = None
    logger.warning("性能监控模块未找到，将跳过性能监控功能")

class RAGService:
    """RAG系统核心服务类"""
    
    def __init__(self):
        # 从环境变量加载配置
        from dotenv import load_dotenv
        import os
        
        # 确保环境变量已加载
        load_dotenv()
        
        # DeepSeek API配置
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        
        # 豆包嵌入模型配置
        self.embedding_client = OpenAI(
            api_key=os.getenv("ARK_API_KEY"),
            base_url=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        )
        
        # 模型配置
        self.chat_model = "deepseek-chat"
        self.embedding_model = os.getenv("ARK_EMBEDDING_MODEL", "doubao-embedding-text-240715")
        
        # RAG系统配置
        self.max_context_length = 128000  # DeepSeek-V3.2-Exp上下文长度
        self.max_output_tokens = 4000     # 默认输出长度
        self.chunk_size = 1000           # 文档分块大小
        self.chunk_overlap = 200         # 分块重叠大小
        self.top_k_retrieval = 5         # 检索返回的top-k文档数量
        
        # 简单缓存机制
        self.query_cache = {}
        self.embedding_cache = {}
        self.cache_ttl = 3600  # 缓存1小时
        self.max_cache_size = 1000  # 最大缓存条目数
        
        logger.info("RAG服务初始化完成")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本嵌入向量（带缓存和性能监控）
        """
        start_time = time.time()
        try:
            embeddings = []
            uncached_texts = []
            uncached_indices = []
            cache_hits = 0
            
            # 检查缓存
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self.embedding_cache:
                    cached_item = self.embedding_cache[cache_key]
                    if self._is_cache_valid(cached_item['timestamp']):
                        embeddings.append(cached_item['embedding'])
                        cache_hits += 1
                        if performance_monitor:
                            performance_monitor.record_cache_hit()
                        continue
                
                # 未缓存或已过期
                uncached_texts.append(text)
                uncached_indices.append(i)
                embeddings.append(None)  # 占位符
                if performance_monitor:
                    performance_monitor.record_cache_miss()
            
            # 批量处理未缓存的文本
            if uncached_texts:
                logger.info(f"生成 {len(uncached_texts)} 个新嵌入向量")
                response = await asyncio.to_thread(
                    self.embedding_client.embeddings.create,
                    model=self.embedding_model,
                    input=uncached_texts
                )
                
                # 处理响应并更新缓存
                for i, embedding_data in enumerate(response.data):
                    embedding = embedding_data.embedding
                    original_index = uncached_indices[i]
                    embeddings[original_index] = embedding
                    
                    # 更新缓存
                    cache_key = self._get_cache_key(uncached_texts[i])
                    self.embedding_cache[cache_key] = {
                        'embedding': embedding,
                        'timestamp': time.time()
                    }
                
                # 清理过期缓存
                self._cleanup_cache()
            
            # 记录性能指标
            if performance_monitor:
                elapsed_time = time.time() - start_time
                performance_monitor.record_embedding_generation(
                    count=len(texts),
                    from_cache=cache_hits
                )
            
            logger.info(f"嵌入向量生成完成: {len(texts)} 个文本, 缓存命中: {cache_hits}")
            return embeddings
            
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {str(e)}")
            if performance_monitor:
                performance_monitor.record_error("embedding_generation")
            raise
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取单个文本的嵌入向量
        """
        try:
            embeddings = await self.generate_embeddings([text])
            return embeddings[0] if embeddings else None
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {str(e)}")
            return None
    
    async def process_document(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理文档：分块、生成嵌入向量
        """
        try:
            logger.info("开始处理文档")
            start_time = time.time()
            
            # 文档分块
            chunks = self._split_text(content)
            logger.info(f"文档分块完成，共 {len(chunks)} 个块")
            
            # 生成嵌入向量
            embeddings = await self.generate_embeddings(chunks)
            logger.info(f"嵌入向量生成完成")
            
            # 构建处理结果
            result = {
                "chunks": chunks,
                "embeddings": embeddings,
                "chunk_count": len(chunks),
                "processed_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # 记录性能指标
            if performance_monitor:
                elapsed_time = time.time() - start_time
                performance_monitor.record_document_processing(
                    content_length=len(content),
                    chunk_count=len(chunks),
                    elapsed_time=elapsed_time
                )
            
            logger.info(f"文档处理完成，耗时: {time.time() - start_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            if performance_monitor:
                performance_monitor.record_error("document_processing")
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """
        将文本分割成块
        """
        if not text:
            return []
        
        # 简单的分块策略：按段落和句子分割
        chunks = []
        current_chunk = ""
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # 如果当前块加上新段落不超过限制，则添加
            if len(current_chunk) + len(paragraph) <= self.chunk_size:
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果段落本身就很长，需要进一步分割
                if len(paragraph) > self.chunk_size:
                    sentences = paragraph.split('。')
                    temp_chunk = ""
                    
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) <= self.chunk_size:
                            if temp_chunk:
                                temp_chunk += '。' + sentence
                            else:
                                temp_chunk = sentence
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip() + '。')
                            temp_chunk = sentence
                    
                    if temp_chunk:
                        current_chunk = temp_chunk.strip()
                        if not current_chunk.endswith('。'):
                            current_chunk += '。'
                    else:
                        current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 处理重叠
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    overlapped_chunks.append(chunk)
                else:
                    # 添加前一个块的结尾作为重叠
                    prev_chunk = chunks[i-1]
                    overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                    overlapped_chunk = overlap_text + '\n' + chunk
                    overlapped_chunks.append(overlapped_chunk)
            chunks = overlapped_chunks
        
        return chunks
    
    def chunk_text(self, text: str) -> List[str]:
        """
        公开的文本分块方法
        """
        return self._split_text(text)
    
    async def chat_completion(self, messages: List[Dict[str, str]], stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        调用DeepSeek聊天完成API
        """
        try:
            logger.info(f"调用DeepSeek API，流式模式: {stream}")
            
            # 准备API参数
            api_params = {
                "model": self.chat_model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.max_output_tokens),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": stream
            }
            
            # 调用API
            if stream:
                # 流式调用
                response = await asyncio.to_thread(
                    self.deepseek_client.chat.completions.create,
                    **api_params
                )
                return {"response": response, "stream": True}
            else:
                # 非流式调用
                response = await asyncio.to_thread(
                    self.deepseek_client.chat.completions.create,
                    **api_params
                )
                return {
                    "response": response,
                    "stream": False,
                    "content": response.choices[0].message.content,
                    "usage": response.usage
                }
                
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            if performance_monitor:
                performance_monitor.record_error("chat_completion")
            raise
    
    async def retrieve_relevant_documents(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        检索相关文档（使用PostgreSQL向量搜索）
        """
        if top_k is None:
            top_k = self.top_k_retrieval
        
        try:
            # 导入PostgreSQL向量服务
            from .postgresql_vector_service import postgresql_vector_service
            
            # 使用PostgreSQL进行语义搜索
            results = await postgresql_vector_service.search_similar(
                query=query,
                top_k=top_k,
                similarity_threshold=0.7
            )
            
            logger.info(f"检索到 {len(results)} 个相关文档")
            return results
            
        except Exception as e:
            logger.error(f"文档检索失败: {str(e)}")
            return []
    
    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        """
        try:
            return await self.retrieve_relevant_documents(query, top_k)
        except Exception as e:
            logger.error(f"文档搜索失败: {str(e)}")
            return []
    
    async def generate_response(self, query: str, context_documents: List[Dict[str, Any]] = None, 
                              conversation_history: List[Dict[str, str]] = None,
                              context_limit: int = None) -> Dict[str, Any]:
        """
        生成RAG响应
        """
        start_time = time.time()
        
        try:
            # 检查查询缓存
            cache_key = self._get_cache_key(query)
            if cache_key in self.query_cache:
                cached_item = self.query_cache[cache_key]
                if self._is_cache_valid(cached_item['timestamp']):
                    logger.info("使用缓存的查询结果")
                    if performance_monitor:
                        performance_monitor.record_cache_hit()
                    return cached_item['response']
            
            # 如果没有提供上下文文档，则检索相关文档
            if context_documents is None:
                top_k = context_limit if context_limit else 5
                context_documents = await self.retrieve_relevant_documents(query, top_k)
            elif context_limit and len(context_documents) > context_limit:
                # 如果提供了context_limit，限制文档数量
                context_documents = context_documents[:context_limit]
            
            # 构建上下文
            context_text = self._build_context(context_documents)
            
            # 构建对话历史
            messages = []
            if conversation_history:
                messages.extend(conversation_history[-10:])  # 保留最近10轮对话
            
            # 构建系统提示
            system_prompt = self._build_system_prompt(context_text)
            messages.insert(0, {"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": query})
            
            # 调用DeepSeek API
            response = await asyncio.to_thread(
                self.deepseek_client.chat.completions.create,
                model=self.chat_model,
                messages=messages,
                max_tokens=self.max_output_tokens,
                temperature=0.7,
                stream=False
            )
            
            # 构建响应
            result = {
                'answer': response.choices[0].message.content,
                'context_documents': context_documents,
                'model_used': self.chat_model,
                'timestamp': datetime.now().isoformat(),
                'token_usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
            # 缓存结果
            self.query_cache[cache_key] = {
                'response': result,
                'timestamp': time.time()
            }
            
            # 记录性能指标
            if performance_monitor:
                elapsed_time = time.time() - start_time
                performance_monitor.record_query_time(elapsed_time, "rag_query")
            
            logger.info(f"RAG响应生成完成，耗时: {time.time() - start_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"生成RAG响应失败: {str(e)}")
            if performance_monitor:
                performance_monitor.record_error("rag_generation")
            raise
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """构建上下文文本"""
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents):
            content = doc.get('content', '')
            filename = doc.get('filename', '未知文档')
            similarity = doc.get('similarity_score', 0)
            
            context_parts.append(f"文档 {i+1} ({filename}, 相似度: {similarity:.3f}):\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _build_system_prompt(self, context_text: str) -> str:
        """构建系统提示"""
        base_prompt = """你是WePlus智能学习助手，专门帮助用户解答学习相关问题。

请根据以下上下文信息回答用户问题：
- 优先使用提供的上下文信息
- 如果上下文信息不足，可以结合你的知识进行补充
- 保持回答的准确性和有用性
- 使用清晰、友好的语言风格
- 如果无法确定答案，请诚实说明"""
        
        if context_text:
            return f"{base_prompt}\n\n上下文信息：\n{context_text}"
        else:
            return f"{base_prompt}\n\n注意：当前没有相关的上下文文档，请基于你的知识回答问题。"
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """检查缓存是否有效"""
        return time.time() - timestamp < self.cache_ttl
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        
        # 清理嵌入缓存
        expired_keys = [
            key for key, item in self.embedding_cache.items()
            if current_time - item['timestamp'] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.embedding_cache[key]
        
        # 清理查询缓存
        expired_keys = [
            key for key, item in self.query_cache.items()
            if current_time - item['timestamp'] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.query_cache[key]
        
        # 如果缓存过大，删除最旧的条目
        if len(self.embedding_cache) > self.max_cache_size:
            sorted_items = sorted(
                self.embedding_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for key, _ in sorted_items[:len(sorted_items) - self.max_cache_size]:
                del self.embedding_cache[key]
        
        if len(self.query_cache) > self.max_cache_size:
            sorted_items = sorted(
                self.query_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for key, _ in sorted_items[:len(sorted_items) - self.max_cache_size]:
                del self.query_cache[key]
    
    async def retrieve_relevant_chunks(self, query: str, chunks: List[Union[Dict[str, Any], str]], embeddings: List[List[float]]) -> List[Dict[str, Any]]:
        """检索相关文档块"""
        try:
            if not chunks or not embeddings:
                return []
            
            # 生成查询的嵌入向量
            query_embedding = await self.generate_embeddings([query])
            if not query_embedding:
                return []
            
            query_vector = query_embedding[0]
            
            # 计算相似度
            similarities = []
            for i, chunk_embedding in enumerate(embeddings):
                if chunk_embedding:
                    # 计算余弦相似度
                    similarity = np.dot(query_vector, chunk_embedding) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(chunk_embedding)
                    )
                    similarities.append((i, similarity))
            
            # 按相似度排序并取前k个
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = similarities[:self.top_k_retrieval]
            
            # 构建结果
            relevant_chunks = []
            for idx, similarity in top_indices:
                if idx < len(chunks):
                    chunk = chunks[idx]
                    # 处理不同的数据类型
                    if isinstance(chunk, dict):
                        chunk_data = chunk.copy()
                        chunk_data['similarity_score'] = float(similarity)
                    elif isinstance(chunk, str):
                        # 如果是字符串，创建字典格式
                        chunk_data = {
                            'content': chunk,
                            'similarity_score': float(similarity)
                        }
                    else:
                        # 其他类型，转换为字符串
                        chunk_data = {
                            'content': str(chunk),
                            'similarity_score': float(similarity)
                        }
                    relevant_chunks.append(chunk_data)
            
            logger.info(f"检索到 {len(relevant_chunks)} 个相关文档块")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"检索相关文档块失败: {str(e)}")
            return []

    async def retrieve_relevant_chunks_from_db(self, query: str, chunks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从数据库获取的文档块中检索相关内容"""
        try:
            if not chunks_data:
                return []
            
            # 生成查询的嵌入向量
            query_embedding = await self.generate_embeddings([query])
            if not query_embedding:
                return []
            
            query_vector = query_embedding[0]
            
            # 为每个文档块生成嵌入向量并计算相似度
            similarities = []
            for i, chunk_data in enumerate(chunks_data):
                try:
                    content = chunk_data.get('content', '')
                    if not content:
                        continue
                    
                    # 生成文档块的嵌入向量
                    chunk_embedding = await self.generate_embeddings([content])
                    if not chunk_embedding:
                        continue
                    
                    chunk_vector = chunk_embedding[0]
                    
                    # 计算余弦相似度
                    similarity = np.dot(query_vector, chunk_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector)
                    )
                    similarities.append((i, similarity))
                    
                except Exception as e:
                    logger.warning(f"处理文档块 {i} 时出错: {str(e)}")
                    continue
            
            # 按相似度排序并取前k个
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = similarities[:self.top_k_retrieval]
            
            # 构建结果
            relevant_chunks = []
            for idx, similarity in top_indices:
                if idx < len(chunks_data):
                    chunk_data = chunks_data[idx].copy()
                    chunk_data['similarity_score'] = float(similarity)
                    relevant_chunks.append(chunk_data)
            
            logger.info(f"从 {len(chunks_data)} 个文档块中检索到 {len(relevant_chunks)} 个相关块")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"从数据库检索相关文档块失败: {str(e)}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """获取RAG系统统计信息"""
        try:
            # 导入PostgreSQL向量服务
            from .postgresql_vector_service import postgresql_vector_service
            
            # 获取向量存储统计
            vector_stats = await postgresql_vector_service.get_stats()
            
            # 添加RAG服务统计
            stats = {
                **vector_stats,
                'cache_stats': {
                    'embedding_cache_size': len(self.embedding_cache),
                    'query_cache_size': len(self.query_cache),
                    'cache_ttl': self.cache_ttl,
                    'max_cache_size': self.max_cache_size
                },
                'model_config': {
                    'chat_model': self.chat_model,
                    'embedding_model': self.embedding_model,
                    'max_context_length': self.max_context_length,
                    'chunk_size': self.chunk_size,
                    'top_k_retrieval': self.top_k_retrieval
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取RAG统计信息失败: {str(e)}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """RAG服务健康检查

        功能：
        - 验证 DeepSeek 聊天API是否可用（轻量调用 models.list）
        - 验证豆包嵌入API是否可用（轻量生成一次小文本嵌入）
        - 调用 PostgreSQL 向量服务健康检查（含数据库与 pgvector 扩展）
        - 汇总缓存与模型配置，计算 overall 总体健康状态

        返回：
        - Dict，包含 deepseek_api、embedding_api、vector_store、database、pgvector、cache、model_config、overall、timestamp 等字段。
        """
        status: Dict[str, Any] = {
            "rag_service": True,
            "deepseek_api": False,
            "embedding_api": False,
            "vector_store": False,
            "database": False,
            "pgvector": False,
            "cache": {
                "embedding_cache_size": len(self.embedding_cache),
                "query_cache_size": len(self.query_cache),
                "cache_ttl": self.cache_ttl,
                "max_cache_size": self.max_cache_size
            },
            "model_config": {
                "chat_model": self.chat_model,
                "embedding_model": self.embedding_model,
                "max_context_length": self.max_context_length,
                "chunk_size": self.chunk_size,
                "top_k_retrieval": self.top_k_retrieval
            },
            "timestamp": datetime.now().isoformat()
        }

        # 检查 DeepSeek 聊天API（使用轻量列表模型调用，避免高成本）
        try:
            def _probe_deepseek() -> bool:
                try:
                    # 轻量 GET /v1/models 调用
                    _ = self.deepseek_client.models.list()
                    return True
                except Exception as e:
                    logger.error(f"DeepSeek API检查失败: {str(e)}")
                    return False

            status["deepseek_api"] = await asyncio.to_thread(_probe_deepseek)
        except Exception as e:
            logger.error(f"DeepSeek API探测异常: {str(e)}")
            status["deepseek_api"] = False

        # 检查豆包嵌入API（使用极小输入生成一次嵌入）
        try:
            def _probe_embedding() -> bool:
                try:
                    # 轻量嵌入生成；如失败则返回 False
                    _ = self.embedding_client.embeddings.create(
                        model=self.embedding_model,
                        input="healthcheck"
                    )
                    return True
                except Exception as e:
                    logger.error(f"嵌入API检查失败: {str(e)}")
                    return False

            status["embedding_api"] = await asyncio.to_thread(_probe_embedding)
        except Exception as e:
            logger.error(f"嵌入API探测异常: {str(e)}")
            status["embedding_api"] = False

        # 检查向量存储与数据库/pgvector 扩展
        try:
            from .postgresql_vector_service import postgresql_vector_service
            # 注意：postgresql_vector_service.health_check 为同步方法
            vector_health = postgresql_vector_service.health_check()
            status["vector_store"] = bool(vector_health.get("overall", False))
            status["database"] = bool(vector_health.get("database", False))
            status["pgvector"] = bool(vector_health.get("pgvector", False))
        except Exception as e:
            logger.error(f"向量存储健康检查失败: {str(e)}")
            status["vector_store"] = False
            status["database"] = False
            status["pgvector"] = False

        # 计算总体健康：RAG需要聊天API、嵌入API与向量/数据库均可用
        status["overall"] = all([
            status.get("rag_service"),
            status.get("deepseek_api"),
            status.get("embedding_api"),
            status.get("vector_store"),
            status.get("database")
        ])

        return status

# 创建全局实例
rag_service = RAGService()
