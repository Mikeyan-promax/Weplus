"""
WePlus - 校园智能服务平台后端
FastAPI主应用入口（生产化增强）
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
from datetime import datetime
import logging
import os

# 核心配置与日志
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.dependencies.admin_security import require_admin_ip_whitelist
from app.middlewares.request_id_middleware import RequestIdMiddleware
from app.middlewares.rate_limit_middleware import RateLimitMiddleware

# 可选可观测性
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except Exception:
    sentry_sdk = None
    FastApiIntegration = None

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except Exception:
    Instrumentator = None

# 导入RAG路由
from app.api.rag_routes import router as rag_router
# 导入认证路由
from auth_routes import router as auth_router
# 导入文档管理路由
from app.api.document_routes import router as document_router
# 导入新的管理API
# from user_management_api import router as user_management_router  # 注释掉，避免与admin_user_api路由冲突
from document_management_api import router as document_management_router
from admin_auth_api import router as admin_auth_router
from admin_dashboard_api import router as admin_dashboard_router

# 导入新开发的后台管理API
from app.api import admin_user_api, admin_file_api, admin_rag_api, admin_dashboard_api as new_dashboard_api, admin_logs_api, user_api
from app.api.admin_backup_api import router as admin_backup_api
from app.api.vector_database_api import router as vector_database_api
from app.api.study_resources_api import router as study_resources_api
from app.api.test_center_api import router as test_center_router

# 导入日志服务
from app.services.logging_service import logging_service, LogLevel, LogCategory

# 配置JSON日志（根据配置开关）
setup_logging(enable_json=settings.ENABLE_JSON_LOGGING)
logger = logging.getLogger("weplus.main")

# 创建FastAPI应用实例
app = FastAPI(
    title="WePlus RAG Campus Assistant",
    description="基于RAG技术的校园智能助手API - 集成DeepSeek和豆包嵌入模型",
    version="2.0.0"
)

# 配置CORS：读取环境变量白名单
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求ID中间件
app.add_middleware(RequestIdMiddleware)

# IP级限流中间件
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.REQUEST_RATE_LIMIT_ENABLED,
    max_per_minute=settings.REQUEST_RATE_LIMIT_PER_MINUTE,
)

# 可选：接入Sentry（存在DSN时启用）
if settings.SENTRY_DSN and sentry_sdk and FastApiIntegration:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()])
    logger.info("Sentry 已启用")

# 可选：Prometheus指标端点
if settings.PROMETHEUS_ENABLED and Instrumentator:
    Instrumentator().instrument(app).expose(app)
    logger.info("Prometheus /metrics 已启用")

# 注册RAG路由
app.include_router(rag_router)
# 注册认证路由
app.include_router(auth_router, prefix="/api", tags=["认证"])
# 注册新的管理API
# app.include_router(user_management_router, tags=["用户管理"])  # 注释掉，避免与admin_user_api路由冲突
app.include_router(document_management_router, prefix="/api/admin", tags=["文档管理"])
app.include_router(admin_auth_router, tags=["管理员认证"])
app.include_router(admin_dashboard_router, prefix="/api", tags=["管理员仪表板"])
app.include_router(document_router)

# 注册后台管理API路由（应用IP白名单依赖）
app.include_router(
    admin_user_api.router,
    tags=["后台用户管理"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(
    admin_file_api.router,
    tags=["后台文件管理"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(
    admin_rag_api.router,
    tags=["后台RAG管理"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(
    new_dashboard_api.router,
    tags=["后台仪表板"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(
    admin_logs_api.router,
    tags=["后台日志管理"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(
    admin_backup_api,
    prefix="/api/admin/backup",
    tags=["后台备份管理"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(
    vector_database_api,
    prefix="/api/admin/vector",
    tags=["向量数据库管理"],
    dependencies=[Depends(require_admin_ip_whitelist)],
)
app.include_router(study_resources_api, tags=["学习资源管理"])
app.include_router(user_api.router, tags=["用户API"])
app.include_router(test_center_router, tags=["测试中心"])

# 添加前端需要的文档路由
@app.get("/api/documents/list")
async def get_documents_list(
    offset: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
):
    """
    获取文档列表 - 前端调用的路由
    直接查询数据库，不需要认证
    """
    try:
        logger.info(f"收到 /api/documents/list 请求: offset={offset}, limit={limit}")
        
        # 导入数据库连接
        from database.config import get_db_connection
        
        # 直接查询数据库
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            params = []
            
            if search:
                # 统一使用 metadata 字段，兼容新库
                where_conditions.append("(filename ILIKE %s OR metadata->>'title' ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if category_id:
                where_conditions.append("metadata->>'category' = %s")
                params.append(str(category_id))
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询总数
            count_query = f"SELECT COUNT(*) FROM documents{where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # 查询文档列表
            query = f"""
                SELECT id, filename, file_type, file_size, upload_time, 
                       content_hash, metadata, status, created_at, updated_at
                FROM documents
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            
            # 转换为前端期望的格式
            document_list = []
            for row in rows:
                doc_id, filename, file_type, file_size, upload_time, content_hash, metadata, status, created_at, updated_at = row
                metadata = metadata or {}
                
                document_list.append({
                    "id": doc_id,
                    "title": metadata.get('title', filename),
                    "filename": filename,
                    "file_type": file_type,
                    "file_size": file_size,
                    "upload_time": upload_time.isoformat() if upload_time else None,
                    "status": status,
                    "category": metadata.get('category', 'general'),
                    "created_at": created_at.isoformat() if created_at else None,
                    "updated_at": updated_at.isoformat() if updated_at else None,
                    "content_hash": content_hash
                })
        
        return {
            "success": True,
            "message": "获取文档列表成功",
            "data": {
                "documents": document_list,
                "total": total,
                "offset": offset,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"获取文档列表失败: {str(e)}",
            "data": {
                "documents": [],
                "total": 0,
                "offset": offset,
                "limit": limit
            }
        }

# 临时路由：解决前端404错误
@app.post("/documents/paginated")
async def documents_paginated_temp():
    """
    临时路由：解决前端404错误
    返回空的分页数据结构
    """
    logger.info("收到 /documents/paginated 请求 - 临时路由响应")
    return {
        "success": True,
        "message": "临时路由响应",
        "data": {
            "documents": [],
            "total": 0,
            "page": 1,
            "limit": 10,
            "total_pages": 0
        }
    }

@app.get("/")
async def root():
    """根路径端点"""
    return {
        "message": "WePlus RAG Campus Assistant API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "DeepSeek聊天API集成",
            "豆包嵌入模型集成", 
            "文档处理和向量化",
            "智能检索和问答",
            "多轮对话支持"
        ],
        "endpoints": {
            "chat": "/api/rag/chat",
            "document_upload": "/api/rag/documents/upload",
            "document_process": "/api/rag/documents/process",
            "health_check": "/api/rag/health",
            "system_stats": "/api/rag/stats"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """基础健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "WePlus RAG API",
        "version": "2.0.0"
    }

# 新增：标准健康与就绪端点
@app.get("/healthz")
async def healthz():
    """K8s风格健康检查（函数级注释）
    返回应用基本运行状态，用于负载均衡健康检查
    """
    return {"ok": True, "app": settings.APP_NAME, "version": settings.APP_VERSION}

@app.get("/api/healthz")
async def api_healthz():
    """健康检查端点（API前缀别名）
    Railway/Nginx 会请求 `/api/healthz`，与 `/healthz` 返回一致结构。
    """
    return {"ok": True, "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/readyz")
async def readyz():
    """K8s风格就绪检查（函数级注释）
    检查必要依赖是否就绪（此处简化，可扩展为数据库与外部服务）
    """
    # 简化：返回就绪，后续可接入数据库探测
    return {"ready": True, "dependencies": ["db", "vector", "email"], "timestamp": datetime.now().isoformat()}

# 保持向后兼容的临时端点
@app.post("/api/chat")
async def legacy_chat_endpoint(message: dict):
    """向后兼容的聊天端点，重定向到新的RAG端点"""
    logger.warning("使用了已弃用的 /api/chat 端点，请使用 /api/rag/chat")
    
    user_message = message.get("message", "")
    
    return {
        "response": f"收到您的消息：{user_message}。请使用新的RAG端点 /api/rag/chat 获得更好的体验！",
        "timestamp": datetime.now().isoformat(),
        "model": "legacy-compatibility",
        "notice": "此端点已弃用，请使用 /api/rag/chat"
    }

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"全局异常处理: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
            "request_path": str(request.url.path)
        }
    )

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 WePlus RAG Campus Assistant API 启动中...")
    logger.info("📚 RAG系统已集成 DeepSeek 和豆包嵌入模型")
    # 初始化日志服务（仅执行一次，失败不影响主流程）
    try:
        logging_service.initialize()
        logger.info("📝 日志服务初始化完成（已确保日志表存在）")
    except Exception as e:
        logger.error(f"日志服务初始化异常: {e}")

    # 启动时自检关键表，缺失时执行完整Schema
    try:
        from database.db_manager import db_manager
        # 以 admin_users 作为哨兵表检测是否已初始化
        if not db_manager.table_exists("admin_users"):
            schema_path = os.path.join(os.path.dirname(__file__), "database", "postgresql_complete_schema.sql")
            if os.path.exists(schema_path):
                ok = db_manager.create_table_from_sql(schema_path)
                if ok:
                    logger.info("📦 已执行完整数据库Schema初始化（首次启动或缺失表）")
                else:
                    logger.warning("⚠️ 尝试执行Schema失败，请检查数据库权限与脚本内容")
            else:
                logger.warning("⚠️ 未找到完整Schema文件：database/postgresql_complete_schema.sql")
        else:
            logger.info("✅ 检测到基础表已存在，跳过Schema初始化")
    except Exception as e:
        logger.error(f"启动自检与Schema初始化失败: {e}")

    logger.info("✅ 服务器启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 WePlus RAG Campus Assistant API 正在关闭...")

if __name__ == "__main__":
    print("🚀 启动WePlus RAG Campus Assistant API服务器...")
    print("📚 RAG系统已集成DeepSeek聊天API和豆包嵌入模型")
    print("🔗 API文档地址: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
