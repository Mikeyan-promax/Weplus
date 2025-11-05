"""
WePlus 后台管理系统 - 日志管理API
提供日志查询、统计、导出、清理等功能
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import json
import csv
import io
from enum import Enum

# 导入日志服务和认证
from app.services.logging_service import logging_service, LogLevel, LogCategory
from app.api.admin_user_api import require_admin, get_current_user

# 创建路由器
router = APIRouter(prefix="/api/admin/logs", tags=["日志管理"])

# Pydantic模型定义
class LogQuery(BaseModel):
    """日志查询模型"""
    table: str = Field("system_logs", description="日志表名")
    limit: int = Field(100, ge=1, le=1000, description="返回记录数量")
    offset: int = Field(0, ge=0, description="偏移量")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    level: Optional[LogLevel] = Field(None, description="日志级别")
    category: Optional[LogCategory] = Field(None, description="日志分类")
    user_id: Optional[int] = Field(None, description="用户ID")
    keyword: Optional[str] = Field(None, description="关键词搜索")

class LogStatisticsQuery(BaseModel):
    """日志统计查询模型"""
    days: int = Field(7, ge=1, le=365, description="统计天数")
    group_by: str = Field("day", pattern="^(hour|day|week|month)$", description="分组方式")

class LogExportQuery(BaseModel):
    """日志导出查询模型"""
    table: str = Field("system_logs", description="日志表名")
    format: str = Field("json", pattern="^(json|csv|txt)$", description="导出格式")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    level: Optional[LogLevel] = Field(None, description="日志级别")
    category: Optional[LogCategory] = Field(None, description="日志分类")
    user_id: Optional[int] = Field(None, description="用户ID")

class LogCleanupConfig(BaseModel):
    """日志清理配置模型"""
    days_to_keep: int = Field(90, ge=1, le=3650, description="保留天数")
    tables: List[str] = Field(
        ["system_logs", "user_action_logs", "security_logs", "api_access_logs"],
        description="要清理的表"
    )

# API端点
@router.get("/query")
async def query_logs(
    table: str = Query("system_logs", description="日志表名"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD HH:MM:SS)"),
    level: Optional[LogLevel] = Query(None, description="日志级别"),
    category: Optional[LogCategory] = Query(None, description="日志分类"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """查询日志记录"""
    try:
        # 构建过滤条件
        filters = {}
        
        if start_date:
            try:
                filters["start_date"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="开始日期格式错误"
                )
        
        if end_date:
            try:
                filters["end_date"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="结束日期格式错误"
                )
        
        if level:
            filters["level"] = level.value
        
        if category:
            filters["category"] = category.value
        
        if user_id:
            filters["user_id"] = user_id
        
        # 验证表名
        valid_tables = ["system_logs", "user_action_logs", "security_logs", "api_access_logs"]
        if table not in valid_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的表名，支持的表: {', '.join(valid_tables)}"
            )
        
        # 查询日志
        logs = logging_service.get_logs(
            table=table,
            limit=limit,
            offset=offset,
            filters=filters
        )
        
        # 关键词过滤（如果提供）
        if keyword:
            keyword_lower = keyword.lower()
            logs = [
                log for log in logs
                if keyword_lower in str(log.get('message', '')).lower() or
                   keyword_lower in str(log.get('details', '')).lower()
            ]
        
        # 记录管理员操作
        logging_service.log_user_action(
            user_id=admin_user['user_id'],
            action="查询日志",
            resource_type="logs",
            new_values={
                "table": table,
                "filters": filters,
                "limit": limit,
                "offset": offset
            },
            success=True
        )
        
        return {
            "logs": logs,
            "total": len(logs),
            "table": table,
            "filters": filters
        }
        
    except Exception as e:
        logging_service.log_system_event(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN_ACTION,
            message=f"查询日志失败: {e}",
            user_id=admin_user['user_id'],
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询日志失败"
        )

@router.get("/statistics")
async def get_log_statistics(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取日志统计信息"""
    try:
        statistics = logging_service.get_log_statistics(days=days)
        
        # 记录管理员操作
        logging_service.log_user_action(
            user_id=admin_user['user_id'],
            action="查看日志统计",
            resource_type="logs",
            new_values={"days": days},
            success=True
        )
        
        return statistics
        
    except Exception as e:
        logging_service.log_system_event(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN_ACTION,
            message=f"获取日志统计失败: {e}",
            user_id=admin_user['user_id'],
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取日志统计失败"
        )

@router.get("/export")
async def export_logs(
    table: str = Query("system_logs", description="日志表名"),
    format: str = Query("json", pattern="^(json|csv|txt)$", description="导出格式"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    level: Optional[LogLevel] = Query(None, description="日志级别"),
    category: Optional[LogCategory] = Query(None, description="日志分类"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """导出日志数据"""
    try:
        # 构建过滤条件
        filters = {}
        
        if start_date:
            filters["start_date"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if end_date:
            filters["end_date"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if level:
            filters["level"] = level.value
        
        if category:
            filters["category"] = category.value
        
        if user_id:
            filters["user_id"] = user_id
        
        # 验证表名
        valid_tables = ["system_logs", "user_action_logs", "security_logs", "api_access_logs"]
        if table not in valid_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的表名，支持的表: {', '.join(valid_tables)}"
            )
        
        # 查询日志（导出时不限制数量，但设置合理上限）
        logs = logging_service.get_logs(
            table=table,
            limit=10000,  # 导出上限
            offset=0,
            filters=filters
        )
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = f"{table}_{timestamp}.{format}"
        
        # 根据格式导出
        if format == "json":
            from fastapi.responses import JSONResponse
            
            content = {
                "table": table,
                "export_time": datetime.now().isoformat(),
                "filters": filters,
                "total_records": len(logs),
                "logs": logs
            }
            
            return JSONResponse(
                content=content,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        elif format == "csv":
            from fastapi.responses import Response
            
            if not logs:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="没有找到符合条件的日志记录"
                )
            
            # 创建CSV内容
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            
            for log in logs:
                # 处理复杂字段
                row = {}
                for key, value in log.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[key] = value
                writer.writerow(row)
            
            return Response(
                content=output.getvalue(),
                media_type="VARCHAR/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        elif format == "txt":
            from fastapi.responses import Response
            
            # 创建文本内容
            lines = []
            lines.append(f"日志导出报告")
            lines.append(f"表名: {table}")
            lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"过滤条件: {json.dumps(filters, ensure_ascii=False, default=str)}")
            lines.append(f"记录总数: {len(logs)}")
            lines.append("=" * 80)
            lines.append("")
            
            for i, log in enumerate(logs, 1):
                lines.append(f"记录 #{i}")
                lines.append("-" * 40)
                for key, value in log.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False, indent=2)
                    lines.append(f"{key}: {value}")
                lines.append("")
            
            content = "\n".join(lines)
            
            return Response(
                content=content,
                media_type="VARCHAR/plain",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        # 记录管理员操作
        logging_service.log_user_action(
            user_id=admin_user['user_id'],
            action="导出日志",
            resource_type="logs",
            new_values={
                "table": table,
                "format": format,
                "filters": filters,
                "record_count": len(logs)
            },
            success=True
        )
        
    except Exception as e:
        logging_service.log_system_event(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN_ACTION,
            message=f"导出日志失败: {e}",
            user_id=admin_user['user_id'],
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出日志失败"
        )

@router.post("/cleanup")
async def cleanup_logs(
    config: LogCleanupConfig,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """清理旧日志记录"""
    try:
        # 验证管理员权限（只有超级管理员可以清理日志）
        if admin_user.get('role') != 'super_admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有超级管理员可以清理日志"
            )
        
        # 执行清理
        logging_service.cleanup_old_logs(days_to_keep=config.days_to_keep)
        
        # 记录管理员操作
        logging_service.log_user_action(
            user_id=admin_user['user_id'],
            action="清理日志",
            resource_type="logs",
            new_values={
                "days_to_keep": config.days_to_keep,
                "tables": config.tables
            },
            success=True
        )
        
        return {
            "message": "日志清理完成",
            "days_to_keep": config.days_to_keep,
            "tables": config.tables
        }
        
    except Exception as e:
        logging_service.log_system_event(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN_ACTION,
            message=f"清理日志失败: {e}",
            user_id=admin_user['user_id'],
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理日志失败"
        )

@router.get("/tables")
async def get_log_tables(
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """获取可用的日志表信息"""
    try:
        tables_info = {
            "system_logs": {
                "name": "系统日志",
                "description": "系统事件、错误和操作记录",
                "fields": ["id", "level", "category", "message", "details", "user_id", "timestamp"]
            },
            "user_action_logs": {
                "name": "用户操作日志",
                "description": "用户在系统中的操作记录",
                "fields": ["id", "user_id", "action", "resource_type", "resource_id", "success", "timestamp"]
            },
            "security_logs": {
                "name": "安全日志",
                "description": "安全相关事件记录",
                "fields": ["id", "event_type", "user_id", "ip_address", "risk_level", "blocked", "timestamp"]
            },
            "api_access_logs": {
                "name": "API访问日志",
                "description": "API接口访问记录",
                "fields": ["id", "method", "endpoint", "user_id", "response_status", "response_time", "timestamp"]
            }
        }
        
        return {
            "tables": tables_info,
            "total_tables": len(tables_info)
        }
        
    except Exception as e:
        logging_service.log_system_event(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN_ACTION,
            message=f"获取日志表信息失败: {e}",
            user_id=admin_user['user_id'],
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取日志表信息失败"
        )

@router.post("/test")
async def test_logging(
    request: Request,
    level: LogLevel = Query(LogLevel.INFO, description="测试日志级别"),
    category: LogCategory = Query(LogCategory.SYSTEM_ERROR, description="测试日志分类"),
    message: str = Query("测试日志消息", description="测试消息内容"),
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """测试日志记录功能"""
    try:
        # 记录测试日志
        logging_service.log_system_event(
            level=level,
            category=category,
            message=message,
            details={
                "test": True,
                "admin_user": admin_user['username'],
                "timestamp": datetime.now().isoformat()
            },
            user_id=admin_user['user_id'],
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent')
        )
        
        # 记录用户操作
        logging_service.log_user_action(
            user_id=admin_user['user_id'],
            action="测试日志功能",
            resource_type="logs",
            new_values={
                "level": level.value,
                "category": category.value,
                "message": message
            },
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent'),
            success=True
        )
        
        return {
            "message": "测试日志记录成功",
            "level": level.value,
            "category": category.value,
            "test_message": message
        }
        
    except Exception as e:
        logging_service.log_system_event(
            level=LogLevel.ERROR,
            category=LogCategory.ADMIN_ACTION,
            message=f"测试日志功能失败: {e}",
            user_id=admin_user['user_id'],
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试日志功能失败"
        )