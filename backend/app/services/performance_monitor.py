"""
RAG系统性能监控模块
提供查询响应时间、缓存命中率等性能指标监控
"""
import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.query_times = deque(maxlen=max_history_size)
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        self.embedding_stats = {
            'total_generated': 0,
            'cache_hits': 0,
            'batch_sizes': deque(maxlen=100)
        }
        self.error_counts = defaultdict(int)
        self.lock = threading.Lock()
        
    def record_query_time(self, query_time: float, query_type: str = "general"):
        """记录查询时间"""
        with self.lock:
            self.query_times.append({
                'time': query_time,
                'type': query_type,
                'timestamp': datetime.now()
            })
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self.lock:
            self.cache_stats['hits'] += 1
            self.cache_stats['total_requests'] += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self.lock:
            self.cache_stats['misses'] += 1
            self.cache_stats['total_requests'] += 1
    
    def record_embedding_generation(self, count: int, from_cache: int = 0):
        """记录嵌入向量生成"""
        with self.lock:
            self.embedding_stats['total_generated'] += count
            self.embedding_stats['cache_hits'] += from_cache
            self.embedding_stats['batch_sizes'].append(count)
    
    def record_document_processing(self, content_length: int, chunk_count: int, elapsed_time: float):
        """记录文档处理性能"""
        with self.lock:
            # 记录为查询时间的一种类型
            self.query_times.append({
                'time': elapsed_time,
                'type': 'document_processing',
                'timestamp': datetime.now(),
                'content_length': content_length,
                'chunk_count': chunk_count
            })
    
    def record_error(self, error_type: str):
        """记录错误"""
        with self.lock:
            self.error_counts[error_type] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        with self.lock:
            # 计算查询时间统计
            if self.query_times:
                times = [q['time'] for q in self.query_times]
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                # 最近5分钟的查询
                recent_cutoff = datetime.now() - timedelta(minutes=5)
                recent_queries = [q for q in self.query_times if q['timestamp'] > recent_cutoff]
                recent_avg = sum(q['time'] for q in recent_queries) / len(recent_queries) if recent_queries else 0
            else:
                avg_time = max_time = min_time = recent_avg = 0
            
            # 计算缓存命中率
            cache_hit_rate = (
                self.cache_stats['hits'] / self.cache_stats['total_requests'] 
                if self.cache_stats['total_requests'] > 0 else 0
            )
            
            # 计算嵌入向量缓存命中率
            embedding_cache_rate = (
                self.embedding_stats['cache_hits'] / self.embedding_stats['total_generated']
                if self.embedding_stats['total_generated'] > 0 else 0
            )
            
            return {
                'query_performance': {
                    'average_time': round(avg_time, 3),
                    'max_time': round(max_time, 3),
                    'min_time': round(min_time, 3),
                    'recent_5min_avg': round(recent_avg, 3),
                    'total_queries': len(self.query_times)
                },
                'cache_performance': {
                    'hit_rate': round(cache_hit_rate * 100, 2),
                    'total_hits': self.cache_stats['hits'],
                    'total_misses': self.cache_stats['misses'],
                    'total_requests': self.cache_stats['total_requests']
                },
                'embedding_performance': {
                    'cache_hit_rate': round(embedding_cache_rate * 100, 2),
                    'total_generated': self.embedding_stats['total_generated'],
                    'cache_hits': self.embedding_stats['cache_hits'],
                    'avg_batch_size': round(
                        sum(self.embedding_stats['batch_sizes']) / len(self.embedding_stats['batch_sizes'])
                        if self.embedding_stats['batch_sizes'] else 0, 2
                    )
                },
                'error_stats': dict(self.error_counts),
                'timestamp': datetime.now().isoformat()
            }
    
    def reset_stats(self):
        """重置统计数据"""
        with self.lock:
            self.query_times.clear()
            self.cache_stats = {'hits': 0, 'misses': 0, 'total_requests': 0}
            self.embedding_stats = {
                'total_generated': 0,
                'cache_hits': 0,
                'batch_sizes': deque(maxlen=100)
            }
            self.error_counts.clear()

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

def monitor_performance(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            performance_monitor.record_query_time(end_time - start_time, func.__name__)
            return result
        except Exception as e:
            performance_monitor.record_error(type(e).__name__)
            raise
    return wrapper

async def monitor_async_performance(func):
    """异步性能监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            performance_monitor.record_query_time(end_time - start_time, func.__name__)
            return result
        except Exception as e:
            performance_monitor.record_error(type(e).__name__)
            raise
    return wrapper