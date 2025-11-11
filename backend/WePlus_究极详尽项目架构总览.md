# WePlus 项目架构总览（后端）

本文档梳理 WePlus 后端的核心结构、初始化流程、环境变量配置及关键模块的协作关系，帮助快速定位问题与安全上线。

## 应用入口与路由
- 入口文件：`backend/main.py`
- 框架：FastAPI
- 中间件：`RequestIdMiddleware`、`RateLimitMiddleware`、CORS
- 可观测性：Sentry（按 `SENTRY_DSN` 启用）、Prometheus（按 `PROMETHEUS_ENABLED` 启用）
- 路由注册：RAG、认证、文档管理、后台管理（用户/文件/RAG/仪表盘/日志/备份/向量库）、学习资源、测试中心等

## 启动与关闭事件
- `@app.on_event("startup")`：
  - 调用 `logging_service.initialize()`，确保日志表与索引存在（失败不影响主流程）。
  - 自检关键表（以 `admin_users` 为哨兵），缺失时执行 `database/postgresql_complete_schema.sql` 完整 Schema。
- `@app.on_event("shutdown")`：记录关闭日志。

## 日志服务 LoggingService
- 文件：`app/services/logging_service.py`
- 关键方法：
  - `initialize()`：一次性初始化，内部调用 `ensure_log_tables()`；失败记录错误不抛出异常。
  - `ensure_log_tables()`：创建/自愈三类日志表：`system_logs`、`user_action_logs`、`api_access_logs`，并补全缺失列与索引（幂等）。
  - `log_system_event()`、`log_user_action()`、`log_api_access()`：写入日志（数据库+文件）。
- 数据库访问：`from database.postgresql_config import get_db_connection`（同步连接池，惰性初始化）。

## 数据库管理与初始化
- 管理器（同步）：`database/db_manager.py`
  - 连接池：`SimpleConnectionPool`（环境变量 `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`）
  - 常用方法：`execute_query()`、`table_exists()`、`create_table_from_sql()`
- 连接配置（同步）：`database/postgresql_config.py`
  - 便捷方法：`get_db_connection()`、`init_connection_pool()`
- 完整 Schema：`database/postgresql_complete_schema.sql`
  - 在启动事件中，当 `admin_users` 不存在时执行一次，以保证基础表、索引和约束到位。
- 注意：`database/admin_models.py` 中的 `init_tables()` 采用 `async` 包装但内部依赖同步执行，当前不作为启动入口使用，避免 `await` 非协程导致的运行时错误。

## 环境变量与配置
- `.env` 加载：`app/core/config.py` 使用 Pydantic BaseSettings；`email_service.py` 也通过 `dotenv.load_dotenv()` 读取。
- 数据库：
  - `DATABASE_URL`（优先）或 `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`
- 邮件服务（来自 `.env`，由 `app/services/email_service.py` 读取并惰性初始化）：
  - `MAIL_USERNAME`、`MAIL_PASSWORD`、`MAIL_FROM`、`MAIL_PORT`、`MAIL_SERVER`
  - `MAIL_FROM_NAME`、`MAIL_STARTTLS`、`MAIL_SSL_TLS`
  - 使用方式：`email_service.ensure_mail_client()` 成功后发送验证码邮件；`DEBUG=True` 时不实际发信，直接返回验证码用于调试。
- 其他：`DEEPSEEK_API_KEY/BASE_URL`、`ARK_API_KEY/BASE_URL/EMBEDDING_MODEL`、`VECTOR_DIMENSION`、`UPLOAD_DIR`、`ALLOWED_EXTENSIONS`、`SECRET_KEY`、`ADMIN_API_SAFE_MODE` 等。

## RAG 与学习资源
- RAG：`app/api/rag_routes.py`，向量搜索等服务在 `app/services/postgresql_vector_service.py`。
- 学习资源：`app/api/study_resources_api.py`，目录从 `settings` 读取（日志显示为 `uploads/study_resources`）。

## 运行与健康检查
- 根路径：`/` 返回应用信息。
- 健康检查：`/health`、`/healthz`、`/api/healthz`、就绪检查 `/readyz`。

## 迁移与注意事项（简版）
- 建议基于 `postgresql_complete_schema.sql` 初始化/迁移表结构。
- 首次启动自动执行 Schema（仅当检测到缺失表）。
- 如需强制重建或大规模迁移，请先备份数据，并按顺序：停机 → 迁移 → 验证 → 上线。
- 详尽迁移报告参见：`backend/PostgreSQL_Migration_Final_Report.md`。

## 常见问题
- 邮件服务初始化失败：检查 `.env` 的邮箱与 SMTP 信息；或在开发模式下（`DEBUG=True`）直接回显验证码。
- 启动后日志表缺失：确认 `logging_service.initialize()` 已在启动事件中调用；检查数据库权限。
- `admin_models.init_tables()` 未被调用：使用启动事件中的自检与完整 Schema 初始化逻辑替代。

## 变更记录（本次）
- 在 `main.py` 的启动事件：
  - 调用 `logging_service.initialize()`；
  - 自检 `admin_users` 表，缺失时执行 `database/postgresql_complete_schema.sql`；
  - 记录初始化结果与异常日志。

