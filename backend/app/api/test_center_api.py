"""
测试中心 API
提供系统组件健康检查与汇总信息
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.services.logging_service import logging_service
from app.services.email_service import email_service
from database.config import get_db_connection

router = APIRouter(prefix="/api/test", tags=["测试中心"])


@router.get("/summary")
def get_test_summary() -> Dict[str, Any]:
    """获取系统健康与配置汇总"""
    # 应用信息
    app_info = {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": bool(getattr(settings, "DEBUG", False))
    }

    # 数据库连通性
    db_info = {"ok": False}
    try:
        # 正确使用数据库连接的上下文管理器
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                _ = cur.fetchone()
        db_info["ok"] = True
    except Exception as e:
        db_info.update({"ok": False, "error": str(e)})

    # 日志服务自检（确保表结构与索引）
    log_info = {"ok": False}
    try:
        logging_service.ensure_log_tables()
        log_info["ok"] = True
    except Exception as e:
        log_info.update({"ok": False, "error": str(e)})

    # 邮件配置状态
    mail_info = {
        "configured": bool(email_service.mail_username and email_service.mail_password),
        "from": email_service.mail_from,
        "debug_mode": bool(getattr(email_service, "debug_mode", False))
    }

    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "app": app_info,
        "services": {
            "database": db_info,
            "logging": log_info,
            "email": mail_info
        }
    }
