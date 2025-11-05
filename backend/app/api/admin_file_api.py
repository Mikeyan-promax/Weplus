"""
WePlus 后台管理系统 - 文件管理API
提供文件上传、下载、管理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Query, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import shutil
import uuid
from pathlib import Path
import mimetypes
import logging
import json

# 导入数据库配置
from database.admin_models import FileRecord, FileType, ProcessingStatus
from app.api.admin_user_api import verify_token, get_current_user, require_admin
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/admin/files", tags=["文件管理"])

# 文件存储配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 允许的文件类型和大小限制
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf',  # 文档
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',  # 图片
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',   # 视频
    '.mp3', '.wav', '.flac', '.aac', '.ogg',          # 音频
    '.zip', '.rar', '.7z', '.tar', '.gz',             # 压缩包
    '.xlsx', '.xls', '.csv', '.ppt', '.pptx'          # 办公文档
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Pydantic模型定义
class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: str
    upload_time: datetime
    uploader_id: int
    processing_status: str

class FileListResponse(BaseModel):
    """文件列表响应模型"""
    files: List[FileUploadResponse]
    total: int
    page: int
    limit: int
    total_pages: int

class FileUpdateRequest(BaseModel):
    """文件信息更新请求模型"""
    filename: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

# 工具函数
def get_file_type(filename: str) -> FileType:
    """根据文件扩展名确定文件类型"""
    ext = Path(filename).suffix.lower()
    
    if ext in ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf']:
        return FileType.DOCUMENT
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
        return FileType.IMAGE
    elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']:
        return FileType.VIDEO
    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
        return FileType.AUDIO
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return FileType.ARCHIVE
    else:
        return FileType.OTHER

def validate_file(file: UploadFile) -> None:
    """验证上传的文件"""
    # 检查文件扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}"
        )
    
    # 检查文件大小
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
        )

def save_uploaded_file(file: UploadFile, user_id: int) -> tuple:
    """保存上传的文件"""
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    filename = f"{file_id}{ext}"
    
    # 创建用户目录
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)
    
    # 保存文件
    file_path = user_dir / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 获取文件信息
    file_size = file_path.stat().st_size
    mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
    
    return str(file_path), file_size, mime_type

# API端点
@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: bool = Form(False),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """上传文件"""
    try:
        # 验证文件
        validate_file(file)
        
        # 保存文件
        file_path, file_size, mime_type = save_uploaded_file(file, current_user["user_id"])
        
        # 解析标签
        tag_list = []
        if tags:
            try:
                tag_list = json.loads(tags) if tags.startswith('[') else [tag.strip() for tag in tags.split(',')]
            except:
                tag_list = [tag.strip() for tag in tags.split(',')]
        
        # 创建文件记录
        file_record = FileRecord.create(
            filename=Path(file_path).name,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=get_file_type(file.filename),
            mime_type=mime_type,
            uploader_id=current_user["user_id"],
            description=description,
            tags=tag_list,
            is_public=is_public
        )
        
        logger.info(f"文件上传成功: {file.filename} by user {current_user['user_id']}")
        
        return FileUploadResponse(
            id=file_record.id,
            filename=file_record.filename,
            original_filename=file_record.original_filename,
            file_path=file_record.file_path,
            file_size=file_record.file_size,
            file_type=file_record.file_type.value,
            mime_type=file_record.mime_type,
            upload_time=file_record.upload_time,
            uploader_id=file_record.uploader_id,
            processing_status=file_record.processing_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败"
        )

@router.get("/", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    file_type: Optional[str] = Query(None, description="文件类型筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    uploader_id: Optional[int] = Query(None, description="上传者ID筛选"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取文件列表"""
    try:
        # 构建筛选条件
        filters = {}
        if file_type:
            filters['file_type'] = file_type
        if uploader_id:
            filters['uploader_id'] = uploader_id
        
        # 非管理员只能看到自己的文件和公开文件
        if current_user.get("role") not in ["admin", "super_admin"]:
            filters['user_filter'] = current_user["user_id"]
        
        # 获取文件列表
        files, total = FileRecord.get_paginated(
            page=page,
            limit=limit,
            search=search,
            filters=filters
        )
        
        # 转换为响应模型
        file_responses = [
            FileUploadResponse(
                id=file_record.id,
                filename=file_record.filename,
                original_filename=file_record.original_filename,
                file_path=file_record.file_path,
                file_size=file_record.file_size,
                file_type=file_record.file_type.value,
                mime_type=file_record.mime_type,
                upload_time=file_record.upload_time,
                uploader_id=file_record.uploader_id,
                processing_status=file_record.processing_status.value
            )
            for file_record in files
        ]
        
        total_pages = (total + limit - 1) // limit
        
        return FileListResponse(
            files=file_responses,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文件列表失败"
        )

@router.get("/{file_id}")
async def get_file_info(
    file_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取文件信息"""
    try:
        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            file_record.uploader_id != current_user["user_id"] and 
            not file_record.is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限访问此文件"
            )
        
        return FileUploadResponse(
            id=file_record.id,
            filename=file_record.filename,
            original_filename=file_record.original_filename,
            file_path=file_record.file_path,
            file_size=file_record.file_size,
            file_type=file_record.file_type.value,
            mime_type=file_record.mime_type,
            upload_time=file_record.upload_time,
            uploader_id=file_record.uploader_id,
            processing_status=file_record.processing_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文件信息失败"
        )

@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """下载文件"""
    try:
        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            file_record.uploader_id != current_user["user_id"] and 
            not file_record.is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限下载此文件"
            )
        
        # 检查文件是否存在
        file_path = Path(file_record.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在于服务器"
            )
        
        # 更新下载次数
        file_record.update_download_count()
        
        return FileResponse(
            path=str(file_path),
            filename=file_record.original_filename,
            media_type=file_record.mime_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件下载失败"
        )

@router.put("/{file_id}", response_model=FileUploadResponse)
async def update_file(
    file_id: int,
    update_data: FileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更新文件信息"""
    try:
        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            file_record.uploader_id != current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限修改此文件"
            )
        
        # 更新文件信息
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            file_record.update(**update_dict)
        
        return FileUploadResponse(
            id=file_record.id,
            filename=file_record.filename,
            original_filename=file_record.original_filename,
            file_path=file_record.file_path,
            file_size=file_record.file_size,
            file_type=file_record.file_type.value,
            mime_type=file_record.mime_type,
            upload_time=file_record.upload_time,
            uploader_id=file_record.uploader_id,
            processing_status=file_record.processing_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文件信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新文件信息失败"
        )

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """删除文件"""
    try:
        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限
        if (current_user.get("role") not in ["admin", "super_admin"] and 
            file_record.uploader_id != current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限删除此文件"
            )
        
        # 删除物理文件
        file_path = Path(file_record.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        file_record.delete()
        
        logger.info(f"文件删除成功: {file_record.original_filename} by user {current_user['user_id']}")
        
        return {"message": "文件删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除文件失败"
        )

@router.post("/batch-delete")
async def batch_delete_files(
    file_ids: List[int],
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """批量删除文件（管理员权限）"""
    try:
        deleted_count = 0
        for file_id in file_ids:
            try:
                file_record = FileRecord.get_by_id(file_id)
                if file_record:
                    # 删除物理文件
                    file_path = Path(file_record.file_path)
                    if file_path.exists():
                        file_path.unlink()
                    
                    # 删除数据库记录
                    file_record.delete()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"删除文件 {file_id} 失败: {e}")
                continue
        
        return {"message": f"成功删除 {deleted_count} 个文件"}
    except Exception as e:
        logger.error(f"批量删除文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量删除文件失败"
        )

@router.get("/stats/summary")
async def get_file_stats(
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取文件统计信息（管理员权限）"""
    try:
        stats = FileRecord.get_stats()
        return stats
    except Exception as e:
        logger.error(f"获取文件统计失败: {e}")
        # 根据安全模式决定行为：关闭则抛错，开启则返回空统计兜底
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return {
            "total_files": 0,
            "total_size": 0,
            "files_by_type": {},
            "files_by_category": {},
            "upload_trend_7d": [],
            "top_uploaders": [],
            "storage_by_user": [],
            "processing_status": {}
        }
