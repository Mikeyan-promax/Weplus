"""
学习资源管理API - PostgreSQL版本
提供学习资源的上传、搜索、分类、评分等功能
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import uuid
import shutil
import logging
import hashlib
from pathlib import Path
from pathlib import PureWindowsPath, PurePosixPath
import json
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime
from urllib.parse import urlparse
import zipfile
from zipfile import ZipFile
from io import BytesIO

# 导入数据库模型和配置
from database.study_resources_models import (
    StudyResource, ResourceCategory, UserStudyRecord, 
    StudyResourceManager, ResourceType, DifficultyLevel, StudyStatus
)
from database.config import get_db_connection

# 导入管理员认证
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/study-resources", tags=["学习资源管理"])

"""
文件存储配置：优先环境变量，其次全局设置，最后使用本地默认目录
函数级注释：
- 目标：在不同运行环境（本地/容器/Railway）统一文件保存与解析的基准目录。
- 优先级：
  1) 环境变量 `STUDY_RESOURCES_DIR` / `WEPLUS_STUDY_RESOURCES_DIR`
  2) 全局设置 `settings.UPLOAD_DIR`（下挂 `study_resources` 子目录）
  3) 项目内默认 `backend/app/data/study_resources`
- 同时维护 `FALLBACK_DIRS` 以便解析旧路径或迁移后的路径。
"""

# 引入全局配置，提供额外的回退目录支持
try:
    from app.core.config import settings
except Exception:
    settings = None

def _compute_upload_dir() -> Path:
    """计算并返回用于保存学习资源文件的主目录。"""
    # 1) 环境变量优先（便于Railway/容器挂载持久化卷，如 /data/study_resources）
    env_dir = os.getenv('STUDY_RESOURCES_DIR') or os.getenv('WEPLUS_STUDY_RESOURCES_DIR')
    if env_dir:
        p = Path(env_dir)
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"使用环境变量指定的学习资源目录: {p}")
        return p

    # 2) 全局设置（如 settings.UPLOAD_DIR），统一在其下创建 study_resources 子目录
    if settings and getattr(settings, 'UPLOAD_DIR', None):
        base = Path(getattr(settings, 'UPLOAD_DIR'))
        p = base / 'study_resources'
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"使用全局设置的学习资源目录: {p}")
        return p

    # 3) 默认项目内目录
    p = Path(__file__).parent.parent.parent / "data" / "study_resources"
    p.mkdir(parents=True, exist_ok=True)
    logger.info(f"使用默认学习资源目录: {p}")
    return p

# 主上传目录
UPLOAD_DIR = _compute_upload_dir()

# 可能的回退目录集合（按优先级）
FALLBACK_DIRS = []

# 将环境变量目录与全局设置目录加入回退，用于兼容旧数据或迁移情况
try:
    env_dir = os.getenv('STUDY_RESOURCES_DIR') or os.getenv('WEPLUS_STUDY_RESOURCES_DIR')
    if env_dir:
        FALLBACK_DIRS.append(Path(env_dir))
except Exception:
    pass

if settings and getattr(settings, 'UPLOAD_DIR', None):
    base = Path(getattr(settings, 'UPLOAD_DIR'))
    FALLBACK_DIRS.append(base / 'study_resources')
    FALLBACK_DIRS.append(base)

# 同时加入历史默认目录，便于解析之前写入的路径
historical_default = Path(__file__).parent.parent.parent / "data" / "study_resources"
if historical_default != UPLOAD_DIR:
    FALLBACK_DIRS.append(historical_default)

# 追加历史常用目录（旧版本可能写入到 uploads 而非 study_resources）
old_uploads_dir_1 = Path(__file__).parent.parent.parent / "data" / "uploads"
old_uploads_dir_2 = Path(__file__).parent.parent.parent / "uploads"
for d in [old_uploads_dir_1, old_uploads_dir_2]:
    try:
        FALLBACK_DIRS.append(d)
    except Exception:
        pass

def _get_media_type(file_path: Path) -> str:
    """根据文件扩展名获取媒体类型（MIME）
    - 统一由后端返回合理的类型，前端根据 Blob.type 渲染
    """
    media_type_map = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    return media_type_map.get(file_path.suffix.lower(), 'application/octet-stream')

def _resolve_resource_file_path(resource: Any) -> Path:
    """解析并定位资源文件的真实路径（容错解析）
    函数级注释：
    - 输入：StudyResource 实例或字典，内含 file_path 字段（可能为绝对/相对路径或仅文件名）
    - 逻辑：
      1) 优先尝试原始路径；
      2) 若不存在，则以原始路径的文件名在主目录 UPLOAD_DIR 下查找；
      3) 再依次在 FALLBACK_DIRS 中查找（包含历史默认目录、环境变量目录等）；
    - 输出：存在的 Path 对象；若无法定位则返回最可能的候选（用于错误日志）
    """
    # 提取原始路径字符串
    raw_path = None
    if isinstance(resource, dict):
        raw_path = resource.get('file_path')
    else:
        raw_path = getattr(resource, 'file_path', None)

    if not raw_path:
        return UPLOAD_DIR / "__missing__"

    # 统一规范化原始路径，兼容 Windows 与 POSIX
    raw_str = str(raw_path)
    primary = Path(raw_str)
    if primary.exists():
        return primary

    # 以文件名为准进行回退查找（双重兼容）
    basename_candidates = []
    try:
        basename_candidates.append(PureWindowsPath(raw_str).name)
    except Exception:
        pass
    try:
        basename_candidates.append(PurePosixPath(raw_str.replace('\\', '/')).name)
    except Exception:
        pass
    # 去重并剔除空值
    basename_candidates = [b for i, b in enumerate(basename_candidates) if b and b not in basename_candidates[:i]]
    if not basename_candidates:
        basename_candidates = [Path(raw_str).name]

    # 追加候选目录（主目录 + 回退目录 + 常见容器持久化目录）
    extra_fallbacks = []
    try:
        # 容器常用持久化卷路径（Railway Volumes 挂载点）
        common_data_dir = Path('/data/study_resources')
        extra_fallbacks.append(common_data_dir)
        # 历史容器路径（旧构建可能落在 /data/uploads）
        extra_fallbacks.append(Path('/data/uploads'))
    except Exception:
        pass

    candidates: List[Path] = []
    for bn in basename_candidates:
        candidates.append(UPLOAD_DIR / bn)
        for d in FALLBACK_DIRS:
            candidates.append(d / bn)
        for d in extra_fallbacks:
            candidates.append(d / bn)

    for cand in candidates:
        try:
            if cand.exists():
                return cand
        except Exception:
            # 某些平台路径解析异常时忽略
            continue

    # 所有候选均不存在，返回主目录下的候选用于错误提示
    missing = UPLOAD_DIR / basename_candidates[0]
    logger.warning(
        f"资源文件定位失败，resource_id={getattr(resource, 'id', None) or (resource.get('id') if isinstance(resource, dict) else None)}, "
        f"原始路径={raw_path}, 主目录={UPLOAD_DIR}, 回退目录={[str(d) for d in FALLBACK_DIRS + extra_fallbacks]}, "
        f"候选文件名={basename_candidates}, 尝试路径样本={str(candidates[:6])}, 返回候选={missing}"
    )
    return missing

# HTTP Bearer认证
security = HTTPBearer()

# JWT配置 - 确保与admin_auth_api.py中的密钥一致
JWT_SECRET_KEY = "weplus_admin_secret_key_2024"
JWT_ALGORITHM = "HS256"

# 管理员认证依赖
async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证管理员token"""
    try:
        token = credentials.credentials
        # 打印token用于调试
        logger.info(f"收到管理员Token: {token[:10]}...")
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # 检查是否为管理员
        role = payload.get("role")
        logger.info(f"管理员角色: {role}")
        
        if role not in ["admin", "super_admin", "manager"]:
            logger.warning(f"非管理员角色尝试访问: {role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        
        return payload
    except ExpiredSignatureError as e:
        logger.error(f"Token已过期: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期"
        )
    except InvalidTokenError as e:
        logger.error(f"无效的Token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token"
        )
    except Exception as e:
        logger.error(f"验证Token时发生未知错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"认证失败: {str(e)}"
        )

# Pydantic模型定义
class ResourceUploadRequest(BaseModel):
    """资源上传请求模型"""
    title: str = Field(..., description="资源标题")
    description: Optional[str] = Field(None, description="资源描述")
    category_id: int = Field(..., description="分类ID")
    difficulty_level: str = Field("beginner", description="难度级别")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    author: Optional[str] = Field(None, description="作者")
    source_url: Optional[str] = Field(None, description="来源URL")

class ResourceSearchRequest(BaseModel):
    """资源搜索请求模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category_id: Optional[int] = Field(None, description="分类ID")
    resource_type: Optional[str] = Field(None, description="资源类型")
    difficulty_level: Optional[str] = Field(None, description="难度级别")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")

class CategoryCreateRequest(BaseModel):
    """分类创建请求模型"""
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    icon: Optional[str] = Field(None, description="分类图标")
    color: Optional[str] = Field("#4A90E2", description="分类颜色")

class RatingRequest(BaseModel):
    """评分请求模型"""
    rating: float = Field(..., ge=1, le=5, description="评分(1-5)")
    review: Optional[str] = Field(None, description="评价内容")

class StudyProgressRequest(BaseModel):
    """学习进度请求模型"""
    progress_percentage: float = Field(..., ge=0, le=100, description="学习进度百分比")
    current_position: Optional[int] = Field(None, description="当前位置")
    notes: Optional[str] = Field(None, description="学习笔记")

# API端点实现

@router.get("/", summary="获取学习资源列表")
async def get_resources(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    difficulty_level: Optional[str] = Query(None, description="难度级别"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    is_featured: Optional[bool] = Query(None, description="是否推荐")
):
    """获取学习资源列表（分页）"""
    try:
        # 构建查询条件
        conditions = ["is_active = true"]  # 只显示激活的资源
        
        if category_id:
            conditions.append(f"category_id = {category_id}")
        if difficulty_level:
            conditions.append(f"difficulty_level = '{difficulty_level}'")
        if resource_type:
            conditions.append(f"file_type = '{resource_type}'")
        if is_featured is not None:
            conditions.append(f"is_featured = {is_featured}")
        
        where_clause = " AND ".join(conditions)
        
        # 获取分页数据
        resources, total = StudyResource.get_paginated(
            page=page,
            limit=page_size,
            category_id=category_id if category_id else None,
            resource_type=ResourceType(resource_type) if resource_type else None,
            difficulty_level=DifficultyLevel(difficulty_level) if difficulty_level else None
        )
        
        return {
            "success": True,
            "data": resources,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "message": "获取资源列表成功"
        }
        
    except Exception as e:
        logger.error(f"获取资源列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.post("/upload", summary="上传学习资源")
async def upload_resource(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    difficulty_level: str = Form("beginner"),
    tags: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None)
):
    """上传学习资源文件"""
    try:
        # 验证文件类型
        allowed_types = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'audio/mpeg': 'mp3',
            'audio/wav': 'wav',
            'video/mp4': 'mp4',
            'video/avi': 'avi',
            'text/plain': 'txt'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )
        
        # 生成唯一文件名
        file_extension = allowed_types[file.content_type]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = file_path.stat().st_size
        
        # 解析标签和关键词
        tags_list = [tag.strip() for tag in tags.split(',')] if tags else []
        keywords_list = [kw.strip() for kw in keywords.split(',')] if keywords else []
        
        # 创建资源记录
        resource = StudyResource.create(
            title=title,
            description=description or "",
            file_type=file_extension.lstrip('.'),  # 去掉点号
            category_id=category_id,
            file_path=str(file_path),
            file_size=file_size,
            original_filename=file.filename,
            content_hash=hashlib.md5(file.filename.encode()).hexdigest(),
            difficulty_level=difficulty_level,
            tags=','.join(tags_list) if tags_list else '',
            metadata='{}',
            uploader_id=1  # 临时使用固定用户ID
        )
        
        resource_id = resource.id
        
        # 后台任务：生成缩略图、提取文本等
        background_tasks.add_task(process_uploaded_file, resource_id, file_path)
        
        return {
            "success": True,
            "message": "资源上传成功",
            "resource_id": resource_id,
            "filename": unique_filename
        }
        
    except Exception as e:
        logger.error(f"资源上传失败: {str(e)}")
        # 清理已上传的文件
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.post("/admin/upload", summary="管理员上传学习资源")
async def admin_upload_resource(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    difficulty_level: str = Form("beginner"),
    tags: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    admin_user: dict = Depends(verify_admin_token)
):
    """管理员上传学习资源文件"""
    try:
        # 验证文件类型
        allowed_types = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'audio/mpeg': 'mp3',
            'audio/wav': 'wav',
            'video/mp4': 'mp4',
            'video/avi': 'avi',
            'text/plain': 'txt',
            'text/markdown': 'md',
            'image/jpeg': 'jpg',
            'image/png': 'png'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )
        
        # 生成唯一文件名
        file_extension = allowed_types[file.content_type]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = file_path.stat().st_size
        
        # 解析标签和关键词
        tags_list = [tag.strip() for tag in tags.split(',')] if tags else []
        keywords_list = [kw.strip() for kw in keywords.split(',')] if keywords else []
        
        # 创建资源记录
        resource = StudyResource.create(
            title=title,
            description=description or "",
            file_type=file_extension.lstrip('.'),  # 去掉点号
            category_id=category_id,
            file_path=str(file_path),
            file_size=file_size,
            original_filename=file.filename,
            content_hash=hashlib.md5(file.filename.encode()).hexdigest(),
            difficulty_level=difficulty_level,
            tags=','.join(tags_list) if tags_list else '',
            metadata=json.dumps({
                'author': author,
                'source_url': source_url,
                'keywords': keywords_list,
                'uploaded_by': admin_user.get('sub', 'admin')
            }),
            uploader_id=1  # 管理员用户ID
        )
        
        resource_id = resource.id
        
        # 后台任务：生成缩略图、提取文本等
        background_tasks.add_task(process_uploaded_file, resource_id, file_path)
        
        return {
            "success": True,
            "message": "管理员资源上传成功",
            "resource_id": resource_id,
            "filename": unique_filename,
            "uploaded_by": admin_user.get('sub', 'admin')
        }
        
    except Exception as e:
        logger.error(f"管理员资源上传失败: {str(e)}")
        # 清理已上传的文件
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

# 后台处理函数
async def process_uploaded_file(resource_id: int, file_path: Path):
    """处理上传的文件（后台任务）"""
    try:
        # 这里可以添加文件处理逻辑，如：
        # 1. 生成缩略图
        # 2. 提取文本内容
        # 3. 生成预览
        # 4. 病毒扫描等
        logger.info(f"开始处理资源文件: {resource_id}")
        
        # 模拟处理时间
        import asyncio
        await asyncio.sleep(1)
        
        logger.info(f"资源文件处理完成: {resource_id}")
        
    except Exception as e:
        logger.error(f"处理资源文件失败: {resource_id}, 错误: {str(e)}")

@router.get("/search", summary="搜索学习资源")
async def search_resources(
    query: Optional[str] = Query(None, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    difficulty_level: Optional[str] = Query(None, description="难度级别"),
    tags: Optional[str] = Query(None, description="标签(逗号分隔)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """搜索学习资源"""
    try:
        # 解析标签
        tags_list = [tag.strip() for tag in tags.split(',')] if tags else None
        
        # 构建搜索条件
        search_params = {
            'query': query,
            'category_id': category_id,
            'resource_type': ResourceType(resource_type) if resource_type else None,
            'difficulty_level': DifficultyLevel(difficulty_level) if difficulty_level else None,
            'tags': tags_list,
            'page': page,
            'page_size': page_size
        }
        
        # 执行搜索
        resources, total_count = StudyResource.search(**search_params)
        
        return {
            "success": True,
            "data": [resource.to_dict() for resource in resources],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "pages": (total_count + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"资源搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/admin/resources", summary="管理员获取所有资源")
async def admin_get_all_resources(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    admin_user: dict = Depends(verify_admin_token)
):
    """管理员获取所有学习资源（包含详细信息）"""
    try:
        # 获取分页数据
        resources, total = StudyResource.get_paginated(
            page=page,
            limit=page_size,
            category_id=category_id
        )
        
        return {
            "success": True,
            "data": resources,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "message": "获取管理员资源列表成功"
        }
        
    except Exception as e:
        logger.error(f"获取管理员资源列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.put("/admin/resource/{resource_id}", summary="管理员更新资源")
async def admin_update_resource(
    resource_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    difficulty_level: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    admin_user: dict = Depends(verify_admin_token)
):
    """管理员更新学习资源信息"""
    try:
        # 检查资源是否存在
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        # 构建更新数据
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if category_id is not None:
            update_data['category_id'] = category_id
        if difficulty_level is not None:
            update_data['difficulty_level'] = difficulty_level
        if tags is not None:
            update_data['tags'] = tags
        if status is not None:
            update_data['status'] = status
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        # 更新资源
        StudyResource.update(resource_id, **update_data)
        
        return {
            "success": True,
            "message": "资源更新成功",
            "resource_id": resource_id,
            "updated_by": admin_user.get('sub', 'admin')
        }
        
    except Exception as e:
        logger.error(f"更新资源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/admin/resource/{resource_id}", summary="管理员删除资源")
async def admin_delete_resource(
    resource_id: int,
    admin_user: dict = Depends(verify_admin_token)
):
    """管理员删除学习资源"""
    try:
        # 检查资源是否存在
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        # 删除文件
        if resource.get('file_path'):
            file_path = Path(resource['file_path'])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"已删除文件: {file_path}")
        
        # 删除数据库记录
        StudyResource.delete(resource_id)
        
        return {
            "success": True,
            "message": "资源删除成功",
            "resource_id": resource_id,
            "deleted_by": admin_user.get('sub', 'admin')
        }
        
    except Exception as e:
        logger.error(f"删除资源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.get("/admin/scan-missing", summary="管理员缺失文件巡检报告")
async def admin_scan_missing_resources(admin_user: dict = Depends(verify_admin_token)):
    """巡检所有学习资源的文件存在性并生成修复建议
    函数级注释：
    - 读取数据库中的资源 `id/title/file_path/source_url`；调用容错解析 `_resolve_resource_file_path`。
    - 输出每条资源的文件状态、建议路径（若能在主目录/回退目录找到同名文件）。
    - 适用于Railway迁移/挂载持久化卷后的一次性巡检。
    """
    try:
        report = []
        total = 0
        missing = 0

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, file_path, source_url FROM study_resources ORDER BY id")
                rows = cur.fetchall()

        for row in rows:
            # 根据游标返回类型兼容元组或字典
            if isinstance(row, dict):
                rid = row.get('id')
                title = row.get('title')
                raw_path = row.get('file_path')
                src_url = row.get('source_url')
            else:
                rid, title, raw_path, src_url = row[0], row[1], row[2], row[3]

            total += 1
            resource = StudyResource.get_by_id(int(rid))
            resolved = _resolve_resource_file_path(resource)

            exists = resolved.exists()
            if not exists:
                missing += 1
            # 生成建议路径：主目录下同名优先
            basename = Path(str(raw_path)).name if raw_path else None
            suggested = None
            if basename:
                candidates = [UPLOAD_DIR / basename]
                for d in FALLBACK_DIRS:
                    candidates.append(d / basename)
                # 容器常见持久化卷
                candidates.append(Path('/data/study_resources') / basename)
                candidates.append(Path('/data/uploads') / basename)
                for c in candidates:
                    try:
                        if c.exists():
                            suggested = str(c)
                            break
                    except Exception:
                        pass

            report.append({
                "id": rid,
                "title": title,
                "raw_file_path": raw_path,
                "resolved_path": str(resolved),
                "exists": exists,
                "source_url": src_url,
                "suggested_path": suggested
            })

        return {
            "success": True,
            "summary": {
                "total": total,
                "missing": missing,
                "upload_dir": str(UPLOAD_DIR)
            },
            "data": report
        }
    except Exception as e:
        logger.error(f"缺失文件巡检失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"巡检失败: {str(e)}")

@router.post("/admin/import-zip", summary="管理员ZIP批量导入并修复路径")
async def admin_import_zip_and_fix(
    zip_file: UploadFile = File(...),
    overwrite_existing: bool = Form(True),
    admin_user: dict = Depends(verify_admin_token)
):
    """上传ZIP压缩包并批量导入学习资源文件，同时修复数据库中的文件路径
    函数级注释：
    - 将ZIP内容解压到 `UPLOAD_DIR/zip_imports/<uuid>`，确保与持久化卷一致；
    - 按 `original_filename` 或现有 `file_path` 的基本文件名进行匹配，更新 `file_path`；
    - 返回导入/更新统计与无法匹配的文件列表。
    """
    try:
        # 保存ZIP到内存并解压到临时目录
        tmp_root = UPLOAD_DIR / "zip_imports" / str(uuid.uuid4())
        tmp_root.mkdir(parents=True, exist_ok=True)

        # 将上传的zip保存到磁盘（避免大文件内存爆）
        zip_path = tmp_root / (zip_file.filename or "import.zip")
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(zip_file.file, f)

        extracted_dir = tmp_root / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        with ZipFile(str(zip_path), 'r') as zf:
            zf.extractall(str(extracted_dir))

        # 构建文件名索引：basename -> 绝对路径
        file_index: Dict[str, Path] = {}
        for root, _, files in os.walk(extracted_dir):
            for name in files:
                p = Path(root) / name
                file_index[name] = p

        # 查询需要修复的资源（活跃资源）
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, original_filename, file_path FROM study_resources WHERE status = 'active' ORDER BY id")
                rows = cur.fetchall()

        updated: List[Dict[str, Any]] = []
        unmatched: List[str] = []

        for row in rows:
            if isinstance(row, dict):
                rid = row.get('id')
                original = row.get('original_filename')
                existing_path = row.get('file_path')
            else:
                rid, original, existing_path = row[0], row[1], row[2]

            candidates = []
            if original:
                candidates.append(original)
            if existing_path:
                candidates.append(Path(str(existing_path)).name)
            # 去重
            candidates = [c for i, c in enumerate(candidates) if c and c not in candidates[:i]]

            target_file: Optional[Path] = None
            for bn in candidates:
                if bn in file_index:
                    target_file = file_index[bn]
                    break

            if not target_file:
                # 记录无法匹配的文件名，便于人工确认
                unmatched.append(original or existing_path or f"id:{rid}")
                continue

            # 将文件移动/复制到主上传目录，形成最终落地路径
            final_path = UPLOAD_DIR / target_file.name
            if final_path.exists():
                if overwrite_existing:
                    try:
                        shutil.copy2(str(target_file), str(final_path))
                    except Exception:
                        pass
                # 若不覆盖，保留现有文件，仍回写路径到数据库
            else:
                shutil.copy2(str(target_file), str(final_path))

            # 更新数据库中的文件路径
            try:
                StudyResource.update_file_path_by_id(int(rid), str(final_path))
                updated.append({"id": rid, "new_path": str(final_path)})
            except Exception as ue:
                logger.warning(f"更新资源路径失败 id={rid}: {ue}")

        return {
            "success": True,
            "message": "ZIP批量导入并修复路径完成",
            "stats": {
                "import_dir": str(extracted_dir),
                "upload_dir": str(UPLOAD_DIR),
                "updated_count": len(updated),
                "unmatched_count": len(unmatched)
            },
            "updated": updated,
            "unmatched": unmatched
        }
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP文件格式不正确或已损坏")
    except Exception as e:
        logger.error(f"ZIP批量导入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.post("/admin/category", summary="管理员创建分类")
async def admin_create_category(
    name: str = Form(...),
    code: str = Form(...),
    description: Optional[str] = Form(None),
    admin_user: dict = Depends(verify_admin_token)
):
    """管理员创建新的资源分类"""
    try:
        # 检查分类代码是否已存在
        existing = ResourceCategory.get_by_code(code)
        if existing:
            raise HTTPException(status_code=400, detail="分类代码已存在")
        
        # 创建分类
        category = ResourceCategory.create(
            name=name,
            code=code,
            description=description or ""
        )
        
        return {
            "success": True,
            "message": "分类创建成功",
            "category": category.to_dict(),
            "created_by": admin_user.get('sub', 'admin')
        }
        
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

# 前端需要的端点 - 必须在参数化路由之前
@router.get("/categories", summary="获取资源分类列表")
async def get_categories_for_frontend():
    """获取所有资源分类 - 前端使用"""
    try:
        categories = ResourceCategory.get_all_active()
        return {
            "success": True,
            "data": [category.to_dict() for category in categories]
        }
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.get("/resources", summary="获取学习资源列表")
async def get_resources_for_frontend(
    category_id: Optional[int] = Query(None, description="分类ID"),
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取学习资源列表 - 前端使用"""
    try:
        # 获取资源列表
        resources, total = StudyResource.get_paginated(
            page=page, 
            limit=limit, 
            category_id=category_id,
            search_query=search
        )
        
        return {
            "success": True,
            "data": resources,  # 现在直接返回字典列表
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        logger.error(f"获取资源列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.get("/{resource_id}", summary="获取资源详情")
async def get_resource(resource_id: int):
    """获取指定资源的详细信息"""
    try:
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        # 增加查看次数
        # await resource.increment_view_count()
        
        return {
            "success": True,
            "data": resource.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资源详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.get("/{resource_id}/preview", summary="预览资源文件")
async def preview_resource(resource_id: int):
    """预览资源文件
    函数级注释：
    - 根据资源ID定位文件（含容错回退），返回内联 FileResponse 用于前端预览。
    - 失败场景：资源不存在或文件无法找到；若存在有效的 source_url，则安全重定向到该URL。
    """
    try:
        # 获取资源信息
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        # 统一使用容错解析定位文件
        file_path = _resolve_resource_file_path(resource)
        if not file_path.exists():
            # 文件缺失时，尝试使用 source_url 安全重定向兜底
            src_url = getattr(resource, 'source_url', None) if not isinstance(resource, dict) else resource.get('source_url')
            if src_url:
                parsed = urlparse(src_url)
                if parsed.scheme in ('http', 'https'):
                    logger.warning(f"资源文件缺失，重定向到 source_url: id={resource_id}, url={src_url}")
                    return RedirectResponse(url=src_url, status_code=302)
            raise HTTPException(status_code=404, detail="文件不存在")

        # 根据文件类型返回适当的媒体类型
        media_type = _get_media_type(file_path)

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            headers={"Content-Disposition": "inline"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件预览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.get("/{resource_id}/download", summary="下载资源文件")
async def download_resource(resource_id: int):
    """下载资源文件
    函数级注释：
    - 根据资源ID定位文件（含容错回退），以附件形式返回 FileResponse。
    - 下载文件名优先使用资源标题 + 原始扩展名，避免出现双点扩展名。
    - 若文件缺失且存在有效的 source_url，则重定向到该URL作为兜底下载。
    """
    try:
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        # 容错解析文件路径
        if isinstance(resource, dict):
            title = resource.get('title', 'resource')
        else:
            title = getattr(resource, 'title', 'resource')

        file_path = _resolve_resource_file_path(resource)
        if not file_path.exists():
            # 文件缺失时，尝试使用 source_url 安全重定向兜底
            src_url = getattr(resource, 'source_url', None) if not isinstance(resource, dict) else resource.get('source_url')
            if src_url:
                parsed = urlparse(src_url)
                if parsed.scheme in ('http', 'https'):
                    logger.warning(f"资源文件缺失，下载重定向到 source_url: id={resource_id}, url={src_url}")
                    return RedirectResponse(url=src_url, status_code=302)
            raise HTTPException(status_code=404, detail="文件不存在")

        # 增加下载次数 - 暂时跳过，因为需要实现
        # await resource.increment_download_count()
        # 规范化下载文件名：标题 + 扩展名（不带双点）
        safe_suffix = file_path.suffix  # 例如 .pdf
        download_name = f"{title}{safe_suffix}"

        return FileResponse(
            path=str(file_path),
            filename=download_name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@router.get("/categories/list", summary="获取资源分类列表")
async def get_categories():
    """获取所有资源分类"""
    try:
        categories = ResourceCategory.get_all_active()
        return {
            "success": True,
            "data": [category.to_dict() for category in categories]
        }
        
    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.post("/categories", summary="创建资源分类")
async def create_category(request: CategoryCreateRequest):
    """创建新的资源分类"""
    try:
        category = ResourceCategory(
            name=request.name,
            description=request.description or "",
            parent_id=request.parent_id,
            icon=request.icon or "",
            color=request.color
        )
        
        category_id = category.create()
        
        return {
            "success": True,
            "message": "分类创建成功",
            "category_id": category_id
        }
        
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.post("/{resource_id}/rate", summary="评分资源")
async def rate_resource(resource_id: int, request: RatingRequest, user_id: int = 1):
    """对资源进行评分"""
    try:
        # 检查资源是否存在
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        # 获取或创建学习记录
        study_record = UserStudyRecord.get_by_user_and_resource(user_id, resource_id)
        if not study_record:
            study_record = UserStudyRecord.create(user_id, resource_id)
        
        # 更新评分
        study_record.rating = request.rating
        study_record.review = request.review or ""
        study_record.save()
        
        return {
            "success": True,
            "message": "评分成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"评分失败: {str(e)}")

@router.get("/{resource_id}/ratings", summary="获取资源评分")
async def get_resource_ratings(resource_id: int):
    """获取资源的评分信息"""
    try:
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        # 获取评分统计
        ratings = UserStudyRecord.get_ratings_by_resource(resource_id)
        
        return {
            "success": True,
            "data": {
                "average_rating": resource.rating,
                "rating_count": resource.rating_count,
                "ratings": ratings
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.post("/{resource_id}/progress", summary="更新学习进度")
async def update_study_progress(
    resource_id: int, 
    request: StudyProgressRequest, 
    user_id: int = 1
):
    """更新用户的学习进度"""
    try:
        # 获取或创建学习记录
        study_record = UserStudyRecord.get_by_user_and_resource(user_id, resource_id)
        if not study_record:
            study_record = UserStudyRecord.create(user_id, resource_id)
        
        # 更新进度
        study_record.progress_percentage = request.progress_percentage
        if request.current_position is not None:
            study_record.current_position = request.current_position
        if request.notes:
            study_record.notes = request.notes
        
        # 更新学习状态
        if request.progress_percentage >= 100:
            study_record.study_status = StudyStatus.COMPLETED
            study_record.completed_at = datetime.now()
        elif request.progress_percentage > 0:
            study_record.study_status = StudyStatus.IN_PROGRESS
            if not study_record.started_at:
                study_record.started_at = datetime.now()
        
        study_record.last_accessed_at = datetime.now()
        study_record.save()
        
        return {
            "success": True,
            "message": "学习进度更新成功"
        }
        
    except Exception as e:
        logger.error(f"更新学习进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/{resource_id}", summary="删除资源")
async def delete_resource(resource_id: int):
    """删除指定资源"""
    try:
        resource = StudyResource.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        
        # 软删除资源
        resource.delete()
        
        return {
            "success": True,
            "message": "资源删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除资源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# 后台任务函数
async def process_uploaded_file(resource_id: int, file_path: Path):
    """处理上传的文件（生成缩略图、提取文本等）"""
    try:
        # 这里可以添加文件处理逻辑
        # 例如：生成PDF缩略图、提取文档文本、音视频元数据等
        logger.info(f"开始处理文件: {file_path}")
        
        # 示例：更新资源的处理状态
        resource = StudyResource.get_by_id(resource_id)
        if resource:
            # 可以在这里添加更多的文件处理逻辑
            pass
            
    except Exception as e:
        logger.error(f"文件处理失败: {str(e)}")
