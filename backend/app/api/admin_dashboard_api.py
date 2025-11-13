"""
管理员仪表板API
提供系统概览、用户统计、文件统计、知识库统计等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging
import json
import os
import psutil
from pathlib import Path
from app.core.config import settings

# 导入数据库模型
from database.admin_models import UserRole, FileRecord, FileType, ProcessingStatus, AdminUser
from database.config import get_db_connection
from app.api.admin_user_api import require_admin

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/admin/dashboard", tags=["管理员仪表板"])

# Pydantic 模型定义
class SystemOverview(BaseModel):
    """系统概览模型"""
    total_users: int
    active_users: int
    new_users_today: int
    total_files: int
    total_file_size: int  # 字节
    total_documents: int
    active_documents: int
    system_uptime: str
    last_backup_time: Optional[datetime]
    storage_usage_percent: float

class UserStatistics(BaseModel):
    """用户统计模型"""
    total_users: int
    verified_users: int
    unverified_users: int
    active_users_7d: int
    active_users_30d: int
    new_registrations_7d: int
    new_registrations_30d: int
    user_growth_trend: List[Dict[str, Any]]  # 用户增长趋势
    top_active_users: List[Dict[str, Any]]   # 最活跃用户

class FileStatistics(BaseModel):
    """文件统计模型"""
    total_files: int
    total_size: int
    files_by_type: Dict[str, int]
    files_by_category: Dict[str, int]
    upload_trend_7d: List[Dict[str, Any]]
    top_uploaders: List[Dict[str, Any]]
    storage_by_user: List[Dict[str, Any]]
    processing_status: Dict[str, int]

class DocumentStatistics(BaseModel):
    """文档统计模型"""
    total_documents: int
    active_documents: int
    vectorized_documents: int
    documents_by_category: Dict[str, int]
    documents_by_source: Dict[str, int]
    recent_additions: int
    search_frequency: Dict[str, int]
    top_accessed_documents: List[Dict[str, Any]]

class SystemHealth(BaseModel):
    """系统健康状态模型"""
    database_status: str
    storage_status: str
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    active_connections: int
    error_rate_24h: float
    response_time_avg: float

class ActivityLog(BaseModel):
    """活动日志模型"""
    id: int
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime

class DashboardData(BaseModel):
    """仪表板完整数据模型"""
    system_overview: SystemOverview
    user_statistics: UserStatistics
    file_statistics: FileStatistics
    document_statistics: DocumentStatistics
    system_health: SystemHealth
    recent_activities: List[ActivityLog]

# 兜底数据构造函数：当统计计算失败时返回结构完整的空数据
def _default_system_overview() -> SystemOverview:
    """构造系统概览的空数据兜底，确保前端可以安全渲染。"""
    return SystemOverview(
        total_users=0,
        active_users=0,
        new_users_today=0,
        total_files=0,
        total_file_size=0,
        total_documents=0,
        active_documents=0,
        system_uptime="未知",
        last_backup_time=None,
        storage_usage_percent=0.0,
    )


def _default_user_statistics() -> UserStatistics:
    """构造用户统计的空数据兜底。"""
    return UserStatistics(
        total_users=0,
        verified_users=0,
        unverified_users=0,
        active_users_7d=0,
        active_users_30d=0,
        new_registrations_7d=0,
        new_registrations_30d=0,
        user_growth_trend=[],
        top_active_users=[],
    )


def _default_file_statistics() -> FileStatistics:
    """构造文件统计的空数据兜底。"""
    return FileStatistics(
        total_files=0,
        total_size=0,
        files_by_type={},
        files_by_category={},
        upload_trend_7d=[],
        top_uploaders=[],
        storage_by_user=[],
        processing_status={},
    )


def _default_document_statistics() -> DocumentStatistics:
    """构造文档统计的空数据兜底。"""
    return DocumentStatistics(
        total_documents=0,
        active_documents=0,
        vectorized_documents=0,
        documents_by_category={},
        documents_by_source={},
        recent_additions=0,
        search_frequency={},
        top_accessed_documents=[],
    )

# 数据库操作函数
def get_system_overview() -> SystemOverview:
    """获取系统概览数据"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            active_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= date_trunc('day', now()) AND created_at < date_trunc('day', now()) + interval '1 day'")
            new_users_today = cur.fetchone()[0]
            try:
                cur.execute("SELECT COUNT(*), COALESCE(SUM(file_size), 0) FROM file_records")
                file_row = cur.fetchone()
                total_files = file_row[0]
                total_file_size = file_row[1]
            except Exception:
                total_files = 0
                total_file_size = 0
        system_uptime = "未知"
        last_backup_time = None
        storage_usage_percent = 0.0
        return SystemOverview(
            total_users=total_users,
            active_users=active_users,
            new_users_today=new_users_today,
            total_files=total_files,
            total_file_size=total_file_size,
            total_documents=0,
            active_documents=0,
            system_uptime=system_uptime,
            last_backup_time=last_backup_time,
            storage_usage_percent=storage_usage_percent
        )
        
    except Exception as e:
        logger.error(f"获取系统概览数据失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return _default_system_overview()

def get_user_statistics() -> UserStatistics:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE is_verified = TRUE")
            verified_users = cur.fetchone()[0]
            unverified_users = max(0, total_users - verified_users)
            active_users_7d = max(0, int(total_users * 0.3))
            active_users_30d = max(0, int(total_users * 0.6))
            cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= now() - interval '7 days'")
            new_registrations_7d = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE created_at >= now() - interval '30 days'")
            new_registrations_30d = cur.fetchone()[0]
            user_growth_trend = []
            for i in range(7):
                cur.execute("SELECT COUNT(*) FROM users WHERE created_at::date = (now()::date - interval '%s day')", (6 - i,))
                count = cur.fetchone()[0]
                date = (datetime.now().date() - timedelta(days=6 - i)).isoformat()
                user_growth_trend.append({"date": date, "count": count})
            cur.execute("SELECT id, username, email, last_login FROM users ORDER BY last_login DESC NULLS LAST LIMIT 10")
            rows = cur.fetchall()
            top_active_users = []
            for r in rows:
                top_active_users.append({
                    "user_id": r[0],
                    "username": r[1],
                    "email": r[2],
                    "last_login": r[3].isoformat() if r[3] else None,
                    "login_count": 0
                })
        return UserStatistics(
            total_users=total_users,
            verified_users=verified_users,
            unverified_users=unverified_users,
            active_users_7d=active_users_7d,
            active_users_30d=active_users_30d,
            new_registrations_7d=new_registrations_7d,
            new_registrations_30d=new_registrations_30d,
            user_growth_trend=user_growth_trend,
            top_active_users=top_active_users
        )
    except Exception as e:
        logger.error(f"获取用户统计数据失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return _default_user_statistics()

def get_file_statistics() -> FileStatistics:
    """获取文件统计数据"""
    try:
        # 基础文件统计
        total_files = FileRecord.count(is_deleted=False)
        total_size = FileRecord.get_total_size() or 0
        
        # 按文件类型统计
        files_by_type = {}
        for file_type in FileType:
            count = FileRecord.count(file_type=file_type, is_deleted=False)
            if count > 0:
                files_by_type[file_type.value] = count
        
        # 按处理状态统计
        processing_status = {}
        for status in ProcessingStatus:
            count = FileRecord.count(processing_status=status, is_deleted=False)
            if count > 0:
                processing_status[status.value] = count
        
        # 上传趋势（最近7天）
        upload_trend_7d = []
        for i in range(7):
            date = datetime.now().date() - timedelta(days=6-i)
            count = FileRecord.count_by_date_range(
                start_date=date,
                end_date=date + timedelta(days=1),
                is_deleted=False
            )
            upload_trend_7d.append({
                "date": date.isoformat(),
                "count": count
            })
        
        # 模拟数据
        files_by_category = {
            "学习资料": int(total_files * 0.4),
            "课程文档": int(total_files * 0.3),
            "参考资料": int(total_files * 0.2),
            "其他": int(total_files * 0.1)
        }
        
        top_uploaders = [
            {"user_id": 1, "username": "admin", "file_count": int(total_files * 0.3)},
            {"user_id": 2, "username": "teacher1", "file_count": int(total_files * 0.2)},
            {"user_id": 3, "username": "teacher2", "file_count": int(total_files * 0.15)}
        ]
        
        storage_by_user = [
            {"user_id": 1, "username": "admin", "storage_used": int(total_size * 0.4)},
            {"user_id": 2, "username": "teacher1", "storage_used": int(total_size * 0.3)},
            {"user_id": 3, "username": "teacher2", "storage_used": int(total_size * 0.2)}
        ]
        
        return FileStatistics(
            total_files=total_files,
            total_size=total_size,
            files_by_type=files_by_type,
            files_by_category=files_by_category,
            upload_trend_7d=upload_trend_7d,
            top_uploaders=top_uploaders,
            storage_by_user=storage_by_user,
            processing_status=processing_status
        )
        
    except Exception as e:
        logger.error(f"获取文件统计数据失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return _default_file_statistics()

def get_document_statistics() -> DocumentStatistics:
    """获取文档统计数据"""
    try:
        # 基础文档统计
        total_documents = Document.count(is_deleted=False)
        active_documents = Document.count(is_deleted=False, is_active=True)
        
        # 向量化文档数量（假设有向量的文档都是向量化的）
        vectorized_documents = DocumentChunk.count_distinct_documents()
        
        # 最近添加的文档数量（最近7天）
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_additions = Document.count_by_date_range(
            start_date=seven_days_ago.date(),
            end_date=datetime.now().date(),
            is_deleted=False
        )
        
        # 模拟数据
        documents_by_category = {
            "技术文档": int(total_documents * 0.4),
            "学术论文": int(total_documents * 0.3),
            "教学资料": int(total_documents * 0.2),
            "其他": int(total_documents * 0.1)
        }
        
        documents_by_source = {
            "用户上传": int(total_documents * 0.6),
            "系统导入": int(total_documents * 0.3),
            "API接口": int(total_documents * 0.1)
        }
        
        search_frequency = {
            "技术问题": 150,
            "学习资料": 120,
            "课程内容": 100,
            "项目文档": 80,
            "其他": 50
        }
        
        top_accessed_documents = [
            {"document_id": 1, "title": "Python编程指南", "access_count": 250},
            {"document_id": 2, "title": "数据结构与算法", "access_count": 200},
            {"document_id": 3, "title": "Web开发基础", "access_count": 180}
        ]
        
        return DocumentStatistics(
            total_documents=total_documents,
            active_documents=active_documents,
            vectorized_documents=vectorized_documents,
            documents_by_category=documents_by_category,
            documents_by_source=documents_by_source,
            recent_additions=recent_additions,
            search_frequency=search_frequency,
            top_accessed_documents=top_accessed_documents
        )
        
    except Exception as e:
        logger.error(f"获取文档统计数据失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return _default_document_statistics()

def get_system_health() -> SystemHealth:
    """获取系统健康状态"""
    try:
        # 数据库状态检查
        database_status = "正常"
        try:
            conn = get_db_connection()
            conn.close()
        except Exception:
            database_status = "异常"
        
        # 系统资源使用情况
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        disk_usage = psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        
        # 存储状态
        storage_status = "正常" if disk_usage < 90 else "警告"
        
        # 模拟数据
        active_connections = 25
        error_rate_24h = 0.5  # 0.5%
        response_time_avg = 120.5  # 毫秒
        
        return SystemHealth(
            database_status=database_status,
            storage_status=storage_status,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            disk_usage=disk_usage,
            active_connections=active_connections,
            error_rate_24h=error_rate_24h,
            response_time_avg=response_time_avg
        )
        
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        # 返回默认值而不是抛出异常（安全模式）
        return SystemHealth(
            database_status="未知",
            storage_status="未知",
            memory_usage=0.0,
            cpu_usage=0.0,
            disk_usage=0.0,
            active_connections=0,
            error_rate_24h=0.0,
            response_time_avg=0.0
        )

def get_recent_activities(limit: int = 20) -> List[ActivityLog]:
    """获取最近活动日志"""
    try:
        # 由于没有活动日志表，返回模拟数据
        activities = []
        for i in range(min(limit, 10)):
            activities.append(ActivityLog(
                id=i + 1,
                user_id=1,
                action="登录系统",
                resource_type="用户",
                resource_id=1,
                details={"ip": "192.168.1.100", "browser": "Chrome"},
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                timestamp=datetime.now() - timedelta(minutes=i * 10)
            ))
        
        return activities
        
    except Exception as e:
        logger.error(f"获取活动日志失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        return []

# API 端点
@router.get("/overview", response_model=SystemOverview, summary="获取系统概览")
async def get_dashboard_overview(current_user: AdminUser = Depends(require_admin)):
    """获取系统概览数据"""
    return get_system_overview()

@router.get("/users", response_model=UserStatistics, summary="获取用户统计")
async def get_dashboard_users(current_user: AdminUser = Depends(require_admin)):
    """获取用户统计数据"""
    return get_user_statistics()

@router.get("/files", response_model=FileStatistics, summary="获取文件统计")
async def get_dashboard_files(current_user: AdminUser = Depends(require_admin)):
    """获取文件统计数据"""
    return get_file_statistics()

@router.get("/documents", response_model=DocumentStatistics, summary="获取文档统计")
async def get_dashboard_documents(current_user: AdminUser = Depends(require_admin)):
    """获取文档统计数据"""
    return get_document_statistics()

@router.get("/health", response_model=SystemHealth, summary="获取系统健康状态")
async def get_dashboard_health(current_user: AdminUser = Depends(require_admin)):
    """获取系统健康状态"""
    return get_system_health()

@router.get("/activities", response_model=List[ActivityLog], summary="获取活动日志")
async def get_dashboard_activities(
    limit: int = Query(20, ge=1, le=100, description="返回记录数量"),
    current_user: AdminUser = Depends(require_admin)
):
    """获取最近活动日志"""
    return get_recent_activities(limit)

@router.get("/", response_model=DashboardData, summary="获取完整仪表板数据")
async def get_dashboard_data(current_user: AdminUser = Depends(require_admin)):
    """获取完整的仪表板数据：任一子项失败时使用兜底数据并返回200。"""
    try:
        overview = get_system_overview()
    except Exception as e:
        logger.error(f"仪表盘-系统总览聚合失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        overview = _default_system_overview()

    try:
        user_stats = get_user_statistics()
    except Exception as e:
        logger.error(f"仪表盘-用户统计聚合失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        user_stats = _default_user_statistics()

    try:
        file_stats = get_file_statistics()
    except Exception as e:
        logger.error(f"仪表盘-文件统计聚合失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        file_stats = _default_file_statistics()

    try:
        doc_stats = get_document_statistics()
    except Exception as e:
        logger.error(f"仪表盘-文档统计聚合失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        doc_stats = _default_document_statistics()

    try:
        health = get_system_health()
    except Exception as e:
        logger.error(f"仪表盘-系统健康聚合失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        health = SystemHealth(
            database_status="未知",
            storage_status="未知",
            memory_usage=0.0,
            cpu_usage=0.0,
            disk_usage=0.0,
            active_connections=0,
            error_rate_24h=0.0,
            response_time_avg=0.0,
        )

    try:
        activities = get_recent_activities(10)
    except Exception as e:
        logger.error(f"仪表盘-活动日志聚合失败: {e}")
        if not settings.ADMIN_API_SAFE_MODE:
            raise
        activities = []

    return DashboardData(
        system_overview=overview,
        user_statistics=user_stats,
        file_statistics=file_stats,
        document_statistics=doc_stats,
        system_health=health,
        recent_activities=activities,
    )
