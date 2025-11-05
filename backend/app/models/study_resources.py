"""
学习资源系统数据模型
提供学习资源相关的数据操作接口
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# 导入数据库配置
from database.config import get_db_connection

@dataclass
class ResourceCategory:
    """资源分类模型"""
    id: Optional[int] = None
    name: str = ""
    code: str = ""
    description: str = ""
    icon: str = ""
    color: str = "#4A90E2"
    sort_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def init_db(cls):
        """初始化数据库表"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # 创建资源分类表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS resource_categories (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        code VARCHAR(50) UNIQUE NOT NULL,
                        description TEXT,
                        icon VARCHAR(100),
                        color VARCHAR(20) DEFAULT '#4A90E2',
                        sort_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"初始化资源分类表失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_all(cls) -> List['ResourceCategory']:
        """获取所有分类"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM resource_categories 
                    WHERE is_active = %s 
                    ORDER BY sort_order, name
                """, (True,))
                rows = cursor.fetchall()
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description]
                
                return [cls(**dict(zip(columns, row))) for row in rows]
        except Exception as e:
            print(f"获取资源分类失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_by_code(cls, code: str) -> Optional['ResourceCategory']:
        """根据代码获取分类"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM resource_categories 
                    WHERE code = %s AND is_active = %s
                """, (code, True))
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return cls(**dict(zip(columns, row)))
                return None
        except Exception as e:
            print(f"根据代码获取资源分类失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

@dataclass
class StudyResource:
    """学习资源模型"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    file_name: str = ""
    file_path: str = ""
    file_type: str = ""
    file_size: int = 0
    category_id: int = 0
    download_count: int = 0
    view_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    status: str = "active"
    upload_time: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    keywords: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.keywords is None:
            self.keywords = []

    @classmethod
    def init_db(cls):
        """初始化数据库表"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # 创建学习资源表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS study_resources (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        file_name VARCHAR(255) NOT NULL,
                        file_path VARCHAR(500) NOT NULL,
                        file_type VARCHAR(50),
                        file_size BIGINT DEFAULT 0,
                        category_id INTEGER REFERENCES resource_categories(id),
                        download_count INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        rating_avg DECIMAL(3,2) DEFAULT 0.0,
                        rating_count INTEGER DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'active',
                        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB,
                        tags JSONB,
                        keywords JSONB
                    )
                """)
                
                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_resources_category 
                    ON study_resources(category_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_resources_status 
                    ON study_resources(status)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_study_resources_upload_time 
                    ON study_resources(upload_time)
                """)
                
                conn.commit()
        except Exception as e:
            print(f"初始化学习资源表失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @classmethod
    def create(cls, **kwargs) -> 'StudyResource':
        """创建新资源"""
        resource = cls(**kwargs)
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO study_resources (
                        name, description, file_name, file_path, file_type, 
                        file_size, category_id, metadata, tags, keywords
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    resource.name, resource.description, resource.file_name,
                    resource.file_path, resource.file_type, resource.file_size,
                    resource.category_id, json.dumps(resource.metadata),
                    json.dumps(resource.tags), json.dumps(resource.keywords)
                ))
                resource.id = cursor.fetchone()[0]
                conn.commit()
        except Exception as e:
            print(f"创建学习资源失败: {e}")
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
        
        return resource

    @classmethod
    def get_by_id(cls, resource_id: int) -> Optional['StudyResource']:
        """根据ID获取资源"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM study_resources WHERE id = %s AND status = %s
                """, (resource_id, 'active'))
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if data.get('metadata'):
                        data['metadata'] = json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata']
                    if data.get('tags'):
                        data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
                    if data.get('keywords'):
                        data['keywords'] = json.loads(data['keywords']) if isinstance(data['keywords'], str) else data['keywords']
                    
                    return cls(**data)
                return None
        except Exception as e:
            print(f"根据ID获取学习资源失败: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_by_category(cls, category_id: int, limit: int = 20, offset: int = 0) -> List['StudyResource']:
        """根据分类获取资源"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM study_resources 
                    WHERE category_id = %s AND status = %s
                    ORDER BY upload_time DESC
                    LIMIT %s OFFSET %s
                """, (category_id, 'active', limit, offset))
                rows = cursor.fetchall()
                
                columns = [desc[0] for desc in cursor.description]
                resources = []
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if data.get('metadata'):
                        data['metadata'] = json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata']
                    if data.get('tags'):
                        data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
                    if data.get('keywords'):
                        data['keywords'] = json.loads(data['keywords']) if isinstance(data['keywords'], str) else data['keywords']
                    
                    resources.append(cls(**data))
                
                return resources
        except Exception as e:
            print(f"根据分类获取学习资源失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @classmethod
    def search(cls, query: str, category_id: Optional[int] = None, limit: int = 20, offset: int = 0) -> List['StudyResource']:
        """搜索资源"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                base_query = """
                    SELECT * FROM study_resources 
                    WHERE status = %s AND (
                        name ILIKE %s OR 
                        description ILIKE %s OR 
                        file_name ILIKE %s
                    )
                """
                params = ['active', f'%{query}%', f'%{query}%', f'%{query}%']
                
                if category_id:
                    base_query += " AND category_id = %s"
                    params.append(category_id)
                
                base_query += " ORDER BY upload_time DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                columns = [desc[0] for desc in cursor.description]
                resources = []
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if data.get('metadata'):
                        data['metadata'] = json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata']
                    if data.get('tags'):
                        data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
                    if data.get('keywords'):
                        data['keywords'] = json.loads(data['keywords']) if isinstance(data['keywords'], str) else data['keywords']
                    
                    resources.append(cls(**data))
                
                return resources
        except Exception as e:
            print(f"搜索学习资源失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def update(self, **kwargs):
        """更新资源信息"""
        try:
            # 更新对象属性
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE study_resources 
                    SET name = %s, description = %s, file_name = %s, 
                        file_path = %s, file_type = %s, file_size = %s,
                        category_id = %s, metadata = %s, tags = %s, 
                        keywords = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    self.name, self.description, self.file_name,
                    self.file_path, self.file_type, self.file_size,
                    self.category_id, json.dumps(self.metadata),
                    json.dumps(self.tags), json.dumps(self.keywords),
                    self.id
                ))
                conn.commit()
        except Exception as e:
            print(f"更新学习资源失败: {e}")
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def delete(self):
        """删除资源（软删除）"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE study_resources 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, ('deleted', self.id))
                conn.commit()
                self.status = 'deleted'
        except Exception as e:
            print(f"删除学习资源失败: {e}")
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def increment_view_count(self):
        """增加查看次数"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE study_resources 
                    SET view_count = view_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (self.id,))
                conn.commit()
                self.view_count += 1
        except Exception as e:
            print(f"增加查看次数失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def increment_download_count(self):
        """增加下载次数"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE study_resources 
                    SET download_count = download_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (self.id,))
                conn.commit()
                self.download_count += 1
        except Exception as e:
            print(f"增加下载次数失败: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_popular_resources(cls, limit: int = 10) -> List['StudyResource']:
        """获取热门资源"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM study_resources 
                    WHERE status = %s
                    ORDER BY (download_count + view_count) DESC, rating_avg DESC
                    LIMIT %s
                """, ('active', limit))
                rows = cursor.fetchall()
                
                columns = [desc[0] for desc in cursor.description]
                resources = []
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if data.get('metadata'):
                        data['metadata'] = json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata']
                    if data.get('tags'):
                        data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
                    if data.get('keywords'):
                        data['keywords'] = json.loads(data['keywords']) if isinstance(data['keywords'], str) else data['keywords']
                    
                    resources.append(cls(**data))
                
                return resources
        except Exception as e:
            print(f"获取热门资源失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_recent_resources(cls, limit: int = 10) -> List['StudyResource']:
        """获取最新资源"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM study_resources 
                    WHERE status = %s
                    ORDER BY upload_time DESC
                    LIMIT %s
                """, ('active', limit))
                rows = cursor.fetchall()
                
                columns = [desc[0] for desc in cursor.description]
                resources = []
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if data.get('metadata'):
                        data['metadata'] = json.loads(data['metadata']) if isinstance(data['metadata'], str) else data['metadata']
                    if data.get('tags'):
                        data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
                    if data.get('keywords'):
                        data['keywords'] = json.loads(data['keywords']) if isinstance(data['keywords'], str) else data['keywords']
                    
                    resources.append(cls(**data))
                
                return resources
        except Exception as e:
            print(f"获取最新资源失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

# 初始化数据库表
def init_all_tables():
    """初始化所有表"""
    ResourceCategory.init_db()
    StudyResource.init_db()

if __name__ == "__main__":
    # 初始化数据库表
    init_all_tables()
    print("学习资源数据库表初始化完成")