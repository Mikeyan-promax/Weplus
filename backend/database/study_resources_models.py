
# PostgreSQL数据库连接配置
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import os

# 数据库连接配置
DB_CONFIG = {
    'host': 'pgm-2ze8ej8ej8ej8ej8.pg.rds.aliyuncs.com',
    'port': '5432',
    'database': 'weplus_main',
    'user': 'weplus_user',
    'password': 'WePlus2024!@#'
}

# 连接池
connection_pool = None

# 重置连接池
connection_pool = None

def init_connection_pool(minconn=1, maxconn=20):
    """初始化连接池"""
    global connection_pool
    try:
        if connection_pool is None:
            from database.postgresql_config import init_connection_pool as init_pool
            connection_pool = init_pool(minconn, maxconn)
        return connection_pool
    except Exception as e:
        logger.error(f"连接池初始化失败: {e}")
        raise

def get_db_connection():
    """获取数据库连接"""
    if connection_pool is None:
        init_connection_pool()
    return connection_pool.getconn()

def return_db_connection(conn):
    """归还数据库连接"""
    if connection_pool:
        connection_pool.putconn(conn)

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """执行查询"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            # 检查是否是SELECT查询或包含RETURNING的INSERT/UPDATE/DELETE查询
            query_upper = query.strip().upper()
            if (query_upper.startswith(('SELECT', 'WITH')) or 
                'RETURNING' in query_upper):
                # 对于包含RETURNING的INSERT/UPDATE/DELETE查询，需要先提交事务
                if 'RETURNING' in query_upper:
                    conn.commit()
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            return_db_connection(conn)


"""
学习资源系统数据库模型 - PostgreSQL版本
包含资源分类、学习资源、用户学习记录等数据模型
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 使用新的PostgreSQL连接管理器
from .db_manager import DatabaseManager as PostgreSQLManager

class ResourceType(Enum):
    """资源类型枚举"""
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    IMAGE = "image"
    LINK = "link"
    COURSE = "course"
    EXERCISE = "exercise"
    OTHER = "other"
    
    @classmethod
    def from_extension(cls, extension: str) -> 'ResourceType':
        """根据文件扩展名确定资源类型"""
        extension = extension.lower().lstrip('.')
        
        # 视频文件
        if extension in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v']:
            return cls.VIDEO
        
        # 文档文件
        elif extension in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages']:
            return cls.DOCUMENT
        
        # 音频文件
        elif extension in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a']:
            return cls.AUDIO
        
        # 图片文件
        elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tiff']:
            return cls.IMAGE
        
        # 默认为其他类型
        else:
            return cls.OTHER

class DifficultyLevel(Enum):
    """难度等级枚举"""
    BEGINNER = "beginner"      # 初级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"      # 高级
    EXPERT = "expert"          # 专家级

class StudyStatus(Enum):
    """学习状态枚举"""
    NOT_STARTED = "not_started"    # 未开始
    IN_PROGRESS = "in_progress"    # 进行中
    COMPLETED = "completed"        # 已完成
    PAUSED = "paused"             # 暂停
    ABANDONED = "abandoned"        # 已放弃

@dataclass
class ResourceCategory:
    """资源分类模型 - PostgreSQL版本"""
    id: Optional[int] = None
    name: str = ""
    code: str = ""                   # 分类代码
    description: str = ""
    icon: str = ""                   # 分类图标
    color: str = ""                  # 分类颜色
    sort_order: int = 0              # 排序顺序
    is_active: bool = True           # 是否激活
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 统计字段
    resource_count: int = 0          # 该分类下的资源数量
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    async def create(cls, name: str, description: str = "", parent_id: int = None,
                    icon: str = "", color: str = "") -> 'ResourceCategory':
        """创建新分类
        函数级注释：
        - 兼容历史签名，接受 parent_id 参数但不持久化该字段。
        - 仅写入基础展示信息（name/description/icon/color）。
        """
        category = cls(
            name=name,
            description=description,
            icon=icon,
            color=color
        )
        
        # 使用PostgreSQL管理器插入数据
        db_manager = PostgreSQLManager()
        query = """
        INSERT INTO resource_categories (name, description, icon, color,
                                       sort_order, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            category.name, category.description,
            category.icon, category.color, category.sort_order,
            category.is_active, category.created_at, category.updated_at
        )
        
        result = await db_manager.execute_query(query, params, fetch_one=True)
        category.id = result['id']
        
        return category
    
    @classmethod
    async def get_by_id(cls, category_id: int) -> Optional['ResourceCategory']:
        """根据ID获取分类"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM resource_categories WHERE id = %s"
        result = await db_manager.execute_query(query, (category_id,), fetch_one=True)
        
        if result:
            data = dict(result)
            data.pop('parent_id', None)
            return cls(**data)
        return None
    
    @classmethod
    def get_all_active(cls) -> List['ResourceCategory']:
        """获取所有激活的分类"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM resource_categories WHERE is_active = true ORDER BY sort_order, name"
        results = db_manager.execute_query(query)
        cleaned = []
        for r in results:
            d = dict(r)
            d.pop('parent_id', None)
            cleaned.append(cls(**d))
        return cleaned
    
@classmethod
async def get_tree(cls) -> List[Dict[str, Any]]:
    """获取分类树结构（平铺版）
    函数级注释：
    - 历史 parent_id 字段已停止使用；此处返回每个分类的 children 为空数组。
    - 如需恢复层级，可在数据库与模型层重新加入 parent_id，并更新此方法。
    """
    categories = await cls.get_all_active()
    tree = []
    for cat in categories:
        item = cat.to_dict()
        item['children'] = []
        tree.append(item)
    return tree
    
async def save(self):
    """保存分类"""
    db_manager = PostgreSQLManager()
    if self.id:
        # 更新现有分类
        query = """
        UPDATE resource_categories SET name = %s, description = %s,
               icon = %s, color = %s, sort_order = %s, is_active = %s, updated_at = %s
        WHERE id = %s
        """
        params = (
            self.name, self.description, self.icon,
            self.color, self.sort_order, self.is_active, datetime.now(), self.id
        )
    else:
        # 创建新分类
        query = """
        INSERT INTO resource_categories (name, description, icon, color,
                                       sort_order, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            self.name, self.description, self.icon,
            self.color, self.sort_order, self.is_active,
            self.created_at, self.updated_at
        )
        result = await db_manager.execute_query(query, params, fetch_one=True)
        self.id = result['id']
        return

    await db_manager.execute_query(query, params)

@dataclass
class StudyResource:
    """学习资源模型 - PostgreSQL版本"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    content: str = ""                    # 资源内容或链接
    resource_type: ResourceType = ResourceType.OTHER
    category_id: Optional[int] = None    # 分类ID
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    
    # 文件相关
    file_path: str = ""                  # 文件路径
    file_size: int = 0                   # 文件大小
    file_hash: str = ""                  # 文件哈希
    thumbnail_path: str = ""             # 缩略图路径
    
    # 元数据
    duration: int = 0                    # 时长（秒）
    tags: List[str] = None               # 标签
    keywords: List[str] = None           # 关键词
    author: str = ""                     # 作者
    source_url: str = ""                 # 来源URL
    
    # 状态和统计
    is_active: bool = True               # 是否激活
    is_featured: bool = False            # 是否推荐
    view_count: int = 0                  # 查看次数
    download_count: int = 0              # 下载次数
    rating: float = 0.0                  # 评分
    rating_count: int = 0                # 评分人数
    
    # 时间字段
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # 学习相关
    estimated_time: int = 0              # 预估学习时间（分钟）
    prerequisites: List[int] = None      # 前置资源ID列表
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.keywords is None:
            self.keywords = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        data['difficulty_level'] = self.difficulty_level.value
        return data
    
    @classmethod
    def create(cls, title: str, description: str = "", file_type: str = "text",
                    category_id: int = None, file_path: str = "", file_size: int = 0,
                    original_filename: str = "", **kwargs) -> 'StudyResource':
        """创建新学习资源 - 与当前PostgreSQL表结构对齐
        函数级注释：
        - 映射字段：title→name，original_filename→file_name；
        - 仅写入现有列：name, description, file_name, file_path, file_type, file_size, category_id,
          status, upload_time, updated_at, metadata, tags, keywords, download_count, view_count, rating_avg, rating_count；
        - 其余字段（content_hash/difficulty_level/language/uploader_id/is_featured）不在当前表结构，避免写入导致错误。
        """
        # 规范化标签/关键词文本
        tags_text = kwargs.get('tags', '[]')
        metadata_text = kwargs.get('metadata', '{}')
        keywords_text = kwargs.get('keywords', '[]')

        query = """
        INSERT INTO study_resources (
            name, description, file_name, file_path, file_type, file_size, category_id,
            status, upload_time, updated_at, metadata, tags, keywords,
            download_count, view_count, rating_avg, rating_count
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        ) RETURNING id
        """
        params = (
            title, description, original_filename, file_path, file_type, file_size, category_id,
            kwargs.get('status', 'active'), datetime.now(), datetime.now(),
            metadata_text, tags_text, keywords_text,
            0, 0, 0.00, 0
        )
        
        result = execute_query(query, params, fetch_one=True)
        
        # 创建并返回资源对象，只传递构造函数接受的参数
        resource = cls()
        resource.id = result['id']
        resource.title = title
        resource.description = description
        resource.content = ""
        resource.resource_type = ResourceType.OTHER
        resource.file_path = file_path
        resource.file_size = file_size
        resource.category_id = category_id
        resource.difficulty_level = DifficultyLevel.BEGINNER
        resource.file_hash = ''
        resource.author = kwargs.get('author', '')
        resource.source_url = kwargs.get('source_url', '')
        resource.is_active = True
        resource.is_featured = False
        resource.created_at = datetime.now()
        resource.updated_at = datetime.now()
        
        return resource
    
    @classmethod
    def get_by_id(cls, resource_id: int) -> Optional['StudyResource']:
        """根据ID获取资源"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM study_resources WHERE id = %s"
        result = db_manager.execute_query(query, (resource_id,), fetch_one=True)
        
        if result:
            # 转换字段名与类型，构造严格匹配数据类的实例
            row = dict(result)
            title = row.get('name', '')
            file_type = row.get('file_type', '')
            # JSON字段处理
            tags = []
            if isinstance(row.get('tags'), str):
                try:
                    tags = json.loads(row['tags'])
                except Exception:
                    tags = []
            keywords = []
            if isinstance(row.get('keywords'), str):
                try:
                    keywords = json.loads(row['keywords'])
                except Exception:
                    keywords = []
            # 构造实例
            inst = cls(
                id=row.get('id'),
                title=title,
                description=row.get('description', ''),
                content='',
                resource_type=ResourceType.from_extension(file_type) if file_type else ResourceType.OTHER,
                category_id=row.get('category_id'),
                difficulty_level=DifficultyLevel.BEGINNER,
                file_path=row.get('file_path', ''),
                file_size=row.get('file_size', 0),
                file_hash='',
                thumbnail_path='',
                duration=0,
                tags=tags,
                keywords=keywords,
                author='',
                source_url=row.get('source_url', ''),
                is_active=(row.get('status', 'active') == 'active'),
                is_featured=False,
                view_count=row.get('view_count', 0),
                download_count=row.get('download_count', 0),
                rating=float(row.get('rating_avg', 0.0) or 0.0),
                rating_count=row.get('rating_count', 0) or 0,
                created_at=row.get('upload_time'),
                updated_at=row.get('updated_at'),
                published_at=None,
                estimated_time=0,
                prerequisites=[],
            )
            return inst
        return None

    @classmethod
    def update(cls, resource_id: int, **update_data) -> int:
        """根据资源ID更新学习资源基础字段
        函数级注释：
        - 目的：兼容管理员端更新接口，仅更新表中存在的基础字段；避免写入不存在列。
        - 输入：resource_id（整数）；可选更新键包括 title、description、category_id、tags、status。
        - 字段映射：title -> name；其余与数据库列同名。
        - 特殊处理：tags 支持逗号分隔字符串，统一存为 JSON 数组文本（如 ["英语","真题"]）。
        - 返回：受影响的行数（通常为1）。
        """
        if not isinstance(resource_id, int) or resource_id <= 0:
            raise ValueError("resource_id 必须为有效的正整数")

        # 允许更新的键映射（API -> DB 列）
        key_map = {
            'title': 'name',
            'name': 'name',
            'description': 'description',
            'category_id': 'category_id',
            'status': 'status',
            'tags': 'tags',
        }

        set_parts = []
        params = []

        for key, value in update_data.items():
            if key not in key_map:
                # 忽略表中不存在的字段（如 difficulty_level 等）
                continue
            column = key_map[key]

            if column == 'tags':
                # 将 tags 统一存储为 JSON 数组文本
                if value is None:
                    json_text = '[]'
                elif isinstance(value, str):
                    # 支持前端提交逗号分隔或已是JSON字符串
                    value_str = value.strip()
                    try:
                        # 若本身是JSON，直接使用
                        loaded = json.loads(value_str)
                        if isinstance(loaded, list):
                            json_text = json.dumps(loaded, ensure_ascii=False)
                        else:
                            json_text = '[]'
                    except Exception:
                        # 逗号分隔转数组
                        arr = [v.strip() for v in value_str.split(',') if v.strip()]
                        json_text = json.dumps(arr, ensure_ascii=False)
                elif isinstance(value, (list, tuple)):
                    json_text = json.dumps(list(value), ensure_ascii=False)
                else:
                    json_text = '[]'
                set_parts.append(f"{column} = %s")
                params.append(json_text)
            elif column == 'status':
                # 仅接受预期状态值
                allowed = {'active', 'inactive', 'deleted'}
                status_val = value if isinstance(value, str) else 'active'
                if status_val not in allowed:
                    status_val = 'active'
                set_parts.append(f"{column} = %s")
                params.append(status_val)
            else:
                set_parts.append(f"{column} = %s")
                params.append(value)

        if not set_parts:
            # 没有可更新的字段
            return 0

        # 统一更新时间
        set_parts.append("updated_at = CURRENT_TIMESTAMP")

        set_clause = ", ".join(set_parts)
        query = f"UPDATE study_resources SET {set_clause} WHERE id = %s"
        params.append(resource_id)

        db_manager = PostgreSQLManager()
        return db_manager.execute_query(query, params)

    @classmethod
    def delete(cls, resource_id: int) -> int:
        """根据资源ID软删除学习资源
        函数级注释：
        - 动作：将 status 更新为 'deleted' 并刷新 updated_at。
        - 说明：软删除保留记录，避免破坏外键关系；前端列表通过 status 筛选隐藏。
        - 返回：受影响的行数（通常为1）。
        """
        if not isinstance(resource_id, int) or resource_id <= 0:
            raise ValueError("resource_id 必须为有效的正整数")
        db_manager = PostgreSQLManager()
        query = "UPDATE study_resources SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        return db_manager.execute_query(query, (resource_id,))

    @classmethod
    def get_paginated(cls, page: int = 1, limit: int = 10,
                           category_id: int = None, resource_type: ResourceType = None,
                           difficulty_level: DifficultyLevel = None,
                           search_query: str = None) -> Tuple[List['StudyResource'], int]:
        """分页获取资源列表"""
        db_manager = PostgreSQLManager()
        offset = (page - 1) * limit
        
        # 构建查询条件
        where_conditions = ["status = 'active'"]
        params = []
        
        if category_id:
            where_conditions.append("category_id = %s")
            params.append(category_id)
        
        if resource_type:
            where_conditions.append("file_type = %s")
            params.append(resource_type.value)
        
        if difficulty_level:
            where_conditions.append("difficulty_level = %s")
            params.append(difficulty_level.value)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            where_conditions.append("(name ILIKE %s OR description ILIKE %s)")
            params.extend([search_pattern, search_pattern])
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) as total FROM study_resources {where_clause}"
        count_result = db_manager.execute_query(count_query, params, fetch_one=True)
        total = count_result['total']
        
        # 获取分页数据
        query = f"""
        SELECT * FROM study_resources {where_clause}
        ORDER BY upload_time DESC, updated_at DESC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        results = db_manager.execute_query(query, params)
        
        resources = []
        for result in results:
            # 转换为字典格式，保持与前端兼容
            resource_dict = dict(result)
            # 兼容映射：数据库列 name -> 前端期望 title
            if 'name' in resource_dict:
                resource_dict['title'] = resource_dict.get('name')
            
            # 处理资源类型
            if 'file_type' in resource_dict:
                resource_dict['resource_type'] = ResourceType.from_extension(resource_dict['file_type']).value
            
            # 处理难度等级
            if resource_dict.get('difficulty_level'):
                try:
                    resource_dict['difficulty_level'] = DifficultyLevel(resource_dict['difficulty_level']).value
                except ValueError:
                    resource_dict['difficulty_level'] = DifficultyLevel.BEGINNER.value
            
            # 处理JSON字段
            if resource_dict.get('tags') and isinstance(resource_dict['tags'], str):
                try:
                    resource_dict['tags'] = json.loads(resource_dict['tags'])
                except:
                    resource_dict['tags'] = []
            
            if resource_dict.get('metadata') and isinstance(resource_dict['metadata'], str):
                try:
                    resource_dict['metadata'] = json.loads(resource_dict['metadata'])
                except:
                    resource_dict['metadata'] = {}
            
            resources.append(resource_dict)
        
        return resources, total
    
    async def increment_view_count(self):
        """增加查看次数"""
        self.view_count += 1
        db_manager = PostgreSQLManager()
        query = "UPDATE study_resources SET view_count = %s WHERE id = %s"
        await db_manager.execute_query(query, (self.view_count, self.id))
    
    async def increment_download_count(self):
        """增加下载次数"""
        self.download_count += 1
        db_manager = PostgreSQLManager()
        query = "UPDATE study_resources SET download_count = %s WHERE id = %s"
        await db_manager.execute_query(query, (self.download_count, self.id))
    
    async def update_rating(self, new_rating: float):
        """更新评分"""
        # 计算新的平均评分
        total_rating = self.rating * self.rating_count + new_rating
        self.rating_count += 1
        self.rating = total_rating / self.rating_count
        
        db_manager = PostgreSQLManager()
        query = "UPDATE study_resources SET rating = %s, rating_count = %s WHERE id = %s"
        await db_manager.execute_query(query, (self.rating, self.rating_count, self.id))
    
    def delete(self):
        """删除资源（软删除）"""
        try:
            db_manager = PostgreSQLManager()
            query = "UPDATE study_resources SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            db_manager.execute_query(query, ('deleted', self.id))
            self.is_active = False
        except Exception as e:
            print(f"删除学习资源失败: {e}")
            raise e
    
    async def save(self):
        """保存资源"""
        db_manager = PostgreSQLManager()
        if self.id:
            # 更新现有资源
            query = """
            UPDATE study_resources SET name = %s, description = %s, content = %s,
                   resource_type = %s, category_id = %s, difficulty_level = %s,
                   file_path = %s, file_size = %s, file_hash = %s, thumbnail_path = %s,
                   duration = %s, tags = %s, keywords = %s, author = %s, source_url = %s,
                   is_active = %s, is_featured = %s, estimated_time = %s,
                   prerequisites = %s, updated_at = %s, published_at = %s
            WHERE id = %s
            """
            params = (
                self.title, self.description, self.content,
                self.resource_type.value, self.category_id, self.difficulty_level.value,
                self.file_path, self.file_size, self.file_hash, self.thumbnail_path,
                self.duration, json.dumps(self.tags), json.dumps(self.keywords),
                self.author, self.source_url, self.is_active, self.is_featured,
                self.estimated_time, json.dumps(self.prerequisites),
                datetime.now(), self.published_at, self.id
            )
        else:
            # 创建新资源
            query = """
            INSERT INTO study_resources (name, description, content, resource_type, category_id,
                                       difficulty_level, file_path, file_size, file_hash,
                                       thumbnail_path, duration, tags, keywords, author,
                                       source_url, is_active, is_featured, estimated_time,
                                       prerequisites, created_at, updated_at, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            params = (
                self.title, self.description, self.content,
                self.resource_type.value, self.category_id, self.difficulty_level.value,
                self.file_path, self.file_size, self.file_hash, self.thumbnail_path,
                self.duration, json.dumps(self.tags), json.dumps(self.keywords),
                self.author, self.source_url, self.is_active, self.is_featured,
                self.estimated_time, json.dumps(self.prerequisites),
                self.created_at, self.updated_at, self.published_at
            )
            result = await db_manager.execute_query(query, params, fetch_one=True)
            self.id = result['id']
            return
        
        await db_manager.execute_query(query, params)

    def update_file_path(self, new_file_path: str) -> None:
        """更新当前资源的文件路径
        函数级注释：
        - 输入：新的文件路径字符串（建议为绝对路径，指向持久化卷目录）
        - 动作：更新数据库中的 `file_path` 字段，并刷新 `updated_at`；同时更新实例属性。
        - 适用场景：迁移或修复路径、批量导入后回写真实存储位置。
        """
        if not self.id:
            raise ValueError("资源未持久化，缺少id，无法更新文件路径")
        self.file_path = new_file_path
        self.updated_at = datetime.now()
        db_manager = PostgreSQLManager()
        query = "UPDATE study_resources SET file_path = %s, updated_at = %s WHERE id = %s"
        db_manager.execute_query(query, (self.file_path, self.updated_at, self.id))

    @classmethod
    def update_file_path_by_id(cls, resource_id: int, new_file_path: str) -> None:
        """根据资源ID更新文件路径
        函数级注释：
        - 输入：资源ID与新文件路径字符串。
        - 动作：直接执行SQL更新，无需先加载完整模型实例，适合批量修复。
        - 注意：仅更新 `file_path` 与 `updated_at`，不改动其他字段。
        """
        if not resource_id or not isinstance(resource_id, int):
            raise ValueError("resource_id必须为有效整数")
        if not new_file_path:
            raise ValueError("new_file_path不能为空")
        db_manager = PostgreSQLManager()
        query = "UPDATE study_resources SET file_path = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        db_manager.execute_query(query, (new_file_path, resource_id))

@dataclass
class UserStudyRecord:
    """用户学习记录模型 - PostgreSQL版本"""
    id: Optional[int] = None
    user_id: int = 0                     # 用户ID
    resource_id: int = 0                 # 资源ID
    study_status: StudyStatus = StudyStatus.NOT_STARTED
    
    # 学习进度
    progress_percentage: float = 0.0     # 学习进度百分比
    current_position: str = ""           # 当前位置（如视频播放位置）
    total_study_time: int = 0            # 总学习时间（秒）
    
    # 时间记录
    started_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 学习笔记和评价
    notes: str = ""                      # 学习笔记
    rating: Optional[float] = None       # 用户评分
    review: str = ""                     # 用户评价
    
    # 统计信息
    access_count: int = 0                # 访问次数
    bookmark_count: int = 0              # 收藏次数
    
    def __post_init__(self):
        if self.started_at is None and self.study_status != StudyStatus.NOT_STARTED:
            self.started_at = datetime.now()
        if self.last_accessed_at is None:
            self.last_accessed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['study_status'] = self.study_status.value
        return data
    
    @classmethod
    def create(cls, user_id: int, resource_id: int) -> 'UserStudyRecord':
        """创建新学习记录"""
        record = cls(
            user_id=user_id,
            resource_id=resource_id,
            study_status=StudyStatus.NOT_STARTED
        )
        
        # 使用PostgreSQL管理器插入数据
        db_manager = PostgreSQLManager()
        query = """
        INSERT INTO user_study_records (user_id, resource_id, study_status, progress_percentage,
                                      current_position, total_study_time, started_at,
                                      last_accessed_at, notes, access_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        params = (
            record.user_id, record.resource_id, record.study_status.value,
            record.progress_percentage, record.current_position, record.total_study_time,
            record.started_at, record.last_accessed_at, record.notes, record.access_count
        )
        
        result = db_manager.execute_query(query, params, fetch_one=True)
        record.id = result['id']
        
        return record
    
    @classmethod
    def get_by_user_and_resource(cls, user_id: int, resource_id: int) -> Optional['UserStudyRecord']:
        """根据用户ID和资源ID获取学习记录"""
        db_manager = PostgreSQLManager()
        query = "SELECT * FROM user_study_records WHERE user_id = %s AND resource_id = %s"
        result = db_manager.execute_query(query, (user_id, resource_id), fetch_one=True)
        
        if result:
            result['study_status'] = StudyStatus(result['study_status'])
            return cls(**result)
        return None
    
    @classmethod
    async def get_user_records(cls, user_id: int, status: StudyStatus = None) -> List['UserStudyRecord']:
        """获取用户的学习记录"""
        db_manager = PostgreSQLManager()
        
        if status:
            query = "SELECT * FROM user_study_records WHERE user_id = %s AND study_status = %s ORDER BY last_accessed_at DESC"
            params = (user_id, status.value)
        else:
            query = "SELECT * FROM user_study_records WHERE user_id = %s ORDER BY last_accessed_at DESC"
            params = (user_id,)
        
        results = await db_manager.execute_query(query, params)
        
        records = []
        for result in results:
            result['study_status'] = StudyStatus(result['study_status'])
            records.append(cls(**result))
        
        return records
    
    def start_study(self):
        """开始学习"""
        if self.study_status == StudyStatus.NOT_STARTED:
            self.study_status = StudyStatus.IN_PROGRESS
            self.started_at = datetime.now()
        self.last_accessed_at = datetime.now()
        self.access_count += 1
    
    def update_progress(self, progress: float, position: int = 0, study_time: int = 0):
        """更新学习进度"""
        self.progress_percentage = min(100.0, max(0.0, progress))
        self.current_position = position
        self.total_study_time += study_time
        self.last_accessed_at = datetime.now()
        
        if self.progress_percentage >= 100.0:
            self.study_status = StudyStatus.COMPLETED
            self.completed_at = datetime.now()
        elif self.study_status == StudyStatus.NOT_STARTED:
            self.study_status = StudyStatus.IN_PROGRESS
            self.started_at = datetime.now()
    
    def pause_study(self):
        """暂停学习"""
        if self.study_status == StudyStatus.IN_PROGRESS:
            self.study_status = StudyStatus.PAUSED
    
    def resume_study(self):
        """恢复学习"""
        if self.study_status == StudyStatus.PAUSED:
            self.study_status = StudyStatus.IN_PROGRESS
        self.last_accessed_at = datetime.now()
    
    def complete_study(self):
        """完成学习"""
        self.study_status = StudyStatus.COMPLETED
        self.progress_percentage = 100.0
        self.completed_at = datetime.now()
        self.last_accessed_at = datetime.now()
    
    def save(self):
        """保存学习记录"""
        db_manager = PostgreSQLManager()
        if self.id:
            # 更新现有记录
            query = """
            UPDATE user_study_records SET study_status = %s, progress_percentage = %s,
                   current_position = %s, total_study_time = %s, started_at = %s,
                   last_accessed_at = %s, completed_at = %s, notes = %s, rating = %s,
                   review = %s, access_count = %s, bookmark_count = %s
            WHERE id = %s
            """
            params = (
                self.study_status.value, self.progress_percentage, self.current_position,
                self.total_study_time, self.started_at, self.last_accessed_at,
                self.completed_at, self.notes, self.rating, self.review,
                self.access_count, self.bookmark_count, self.id
            )
        else:
            # 创建新记录
            query = """
            INSERT INTO user_study_records (user_id, resource_id, study_status, progress_percentage,
                                          current_position, total_study_time, started_at,
                                          last_accessed_at, completed_at, notes, rating,
                                          review, access_count, bookmark_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            params = (
                self.user_id, self.resource_id, self.study_status.value,
                self.progress_percentage, self.current_position, self.total_study_time,
                self.started_at, self.last_accessed_at, self.completed_at,
                self.notes, self.rating, self.review, self.access_count, self.bookmark_count
            )
            result = db_manager.execute_query(query, params, fetch_one=True)
            self.id = result['id']
            return
        
        db_manager.execute_query(query, params)

# 学习资源管理器
class StudyResourceManager:
    """学习资源管理器 - PostgreSQL版本"""
    
    def __init__(self):
        self.pg_manager = PostgreSQLManager()
    
    async def init_tables(self):
        """初始化数据库表"""
        # 这个方法会在完整的schema初始化中处理
        pass
    
    async def create_category(self, category_data: Dict[str, Any]) -> ResourceCategory:
        """创建资源分类"""
        return await ResourceCategory.create(**category_data)
    
    async def get_categories(self) -> List[ResourceCategory]:
        """获取所有分类"""
        return await ResourceCategory.get_all_active()
    
    async def get_category_tree(self) -> List[Dict[str, Any]]:
        """获取分类树"""
        return await ResourceCategory.get_tree()
    
    async def create_resource(self, resource_data: Dict[str, Any]) -> StudyResource:
        """创建学习资源"""
        return await StudyResource.create(**resource_data)
    
    async def get_resources(self, page: int = 1, limit: int = 10, **filters) -> Tuple[List[StudyResource], int]:
        """获取资源列表"""
        return await StudyResource.get_paginated(page, limit, **filters)
    
    async def get_resource_by_id(self, resource_id: int) -> Optional[StudyResource]:
        """根据ID获取资源"""
        return await StudyResource.get_by_id(resource_id)
    
    async def create_study_record(self, user_id: int, resource_id: int) -> UserStudyRecord:
        """创建学习记录"""
        # 检查是否已存在记录
        existing_record = await UserStudyRecord.get_by_user_and_resource(user_id, resource_id)
        if existing_record:
            return existing_record
        
        return await UserStudyRecord.create(user_id, resource_id)
    
    async def get_user_study_records(self, user_id: int, status: StudyStatus = None) -> List[UserStudyRecord]:
        """获取用户学习记录"""
        return await UserStudyRecord.get_user_records(user_id, status)
    
    async def update_study_progress(self, user_id: int, resource_id: int,
                                  progress: float, position: int = 0, study_time: int = 0):
        """更新学习进度"""
        record = await UserStudyRecord.get_by_user_and_resource(user_id, resource_id)
        if not record:
            record = await UserStudyRecord.create(user_id, resource_id)
        
        record.update_progress(progress, position, study_time)
        await record.save()
        
        # 同时更新资源的查看次数
        resource = await StudyResource.get_by_id(resource_id)
        if resource:
            await resource.increment_view_count()
    
    async def get_study_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取用户学习统计"""
        records = await UserStudyRecord.get_user_records(user_id)
        
        stats = {
            'total_resources': len(records),
            'completed_resources': len([r for r in records if r.study_status == StudyStatus.COMPLETED]),
            'in_progress_resources': len([r for r in records if r.study_status == StudyStatus.IN_PROGRESS]),
            'total_study_time': sum(r.total_study_time for r in records),
            'average_progress': sum(r.progress_percentage for r in records) / len(records) if records else 0,
            'completion_rate': len([r for r in records if r.study_status == StudyStatus.COMPLETED]) / len(records) * 100 if records else 0
        }
        
        return stats

# 全局学习资源管理器实例
study_resource_manager = StudyResourceManager()
