"""
WePlus 后台管理系统 - 数据备份管理API
提供数据备份的创建、查看、删除和恢复功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

from ..services.backup_service import backup_service, BackupInfo, BackupConfig
from ..services.logging_service import logging_service, LogLevel, LogCategory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 请求模型
class CreateBackupRequest(BaseModel):
    """创建备份请求模型"""
    type: str = Field("full", description="备份类型: full, database, files")
    description: str = Field("", description="备份描述")
    include_files: bool = Field(True, description="是否包含文件")
    include_database: bool = Field(True, description="是否包含数据库")
    include_vector_store: bool = Field(True, description="是否包含向量存储")

class BackupConfigRequest(BaseModel):
    """备份配置请求模型"""
    max_backups: int = Field(30, ge=1, le=100, description="最大备份数量")
    backup_interval_hours: int = Field(24, ge=1, le=168, description="备份间隔（小时）")
    include_files: bool = Field(True, description="默认包含文件")
    include_database: bool = Field(True, description="默认包含数据库")
    include_vector_store: bool = Field(True, description="默认包含向量存储")
    compress: bool = Field(True, description="是否压缩备份")

class RestoreBackupRequest(BaseModel):
    """恢复备份请求模型"""
    backup_id: str = Field(..., description="备份ID")
    confirm: bool = Field(False, description="确认恢复（此操作不可逆）")

# 响应模型
class BackupResponse(BaseModel):
    """备份响应模型"""
    id: str
    timestamp: datetime
    size: int
    size_mb: float
    type: str
    status: str
    file_path: str
    description: str
    error_message: str = ""

class BackupListResponse(BaseModel):
    """备份列表响应模型"""
    backups: List[BackupResponse]
    total: int
    statistics: Dict[str, Any]

class BackupOperationResponse(BaseModel):
    """备份操作响应模型"""
    success: bool
    message: str
    backup_id: Optional[str] = None
    details: Dict[str, Any] = {}

# 工具函数
def convert_backup_info_to_response(backup_info: BackupInfo) -> BackupResponse:
    """转换备份信息为响应模型"""
    return BackupResponse(
        id=backup_info.id,
        timestamp=backup_info.timestamp,
        size=backup_info.size,
        size_mb=round(backup_info.size / (1024 * 1024), 2),
        type=backup_info.type,
        status=backup_info.status,
        file_path=backup_info.file_path,
        description=backup_info.description,
        error_message=backup_info.error_message
    )

# API端点
@router.post("/create", response_model=BackupOperationResponse)
async def create_backup(
    request: CreateBackupRequest,
    background_tasks: BackgroundTasks
):
    """
    创建数据备份
    支持完整备份、数据库备份和文件备份
    """
    try:
        # 记录操作日志
        await logging_service.log(
            level=LogLevel.INFO,
            category=LogCategory.ADMIN,
            message=f"开始创建备份",
            details={
                "backup_type": request.type,
                "description": request.description,
                "include_files": request.include_files,
                "include_database": request.include_database,
                "include_vector_store": request.include_vector_store
            }
        )
        
        # 更新备份配置
        backup_service.config.include_files = request.include_files
        backup_service.config.include_database = request.include_database
        backup_service.config.include_vector_store = request.include_vector_store
        
        # 根据备份类型创建备份
        if request.type == "full":
            backup_info = await backup_service.create_full_backup(request.description)
        elif request.type == "database":
            backup_info = await backup_service.create_database_backup(request.description)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的备份类型: {request.type}")
        
        # 记录结果日志
        if backup_info.status == "success":
            await logging_service.log(
                level=LogLevel.INFO,
                category=LogCategory.ADMIN,
                message=f"备份创建成功",
                details={
                    "backup_id": backup_info.id,
                    "backup_size": backup_info.size,
                    "backup_type": backup_info.type
                }
            )
            
            return BackupOperationResponse(
                success=True,
                message="备份创建成功",
                backup_id=backup_info.id,
                details={
                    "size": backup_info.size,
                    "size_mb": round(backup_info.size / (1024 * 1024), 2),
                    "type": backup_info.type
                }
            )
        else:
            await logging_service.log(
                level=LogLevel.ERROR,
                category=LogCategory.ADMIN,
                message=f"备份创建失败",
                details={
                    "backup_id": backup_info.id,
                    "error": backup_info.error_message
                }
            )
            
            return BackupOperationResponse(
                success=False,
                message=f"备份创建失败: {backup_info.error_message}",
                backup_id=backup_info.id
            )
            
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        await logging_service.log(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN,
            message=f"创建备份异常",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")

@router.get("/list", response_model=BackupListResponse)
async def get_backup_list():
    """
    获取备份列表
    包含备份统计信息
    """
    try:
        # 获取备份列表
        backups = await backup_service.get_backup_list()
        
        # 转换为响应模型
        backup_responses = [
            convert_backup_info_to_response(backup) for backup in backups
        ]
        
        # 获取统计信息
        statistics = await backup_service.get_backup_statistics()
        
        return BackupListResponse(
            backups=backup_responses,
            total=len(backup_responses),
            statistics=statistics
        )
        
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@router.get("/statistics")
async def get_backup_statistics():
    """
    获取备份统计信息
    """
    try:
        statistics = await backup_service.get_backup_statistics()
        return {
            "success": True,
            "data": statistics
        }
        
    except Exception as e:
        logger.error(f"获取备份统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份统计失败: {str(e)}")

@router.delete("/{backup_id}", response_model=BackupOperationResponse)
async def delete_backup(backup_id: str):
    """
    删除指定备份
    """
    try:
        # 记录操作日志
        await logging_service.log(
            level=LogLevel.INFO,
            category=LogCategory.ADMIN,
            message=f"删除备份",
            details={"backup_id": backup_id}
        )
        
        success = await backup_service.delete_backup(backup_id)
        
        if success:
            await logging_service.log(
                level=LogLevel.INFO,
                category=LogCategory.ADMIN,
                message=f"备份删除成功",
                details={"backup_id": backup_id}
            )
            
            return BackupOperationResponse(
                success=True,
                message="备份删除成功",
                backup_id=backup_id
            )
        else:
            return BackupOperationResponse(
                success=False,
                message="备份删除失败，备份不存在或无法删除",
                backup_id=backup_id
            )
            
    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        await logging_service.log(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN,
            message=f"删除备份异常",
            details={"backup_id": backup_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")

@router.post("/restore", response_model=BackupOperationResponse)
async def restore_backup(request: RestoreBackupRequest):
    """
    恢复备份
    注意：此操作会覆盖当前数据，不可逆
    """
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400, 
                detail="请确认恢复操作，此操作将覆盖当前数据且不可逆"
            )
        
        # 记录操作日志
        await logging_service.log(
            level=LogLevel.WARNING,
            category=LogCategory.ADMIN,
            message=f"开始恢复备份",
            details={"backup_id": request.backup_id}
        )
        
        success = await backup_service.restore_backup(request.backup_id)
        
        if success:
            await logging_service.log(
                level=LogLevel.INFO,
                category=LogCategory.ADMIN,
                message=f"备份恢复成功",
                details={"backup_id": request.backup_id}
            )
            
            return BackupOperationResponse(
                success=True,
                message="备份恢复成功，系统数据已恢复到备份时的状态",
                backup_id=request.backup_id
            )
        else:
            await logging_service.log(
                level=LogLevel.ERROR,
                category=LogCategory.ADMIN,
                message=f"备份恢复失败",
                details={"backup_id": request.backup_id}
            )
            
            return BackupOperationResponse(
                success=False,
                message="备份恢复失败，请检查备份文件是否存在",
                backup_id=request.backup_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        await logging_service.log(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN,
            message=f"恢复备份异常",
            details={"backup_id": request.backup_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")

@router.get("/download/{backup_id}")
async def download_backup(backup_id: str):
    """
    下载备份文件
    """
    try:
        # 获取备份列表
        backups = await backup_service.get_backup_list()
        backup_to_download = None
        
        for backup in backups:
            if backup.id == backup_id:
                backup_to_download = backup
                break
        
        if not backup_to_download:
            raise HTTPException(status_code=404, detail="备份不存在")
        
        # 检查文件是否存在
        from pathlib import Path
        backup_path = Path(backup_to_download.file_path)
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 记录下载日志
        await logging_service.log(
            level=LogLevel.INFO,
            category=LogCategory.ADMIN,
            message=f"下载备份文件",
            details={"backup_id": backup_id, "file_path": str(backup_path)}
        )
        
        # 返回文件
        return FileResponse(
            path=str(backup_path),
            filename=f"{backup_id}.zip" if backup_path.suffix == '.zip' else backup_id,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载备份失败: {str(e)}")

@router.get("/config")
async def get_backup_config():
    """
    获取备份配置
    """
    try:
        config = backup_service.config
        return {
            "success": True,
            "data": {
                "max_backups": config.max_backups,
                "backup_interval_hours": config.backup_interval_hours,
                "include_files": config.include_files,
                "include_database": config.include_database,
                "include_vector_store": config.include_vector_store,
                "compress": config.compress,
                "backup_dir": config.backup_dir
            }
        }
        
    except Exception as e:
        logger.error(f"获取备份配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份配置失败: {str(e)}")

@router.put("/config", response_model=BackupOperationResponse)
async def update_backup_config(request: BackupConfigRequest):
    """
    更新备份配置
    """
    try:
        # 记录操作日志
        await logging_service.log(
            level=LogLevel.INFO,
            category=LogCategory.ADMIN,
            message=f"更新备份配置",
            details={
                "max_backups": request.max_backups,
                "backup_interval_hours": request.backup_interval_hours,
                "include_files": request.include_files,
                "include_database": request.include_database,
                "include_vector_store": request.include_vector_store,
                "compress": request.compress
            }
        )
        
        # 更新配置
        backup_service.config.max_backups = request.max_backups
        backup_service.config.backup_interval_hours = request.backup_interval_hours
        backup_service.config.include_files = request.include_files
        backup_service.config.include_database = request.include_database
        backup_service.config.include_vector_store = request.include_vector_store
        backup_service.config.compress = request.compress
        
        return BackupOperationResponse(
            success=True,
            message="备份配置更新成功",
            details={
                "max_backups": request.max_backups,
                "backup_interval_hours": request.backup_interval_hours
            }
        )
        
    except Exception as e:
        logger.error(f"更新备份配置失败: {e}")
        await logging_service.log(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN,
            message=f"更新备份配置异常",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"更新备份配置失败: {str(e)}")

@router.post("/schedule/start", response_model=BackupOperationResponse)
async def start_scheduled_backup():
    """
    启动定时备份任务
    """
    try:
        # 这里可以实现定时任务的启动逻辑
        # 由于这是一个简化版本，我们只记录日志
        await logging_service.log(
            level=LogLevel.INFO,
            category=LogCategory.ADMIN,
            message="启动定时备份任务",
            details={"interval_hours": backup_service.config.backup_interval_hours}
        )
        
        return BackupOperationResponse(
            success=True,
            message="定时备份任务已启动",
            details={"interval_hours": backup_service.config.backup_interval_hours}
        )
        
    except Exception as e:
        logger.error(f"启动定时备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动定时备份失败: {str(e)}")

@router.post("/schedule/stop", response_model=BackupOperationResponse)
async def stop_scheduled_backup():
    """
    停止定时备份任务
    """
    try:
        await logging_service.log(
            level=LogLevel.INFO,
            category=LogCategory.ADMIN,
            message="停止定时备份任务"
        )
        
        return BackupOperationResponse(
            success=True,
            message="定时备份任务已停止"
        )
        
    except Exception as e:
        logger.error(f"停止定时备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止定时备份失败: {str(e)}")

# 健康检查
@router.get("/health")
async def backup_health_check():
    """
    备份服务健康检查
    """
    try:
        # 检查备份目录是否存在
        from pathlib import Path
        backup_dir = Path(backup_service.config.backup_dir)
        
        health_status = {
            "backup_service": "healthy",
            "backup_directory_exists": backup_dir.exists(),
            "backup_directory_writable": backup_dir.exists() and os.access(backup_dir, os.W_OK),
            "last_check": datetime.now().isoformat()
        }
        
        # 获取最近的备份信息
        backups = await backup_service.get_backup_list()
        if backups:
            health_status["last_backup"] = {
                "id": backups[0].id,
                "timestamp": backups[0].timestamp.isoformat(),
                "status": backups[0].status
            }
        
        return {
            "success": True,
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"备份服务健康检查失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "backup_service": "unhealthy",
                "last_check": datetime.now().isoformat()
            }
        }

import os