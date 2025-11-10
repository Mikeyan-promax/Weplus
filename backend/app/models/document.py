"""
文档模型
管理文档的数据库操作
"""

import os
import hashlib
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field

# 导入数据库配置
from database.config import get_db_connection

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 工具函数
def calculate_file_hash(file_input) -> str:
    """
    计算文件的MD5哈希值
    支持文件路径(str)或文件内容(bytes)
    """
    hash_md5 = hashlib.md5()
    try:
        if isinstance(file_input, bytes):
            # 如果输入是bytes，直接计算哈希
            hash_md5.update(file_input)
        elif isinstance(file_input, str):
            # 如果输入是文件路径，读取文件内容
            with open(file_input, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        else:
            raise ValueError(f"不支持的输入类型: {type(file_input)}")
        
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败: {e}")
        return ""

def get_file_type(file_path: str) -> str:
    """获取文件类型"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    type_mapping = {
        '.pdf': 'pdf',
        '.txt': 'text',
        '.md': 'markdown',
        '.htm': 'html',
        '.html': 'html',
        '.doc': 'word',
        '.docx': 'word',
        '.ppt': 'powerpoint',
        '.pptx': 'powerpoint',
        '.xls': 'excel',
        '.xlsx': 'excel',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.mp4': 'video',
        '.avi': 'video',
        '.mov': 'video',
        '.mp3': 'audio',
        '.wav': 'audio',
        '.flac': 'audio'
    }
    
    return type_mapping.get(ext, 'unknown')

def validate_file_type(file_path: str) -> bool:
    """验证文件类型是否支持"""
    supported_types = {
        '.pdf', '.txt', '.md', '.htm', '.html', '.doc', '.docx', 
        '.ppt', '.pptx', '.xls', '.xlsx',
        '.jpg', '.jpeg', '.png', '.gif',
        '.mp4', '.avi', '.mov',
        '.mp3', '.wav', '.flac'
    }
    
    _, ext = os.path.splitext(file_path)
    return ext.lower() in supported_types

class Category:
    """文档分类数据模型"""
    
    def __init__(self, id=None, name=None, description=None, color=None, 
                 parent_id=None, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.color = color or "#007bff"
        self.parent_id = parent_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def _init_db(cls):
        """初始化分类表"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        description TEXT,
                        color VARCHAR(20) DEFAULT '#007bff',
                        parent_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (parent_id) REFERENCES categories (id)
                    )
                ''')
                conn.commit()
                logger.info("分类表初始化成功")
        except Exception as e:
            logger.error(f"分类表初始化失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def create(cls, name: str, description: str = None, color: str = None, parent_id: int = None) -> 'Category':
        """创建新分类"""
        try:
            cls._init_db()
            
            category = cls(
                name=name,
                description=description,
                color=color or "#007bff",
                parent_id=parent_id
            )
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO categories (name, description, color, parent_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    name, description, category.color, parent_id,
                    category.created_at,
                    category.updated_at
                ))
                category.id = cursor.fetchone()[0]
                conn.commit()
                
            logger.info(f"分类创建成功，ID: {category.id}")
            return category
            
        except Exception as e:
            logger.error(f"创建分类失败: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def get_all(cls) -> List['Category']:
        """获取所有分类"""
        try:
            cls._init_db()
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT id, name, description, color, parent_id, created_at, updated_at
                    FROM categories ORDER BY name
                ''')
                rows = cursor.fetchall()
                
                categories = []
                for row in rows:
                    category = cls(
                        id=row[0], name=row[1], description=row[2], color=row[3],
                        parent_id=row[4],
                        created_at=row[5],
                        updated_at=row[6]
                    )
                    categories.append(category)
                
                return categories
        except Exception as e:
            logger.error(f"获取分类列表失败: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def get_by_id(cls, category_id: int) -> Optional['Category']:
        """根据ID获取分类"""
        try:
            cls._init_db()
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT id, name, description, color, parent_id, created_at, updated_at
                    FROM categories WHERE id = %s
                ''', (category_id,))
                row = cursor.fetchone()
                
                if row:
                    return cls(
                        id=row[0], name=row[1], description=row[2], color=row[3],
                        parent_id=row[4],
                        created_at=row[5],
                        updated_at=row[6]
                    )
                return None
        except Exception as e:
            logger.error(f"根据ID获取分类失败: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def update(cls, category_id: int, name: str = None, description: str = None, 
               color: str = None, parent_id: int = None) -> bool:
        """更新分类"""
        try:
            cls._init_db()
            conn = get_db_connection()
            with conn.cursor() as cursor:
                
                # 构建更新语句
                updates = []
                params = []
                
                if name is not None:
                    updates.append("name = %s")
                    params.append(name)
                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                if color is not None:
                    updates.append("color = %s")
                    params.append(color)
                if parent_id is not None:
                    updates.append("parent_id = %s")
                    params.append(parent_id)
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                params.append(category_id)
                
                cursor.execute(f'''
                    UPDATE categories SET {", ".join(updates)} WHERE id = %s
                ''', params)
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新分类失败: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def delete(cls, category_id: int) -> bool:
        """删除分类"""
        try:
            cls._init_db()
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM categories WHERE id = %s', (category_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除分类失败: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Tag:
    """文档标签数据模型"""
    
    def __init__(self, id=None, name=None, color=None, created_at=None):
        self.id = id
        self.name = name
        self.color = color or "#28a745"
        self.created_at = created_at or datetime.utcnow()
    
    @classmethod
    def _init_db(cls):
        """初始化标签表"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tags (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        color VARCHAR(20) DEFAULT '#28a745',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("标签表初始化成功")
        except Exception as e:
            logger.error(f"标签表初始化失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def create(cls, name: str, color: str = None) -> 'Tag':
        """创建新标签"""
        try:
            cls._init_db()
            
            tag = cls(name=name, color=color or "#28a745")
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO tags (name, color, created_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                ''', (name, tag.color, tag.created_at))
                tag.id = cursor.fetchone()[0]
                conn.commit()
                
            logger.info(f"标签创建成功，ID: {tag.id}")
            return tag
            
        except Exception as e:
            logger.error(f"创建标签失败: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def get_all(cls) -> List['Tag']:
        """获取所有标签"""
        try:
            cls._init_db()
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('SELECT id, name, color, created_at FROM tags ORDER BY name')
                rows = cursor.fetchall()
                
                tags = []
                for row in rows:
                    tag = cls(id=row[0], name=row[1], color=row[2], created_at=row[3])
                    tags.append(tag)
                
                return tags
        except Exception as e:
            logger.error(f"获取标签列表失败: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    @classmethod
    def get_by_id(cls, tag_id: int) -> Optional['Tag']:
        """根据ID获取标签"""
        try:
            cls._init_db()
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('SELECT id, name, color, created_at FROM tags WHERE id = %s', (tag_id,))
                row = cursor.fetchone()
                
                if row:
                    return cls(id=row[0], name=row[1], color=row[2], created_at=row[3])
                return None
        except Exception as e:
            logger.error(f"根据ID获取标签失败: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Document:
    """文档数据模型"""
    
    def __init__(self, id=None, filename=None, file_type=None, file_size=None,
                 upload_time=None, content_hash=None, doc_metadata=None, 
                 status=None, category_id=None):
        self.id = id
        self.filename = filename
        self.file_type = file_type
        self.file_size = file_size
        self.upload_time = upload_time or datetime.utcnow()
        self.content_hash = content_hash
        self.doc_metadata = doc_metadata or {}
        self.status = status or "uploaded"
        self.category_id = category_id
    
    @classmethod
    def _init_db(cls):
        """初始化文档相关表"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # 文档表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS documents (
                            id SERIAL PRIMARY KEY,
                            filename VARCHAR(255) NOT NULL,
                            file_type VARCHAR(100) NOT NULL,
                            file_size BIGINT NOT NULL,
                            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            content_hash VARCHAR(255) UNIQUE NOT NULL,
                            doc_metadata JSONB DEFAULT '{}',
                            status VARCHAR(50) DEFAULT 'uploaded',
                            category_id INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (category_id) REFERENCES categories (id)
                        )
                    ''')
                    
                    # 文档标签关联表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS document_tags (
                            id SERIAL PRIMARY KEY,
                            document_id INTEGER NOT NULL,
                            tag_id INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
                            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                            UNIQUE(document_id, tag_id)
                        )
                    ''')
                    
                    conn.commit()
                    logger.info("文档表初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    @classmethod
    def create_document(
        cls,
        filename: str,
        file_type: str,
        file_size: int,
        content_hash: str,
        metadata: Dict[str, Any] = None,
        category_id: int = None,
        tag_ids: List[int] = None
    ) -> 'Document':
        """创建新文档记录"""
        try:
            cls._init_db()  # 确保表存在
            
            doc = cls(
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                content_hash=content_hash,
                doc_metadata=metadata or {},
                status="uploaded",
                category_id=category_id
            )
            
            # 保存到数据库
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO documents (filename, file_type, file_size, upload_time, content_hash, doc_metadata, status, category_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        filename,
                        file_type,
                        file_size,
                        datetime.utcnow(),
                        content_hash,
                        json.dumps(metadata or {}),
                        "uploaded",
                        category_id
                    ))
                    doc.id = cursor.fetchone()[0]
                    
                    # 添加标签关联
                    if tag_ids:
                        for tag_id in tag_ids:
                            cursor.execute('''
                                INSERT INTO document_tags (document_id, tag_id)
                                VALUES (%s, %s)
                            ''', (doc.id, tag_id))
                    
                    conn.commit()
                    
            logger.info(f"文档记录创建成功，ID: {doc.id}")
            return doc
            
        except Exception as e:
            logger.error(f"创建文档记录失败: {str(e)}")
            raise

    @classmethod
    def get_by_id(cls, doc_id: int) -> Optional['Document']:
        """根据ID获取文档"""
        try:
            cls._init_db()
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT id, filename, file_type, file_size, upload_time, 
                               content_hash, doc_metadata, status, category_id
                        FROM documents WHERE id = %s
                    ''', (doc_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        metadata = row[6]
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        
                        return cls(
                            id=row[0], filename=row[1], file_type=row[2], file_size=row[3],
                            upload_time=row[4], content_hash=row[5], doc_metadata=metadata,
                            status=row[7], category_id=row[8]
                        )
                    return None
        except Exception as e:
            logger.error(f"根据ID获取文档失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_hash(cls, content_hash: str) -> Optional['Document']:
        """根据内容哈希获取文档"""
        try:
            cls._init_db()
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT id, filename, file_type, file_size, upload_time, 
                               content_hash, doc_metadata, status, category_id
                        FROM documents WHERE content_hash = %s
                    ''', (content_hash,))
                    row = cursor.fetchone()
                    
                    if row:
                        metadata = row[6]
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        
                        return cls(
                            id=row[0], filename=row[1], file_type=row[2], file_size=row[3],
                            upload_time=row[4], content_hash=row[5], doc_metadata=metadata,
                            status=row[7], category_id=row[8]
                        )
                    return None
        except Exception as e:
            logger.error(f"根据哈希获取文档失败: {str(e)}")
            return None
    
    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0, category_id: int = None, 
                status: str = None) -> List['Document']:
        """获取文档列表"""
        try:
            cls._init_db()
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # 构建查询条件
                    conditions = []
                    params = []
                    
                    if category_id is not None:
                        conditions.append("category_id = %s")
                        params.append(category_id)
                    
                    if status is not None:
                        conditions.append("status = %s")
                        params.append(status)
                    
                    where_clause = ""
                    if conditions:
                        where_clause = "WHERE " + " AND ".join(conditions)
                    
                    params.extend([limit, offset])
                    
                    cursor.execute(f'''
                        SELECT id, filename, file_type, file_size, upload_time, 
                               content_hash, doc_metadata, status, category_id
                        FROM documents {where_clause}
                        ORDER BY upload_time DESC
                        LIMIT %s OFFSET %s
                    ''', params)
                    rows = cursor.fetchall()
                    
                    documents = []
                    for row in rows:
                        metadata = row[6]
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        
                        doc = cls(
                            id=row[0], filename=row[1], file_type=row[2], file_size=row[3],
                            upload_time=row[4], content_hash=row[5], doc_metadata=metadata,
                            status=row[7], category_id=row[8]
                        )
                        documents.append(doc)
                    
                    return documents
        except Exception as e:
            logger.error(f"获取文档列表失败: {str(e)}")
            return []
    
    @classmethod
    def search(cls, query: str, limit: int = 50, offset: int = 0) -> List['Document']:
        """搜索文档"""
        try:
            cls._init_db()
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT id, filename, file_type, file_size, upload_time, 
                               content_hash, doc_metadata, status, category_id
                        FROM documents 
                        WHERE filename ILIKE %s OR doc_metadata::text ILIKE %s
                        ORDER BY upload_time DESC
                        LIMIT %s OFFSET %s
                    ''', (f'%{query}%', f'%{query}%', limit, offset))
                    rows = cursor.fetchall()
                    
                    documents = []
                    for row in rows:
                        metadata = row[6]
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        
                        doc = cls(
                            id=row[0], filename=row[1], file_type=row[2], file_size=row[3],
                            upload_time=row[4], content_hash=row[5], doc_metadata=metadata,
                            status=row[7], category_id=row[8]
                        )
                        documents.append(doc)
                    
                    return documents
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []
    
    def update_status(self, new_status: str) -> bool:
        """更新文档状态"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE documents SET status = %s WHERE id = %s
                    ''', (new_status, self.id))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        self.status = new_status
                        return True
                    return False
        except Exception as e:
            logger.error(f"更新文档状态失败: {str(e)}")
            return False
    
    def update_metadata(self, metadata: Dict[str, Any]) -> bool:
        """更新文档元数据"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE documents SET doc_metadata = %s WHERE id = %s
                    ''', (json.dumps(metadata), self.id))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        self.doc_metadata = metadata
                        return True
                    return False
        except Exception as e:
            logger.error(f"更新文档元数据失败: {str(e)}")
            return False
    
    def add_tags(self, tag_ids: List[int]) -> bool:
        """为文档添加标签"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for tag_id in tag_ids:
                        cursor.execute('''
                            INSERT INTO document_tags (document_id, tag_id)
                            VALUES (%s, %s)
                            ON CONFLICT (document_id, tag_id) DO NOTHING
                        ''', (self.id, tag_id))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"添加文档标签失败: {str(e)}")
            return False
    
    def remove_tags(self, tag_ids: List[int]) -> bool:
        """移除文档标签"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        DELETE FROM document_tags 
                        WHERE document_id = %s AND tag_id = ANY(%s)
                    ''', (self.id, tag_ids))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"移除文档标签失败: {str(e)}")
            return False
    
    def get_tags(self) -> List[Tag]:
        """获取文档的所有标签"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT t.id, t.name, t.color, t.created_at
                        FROM tags t
                        JOIN document_tags dt ON t.id = dt.tag_id
                        WHERE dt.document_id = %s
                        ORDER BY t.name
                    ''', (self.id,))
                    rows = cursor.fetchall()
                    
                    tags = []
                    for row in rows:
                        tag = Tag(id=row[0], name=row[1], color=row[2], created_at=row[3])
                        tags.append(tag)
                    
                    return tags
        except Exception as e:
            logger.error(f"获取文档标签失败: {str(e)}")
            return []
    
    def delete(self) -> bool:
        """删除文档记录"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 先删除标签关联
                    cursor.execute('DELETE FROM document_tags WHERE document_id = %s', (self.id,))
                    # 再删除文档记录
                    cursor.execute('DELETE FROM documents WHERE id = %s', (self.id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "content_hash": self.content_hash,
            "doc_metadata": self.doc_metadata,
            "status": self.status,
            "category_id": self.category_id
        }

class DocumentChunk(BaseModel):
    """文档块模型"""
    content: str = Field(..., description="块内容")
    chunk_index: int = Field(..., description="块索引")
    document_id: str = Field(..., description="所属文档ID")
    embedding: Optional[List[float]] = Field(default=None, description="嵌入向量")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="块元数据")

class DocumentManager:
    """文档管理器"""
    
    @staticmethod
    def init_all_tables():
        """初始化所有表"""
        Category._init_db()
        Tag._init_db()
        Document._init_db()
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # 总文档数
                cursor.execute('SELECT COUNT(*) FROM documents')
                total_docs = cursor.fetchone()[0]
                
                # 总文件大小
                cursor.execute('SELECT SUM(file_size) FROM documents')
                total_size = cursor.fetchone()[0] or 0
                
                # 按状态统计
                cursor.execute('''
                    SELECT status, COUNT(*) 
                    FROM documents 
                    GROUP BY status
                ''')
                status_stats = dict(cursor.fetchall())
                
                # 按文件类型统计
                cursor.execute('''
                    SELECT file_type, COUNT(*) 
                    FROM documents 
                    GROUP BY file_type 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                ''')
                type_stats = dict(cursor.fetchall())
                
                # 按分类统计
                cursor.execute('''
                    SELECT c.name, COUNT(d.id)
                    FROM categories c
                    LEFT JOIN documents d ON c.id = d.category_id
                    GROUP BY c.id, c.name
                    ORDER BY COUNT(d.id) DESC
                ''')
                category_stats = dict(cursor.fetchall())
                
                return {
                    "total_documents": total_docs,
                    "total_size": total_size,
                    "status_distribution": status_stats,
                    "type_distribution": type_stats,
                    "category_distribution": category_stats
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()
    


# 初始化数据库表
if __name__ == "__main__":
    DocumentManager.init_all_tables()
    print("文档数据库表初始化完成！")
