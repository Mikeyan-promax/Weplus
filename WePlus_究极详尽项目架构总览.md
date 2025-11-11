# WePlus 文档项目究极详尽架构总览（迁移交接版）

> 编写说明：已启用 GPT-5-high 深度思考模式，全程深度分析与校对；为保证可读性，仅呈现结论，不展示内部推理过程。本文面向“对本项目完全陌生”的新 AI 助手，帮助其在最短时间内全面掌握项目结构、关键决策、操作习惯与落地方法。

---

## 1. 项目目标与范围

- 目标：构建“基于 RAG 的校园智能助手”，支持文档上传解析向量化检索、DeepSeek 聊天、多模块后台管理、用户系统与前端交互。
- 范围：后端（FastAPI）、服务层（RAG、向量存储、文档处理、日志）、数据库（PostgreSQL + pgvector）、前端（React + Vite）、联通（SSE/REST）、部署（Nginx/Railway）、可观测性（日志/巡检）、安全（CORS/限流/IP 白名单）、操作习惯（Git 推送等）。

---

## 2. 总体架构视图（文字版）

- 用户 → 前端（React + Vite） → 代理 `/api` → 后端 FastAPI（主入口 `backend/main.py`）
  - 中间件：请求 ID、IP 限流
  - 路由：RAG（聊天/流式/处理）、文档管理（上传/搜索/分类标签）、管理员后台（仪表盘/日志/备份/向量数据库/用户管理/学习资源/测试中心）
  - 服务层：RAG 服务（DeepSeek 聊天 + 豆包嵌入）、PostgreSQL 向量服务（pgvector）、文档服务（解析分块向量化）、日志服务（审计/系统/API 访问）
  - 数据库：PostgreSQL（`document_chunks` 含向量列、文档元数据、会话与消息、检索日志）
- 观测与安全：JSON 日志 + 请求 ID；可选 Sentry/Prometheus；CORS 白名单；管理员 IP 白名单；（可选）限流
- 部署：本地 Dev（Vite 代理 → FastAPI）；生产 Nginx 反代；Railway 可选；脚本化巡检与修复

---

## 3. 后端架构

### 3.1 应用入口与装配

- 主入口：`backend/main.py`
  - 创建应用：`FastAPI(title, description, version)`
  - 加载配置：`from app.core.config import settings`
  - 日志初始化：`app.core.logging_config.setup_logging(enable_json=settings.ENABLE_JSON_LOGGING)`
  - 中间件：
    - `RequestIdMiddleware`（注入 `X-Request-ID` 并贯通日志）
    - `RateLimitMiddleware`（IP 级滑动窗口，按分钟配额；受 `settings.REQUEST_RATE_LIMIT_ENABLED` 控制）
  - CORS：读取 `settings.ALLOWED_ORIGINS`（默认 `http://localhost:5173, 5174`）
  - 可选：`sentry_sdk`（存在 DSN 时启用）；`prometheus_fastapi_instrumentator`（`settings.PROMETHEUS_ENABLED`）
  - 依赖注入：`require_admin_ip_whitelist` 保护 `/api/admin*`，基于 `X-Forwarded-For` 或 `request.client.host`
  - 路由注册：
    - RAG：`app.api.rag_routes`
    - 文档管理：`app.api.document_routes`
    - 认证：`auth_routes`
    - 管理后台：`app/api/admin_*` 全套（用户、文件、RAG、仪表板、日志、备份、向量数据库、学习资源、测试中心）

### 3.2 全局配置（Settings）

- 文件：`backend/app/core/config.py`
- 关键项：
  - App：`APP_NAME, APP_VERSION, DEBUG`
  - Server：`HOST, PORT`
  - DB：`DATABASE_URL` 或 `POSTGRES_*`
  - Redis：`REDIS_URL`（可选）
  - AI：`DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL`；`OPENAI_API_KEY`（备用）；`ARK_API_KEY / ARK_BASE_URL / ARK_EMBEDDING_MODEL`
  - 向量存储：`VECTOR_DIMENSION`（默认 1536，实用 2560）；`CHROMA_PERSIST_DIRECTORY`
  - 上传限制：`UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS`
  - JWT：`SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES`
  - CORS：`ALLOWED_ORIGINS`
  - 观测：`ENABLE_JSON_LOGGING, SENTRY_DSN, PROMETHEUS_ENABLED`
  - 限流与访问控制：`REQUEST_RATE_LIMIT_ENABLED/REQUEST_RATE_LIMIT_PER_MINUTE`、`ADMIN_IP_WHITELIST`
  - 管理只读安全模式：`ADMIN_API_SAFE_MODE`（异常时返回结构化空数据；生产建议关闭以触发告警）

### 3.3 中间件与依赖注入

- 请求 ID：`app/middlewares/request_id_middleware.py`
  - 从 Header 读取或生成 UUID，注入日志上下文，写回 `X-Request-ID`
- 限流：`app/middlewares/rate_limit_middleware.py`
  - 依赖内存滑动窗口，按 `max_per_minute` 计数；默认关闭
- 管理 IP 白名单：`app/dependencies/admin_security.py`
  - 无白名单（本地开发）则放行；反代场景使用 `X-Forwarded-For` 首地址

### 3.4 路由模块地图

- RAG（`/api/rag`）：聊天（普通/流式）、文档处理（分块+嵌入+入库）、健康与统计
- 文档（`/api/documents`）：上传/批量上传、列表、删除、搜索、分类、标签、元数据维护
- 管理后台（`/api/admin/*`）：仪表板、日志、备份、向量数据库、RAG 知识库、用户管理、学习资源、测试中心
- 认证（`/api/auth/*`）：登录、注册、验证码；与前端 JWT 流程对接

### 3.5 服务层

- RAG 服务：`backend/app/services/rag_service.py`
  - DeepSeek 聊天：`chat_completion(messages, stream=True/False)`
  - 豆包嵌入：`embedding_model=doubao-embedding-text-240715`；单/批量嵌入（含缓存与性能监控钩子）
  - 检索：基于 pgvector 搜索相关分块，拼接上下文生成回答；失败时回退普通聊天
- PostgreSQL 向量服务：`backend/app/services/postgresql_vector_service.py`
  - 维度：`embedding_dimension=2560`（与豆包模型一致）
  - 入库：`add_document(document_id, chunks, metadata)` → 为每块生成嵌入并写入 `document_chunks(embedding vector)`
  - 检索：`search_similar(query, top_k, similarity_threshold)`，使用 `<=>` 余弦相似度，返回 `document_id/content/metadata/similarity`
- 文档服务：`backend/app/services/document_service.py`
  - 上传管线：验证 → 计算哈希去重 → 解析文本 → 分块 → 生成嵌入 → 向量入库 → 更新状态
  - 我们已修复：严格拒绝 `.xls`；上传失败不保留记录；失败/处理中旧记录可重试；统一清理残留（本地文件与DB）
- 日志服务：`backend/app/services/logging_service.py`
  - 多表日志（系统/用户行为/安全/API访问）与索引；文件日志输出 `logs/weplus.log`

---

## 4. 数据库与存储

### 4.1 连接与池化

- `backend/database/config.py`：`asyncpg + psycopg2`，统一线程池/连接池；`get_db_connection()` 面向服务层
- `backend/database/postgresql_config.py`：Aliyun RDS 连接池（`SimpleConnectionPool`）；历史迁移兼容

> 建议：统一代码使用 `database/config.py` 的 `get_db_connection`，减少环境差异。

### 4.2 主要表结构概览（逻辑）

- `documents`：文档元信息（标题、描述、分类、标签、状态、哈希等）
- `document_chunks`：文档分块（`content`、`embedding vector(2560)`、`metadata`、`chunk_index`）
- `chat_sessions` / `chat_messages`：会话与消息（便于对话历史与检索日志）
- `retrieval_logs`：检索记录（查询、命中块、相似度、耗时等）
- 管理后台相关多表（用户、角色、文件记录、处理状态等）

### 4.3 pgvector 配置

- `embedding` 列类型：`vector(2560)`（与豆包嵌入模型维度一致）
- 检索：`1 - (embedding <=> query_vector) as similarity`，按距离排序并过滤阈值
- 维度一致性：后端服务层已使用 2560；`settings.VECTOR_DIMENSION` 默认 1536，建议统一到 2560

### 4.4 迁移与修复脚本（举例）

- `fix_embedding_dimension_2560.py` / `fix_vector_dimension.py` / `fix_vector_search.py`：维度与检索修复
- `fix_document_chunks_*` 系列：分块表约束/结构修复
- `init_postgresql.py` / `init_db.sql`：初始化与统一建库

---

## 5. 文档处理与上传管线（关键）
## 4.A 数据库架构深描与规范（扩展）

- 连接/池化策略
  - 统一入口：`backend/database/config.py` 提供 `asyncpg` 与 `psycopg2` 的连接池封装，面向服务层暴露简化接口。
  - 历史兼容：`backend/database/postgresql_config.py`（含备份与 legacy 版本）用于阿里云 RDS 连接池，建议逐步统一到 `database/config.py`。

- pgvector 维度规范
  - 标准维度：`2560`（豆包 `doubao-embedding-text-240715`）。
  - 列类型：`document_chunks.embedding vector(2560)`；确保服务层生成向量与列类型一致。
  - 配置统一：`settings.VECTOR_DIMENSION` 建议设置为 `2560`，避免默认 `1536` 带来的维度不一致。

- 关键表（逻辑结构与约束）
  - `documents`
    - 字段示例：`id, title, description, category, tags, status, file_hash, created_at, updated_at`
    - 约束与索引：`UNIQUE(file_hash)`；`INDEX(category)`；`INDEX(created_at)`
  - `document_chunks`
    - 字段示例：`id, document_id(FK), chunk_index, content, embedding(vector(2560)), metadata(jsonb), created_at`
    - 约束与索引：`INDEX(document_id, chunk_index)`；`GIN(metadata)`；必要时 `IVFFlat/ HNSW`（如启用 pgvector 索引方案）
  - `chat_sessions` / `chat_messages`
    - 会话可含 `user_id, title, created_at`；消息含 `session_id, role, content, created_at`
    - 索引：`INDEX(session_id, created_at)`；必要时消息表分区（高并发时）
  - `retrieval_logs`
    - 字段示例：`query, top_k, hit_ids, similarity_stats, elapsed_ms, created_at`
    - 索引：`INDEX(created_at)`；`GIN(hit_ids)`（数组/JSON）

- 迁移与修复策略（与现有脚本对应）
  - 维度统一：`fix_embedding_dimension_2560.py` / `fix_vector_dimension.py` 调整列类型与维度一致性。
  - 检索修复：`fix_vector_search.py` 校准距离/相似度计算与查询语句。
  - 分块表修复：`fix_document_chunks_*` 系列统一约束（主键、外键、索引）。
  - 初始化：`init_postgresql.py` / `postgresql_unified_schema.sql` 引导统一建库。

> 注意：上述字段命名与索引为项目内常见实践的逻辑总结，具体列名以 `backend/database/*.sql` 与 `models.py` 实际定义为准；维度与检索逻辑已经在服务层与脚本中统一至 2560。

---

- 路由：`POST /api/documents/upload`（`document_routes.py`）
- 服务：`DocumentService.upload_document`
  1) 验证：扩展名/大小（明确拒绝 `.xls`；`MAX_FILE_SIZE` 控制）
  2) 哈希：`Document.get_by_hash` 去重（失败/处理中旧记录允许复用与重试；成功状态提示已存在）
  3) 解析：按类型（PDF/Word/HTML/PPTX/Excel/TXT/MD 等）提取纯文本
  4) 分块：控制 `chunk_size` 与 `chunk_overlap`（同 `rag_service`）
  5) 嵌入：批量生成（豆包 `doubao-embedding-text-240715`，维度 2560）
  6) 入库：写入 `document_chunks` 与文档状态更新
  7) 失败清理：任何步骤异常，彻底清理本地与数据库记录，保证可重传

> 我们近期修复了“上传失败仍保留记录导致‘文档已存在’”的问题，并将 `.xls` 严格拒绝，以提升稳定性。

---

## 6. RAG 检索与聊天

- 检索：`rag_service.retrieve_relevant_documents()` → `postgresql_vector_service.search_similar()`
- 上下文组装：把检索到的文档块拼接为系统提示，调用 DeepSeek 生成回答
- 回退机制：检索不可用或为空时，降级为普通聊天
- 流式 SSE：`POST /api/rag/chat/stream`，按 `text/event-stream` 返回分片（字段 `content/finished/error`）

---

## 7. 前端架构

- 技术栈：React + TypeScript + Vite；React Router；CSS Modules；动画与富文本（Markdown/Math）
- 代理：`frontend2/vite.config.ts` — `server.proxy['/api'] -> http://localhost:8000`（开发态避免跨域）
- 路由：`frontend2/src/App.tsx` 集中注册（主页、RAGChat、用户信息、校园地图、认证页、管理后台等）
- RAG聊天：组件 `RAGChat.tsx` + 服务 `src/services/ragApi.ts`（普通/流式）
- 管理后台：`AdminDashboard` 与 `components/admin/*` 对接 `/api/admin/*` 系列接口
- 报告与文档：`frontend2/404错误调研报告.md` 等用于问题定位与共享知识

> 404 提示（已确认）：后端没有 `/documents/paginated` 路由；该 404 常与 `/health` 成对出现，可能来源于历史缓存/第三方插件/某轮询；前端代码暂无此调用。

---

## 8. 前后端连接

- 通信：REST（JSON）；流式 SSE（RAG 聊天）
- 代理：开发态 Vite 代理；生产态使用 Nginx 反代到 FastAPI（或通过 Railway 等托管方案）
- CORS：按 `settings.ALLOWED_ORIGINS` 白名单控制；生产需更新为正式域名

---

## 9. 部署与运行

### 9.1 本地开发

- 启动后端：`uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
- 启动前端：`npm run dev`（默认 5173，已代理 `/api` 到 8000）

### 9.2 生产部署（示例）

- Nginx：反代 `/api` 到 FastAPI；静态资源由前端构建产物提供
- Railway：`deploy/` 目录含 `docker-compose.yml` 与 `nginx.railway.conf.template`；提供上线检查脚本
- 监控：
  - Sentry：设置 `SENTRY_DSN` 即启用
  - Prometheus：`settings.PROMETHEUS_ENABLED=True` 暴露 `/metrics`
  - 日志：统一输出到 `logs/weplus.log`（JSON/文本可选）

---

## 10. 安全与访问控制

- 认证：`/api/auth/*`；前端采用 JWT（LocalStorage 持久化）
- CORS：白名单控制；生产需严格限制来源域
- 限流：`RateLimitMiddleware`（默认关闭；按 IP/分钟计数）
- 管理端 IP 白名单：保护 `/api/admin*`；本地开发空白名单时放行
- 管理只读安全模式：`ADMIN_API_SAFE_MODE=True` 时只读端点异常返回结构化空数据（200），避免仪表盘不可用；生产建议关闭以暴露问题并触发告警

---

## 11. 日志与可观测性

- 请求 ID：贯通日志，定位问题迅速（`X-Request-ID`）
- 统一日志服务：系统/用户行为/安全/API 访问多表；自动建表与索引；文件输出 `logs/weplus.log`
- 巡检脚本：`backend/test_admin_readonly_endpoints.py`（只读接口巡检），`backend/test_api_*` 系列（集成测试）

---

## 12. 操作习惯与约定（极重要）

- Windows 多命令连接符：使用 `;;`（不是 `&&`）
- 对话与代码注释：统一中文；在生成代码时添加函数级注释（文档不适用）
- 推送到 GitHub：采用“标准流程 + 安全强推（必要时）”，并清理代理与证书设置避免 `Recv failure: Connection was reset`

### 12.1 标准推送流程（已设为默认）

```powershell
# 线性化历史后提交并推送
git switch main ;; git pull --rebase ;; git add -A ;; git commit -m "描述本次改动" ;; git push
```

### 12.2 一次性正常推送（已在 main 且远程已设置）

```powershell
git add -A ;; git commit -m "update" ;; git pull --rebase ;; git push
```

### 12.3 覆盖远程（谨慎；推荐安全强推）

```powershell
# 安全强推（本地覆盖远程，但在本地落后于远程时拒绝覆盖）
git push -u origin main --force-with-lease

# 绝对强推（仅在完全不保留远程历史时使用）
# git push -u origin main --force
```

### 12.4 代理与证书设置清理（避免 Recv failure）

```powershell
# 清理 Git 代理
git config --global --unset http.proxy ;; git config --global --unset https.proxy

# 强制使用 Windows 证书链
git config --global http.sslbackend schannel

# 禁用 HTTP/2，使用 HTTP/1.1 提升兼容性
git config --global http.version HTTP/1.1
```

> 推送后远程 URL 应为安全地址：`https://github.com/Mikeyan-promax/Weplus.git`（不含令牌）。

> 脚本：`scripts/win_push.ps1` 可一键执行“拉取→提交→推送”。

## 12.A GitHub 推送问题与解决方案（详尽版）

为便于新助手快速定位与修复，这里汇总我们近期对话中涉及的推送问题、成因与操作步骤，均基于 Windows 11 与 PowerShell，使用多命令分隔符 `;;`。

- 常见问题类型与成因
  - 远程地址错误或失效：`origin` 指向错误仓库或带令牌的临时 URL，导致 403/401 或认证异常。
  - 分支不一致/分叉历史：本地 `main` 与远程 `origin/main` 历史不同步，正常推送被拒绝，需要变基或强推。
  - 网络与代理：系统/浏览器代理残留导致 `Recv failure: Connection was reset` 或 TLS 握手不稳定。
  - TLS/证书链问题：Windows 上 Git 使用 OpenSSL 时偶发证书链兼容问题，切换到 `schannel` 更稳。
  - HTTP/2 兼容：部分网络在 HTTP/2 下表现不稳定，降级到 HTTP/1.1 更兼容。
  - 分离 HEAD：处于分离 HEAD 状态导致无法重命名当前分支或推送失败。
  - 凭据交互：弹出用户名/密码框时，密码必须填 GitHub PAT，不是登录密码。

- 标准修复流程（安全、线性化优先）
  - 检查远程：`git remote -v` 确保为安全地址 `https://github.com/Mikeyan-promax/Weplus.git`
  - 切到 `main` 并线性化：`git switch -C main ;; git pull --rebase`
  - 暂存提交：`git add -A ;; git commit -m "本次改动描述"`
  - 正常推送：`git push`（已建立跟踪即可）

- 强制覆盖场景（谨慎使用，推荐安全强推）
  - 使用 `--force-with-lease`：在本地落后于远程时拒绝覆盖，避免误伤他人提交。
    - `git push -u origin main --force-with-lease`
  - 绝对强推（仅当远程历史不需保留时）：`git push -u origin main --force`

- 网络/证书问题修复清单（Windows）
  - 清理代理：`git config --global --unset http.proxy ;; git config --global --unset https.proxy`
  - 切换证书后端：`git config --global http.sslbackend schannel`
  - 禁用 HTTP/2：`git config --global http.version HTTP/1.1`
  - 若仍异常：检查系统代理/VPN、防火墙与企业网络策略；必要时临时关闭 VPN 后再试。

- 分离 HEAD 修复
  - 执行：`git switch -C main`；若需要保留当前游离提交，先创建新分支再合并到 `main`。

- 凭据与安全
  - 用户名：`Mikeyan-promax`
  - 密码：GitHub PAT（个人访问令牌），不是登录密码。
  - 推送后：保持远程地址为安全 URL，不在 `.git/config` 中保存令牌。

> 我们近期的对话与操作，已将以上流程固化为默认方案：优先 `pull --rebase` 同步，正常 `push`；明确要求“覆盖远程”时，改用 `--force-with-lease` 并回报覆盖范围与结果。

---

## 13. 主要 API 端点速览

- RAG
  - `POST /api/rag/chat` — 智能聊天（RAG/普通）
  - `POST /api/rag/chat/stream` — 流式聊天（SSE）
  - `POST /api/rag/documents/process` — 文档内容分块与向量化入库
- 文档
  - `POST /api/documents/upload` / `POST /api/documents/batch-upload`
  - `GET /api/documents/list` / `DELETE /api/documents/{id}`
  - `POST /api/documents/search`
  - 分类/标签：`/api/documents/categories` / `/api/documents/tags`
- 管理后台（IP 白名单保护）
  - `/api/admin/dashboard/*`、`/api/admin/rag/*`、`/api/admin/vector/*`、`/api/admin/backup/*`、`/api/admin/logs/*`
- 认证
  - `POST /api/auth/login`、`POST /api/auth/register`、`POST /api/auth/send-verification-code`

---

## 14. 常见问题与故障排查

- 404 `/documents/paginated`
  - 后端未定义该路由；日志显示与 `/health` 成对出现，可能来源于历史缓存/第三方插件/某轮询；前端未发现直接调用
- 文档已存在但上传失败保留记录
  - 已修复：上传失败不保留记录；失败/处理中允许重试；严格拒绝 `.xls`
- Git 推送 `Recv failure: Connection was reset`
  - 清理代理；使用 `schannel` 与 `HTTP/1.1`；验证网络环境与 VPN 状态
- 向量维度不一致
  - 统一使用 2560（豆包嵌入）；检查 `document_chunks.embedding` 列类型与服务层配置

---

## 15. 端到端数据流示例

- 文档上传 → 验证扩展/大小 → 哈希查重 → 解析文本 → 分块 → 生成嵌入 → 写入 `document_chunks` → 更新文档状态 → 前端收到结果
- RAG 聊天 → 向量检索相关分块 → 拼接上下文 → DeepSeek 生成回答 → 返回答案与来源；流式模式按 SSE 片段传输

---

## 16. 近期修复点与行为变化

- 上传失败不保留记录；彻底清理本地与数据库残留
- `.xls` 严格拒绝；减少解析失败与兼容问题
- 失败/处理中旧记录允许复用与重试；成功状态仍提示已存在
- 流式聊天在 RAG 检索异常时回退普通聊天，保证体验稳定

---

## 17. 未来改进建议

- 统一数据库连接模块（去除历史分裂配置）
- 将 `settings.VECTOR_DIMENSION` 与服务层模型统一到 2560
- 为文档处理与检索补充端到端集成测试，覆盖上传→分块→嵌入→检索→聊天
- 在前端新增“RAG服务健康/统计”页，调用 `/api/rag/stats` 可视化缓存、模型与向量库状态
- 部署时使用反代统一域，配合严格 CORS 白名单与安全头

---

## 18. 环境变量清单（常用）

- DeepSeek：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL=https://api.deepseek.com`
- 豆包嵌入：`ARK_API_KEY`、`ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3`、`ARK_EMBEDDING_MODEL=doubao-embedding-text-240715`
- 数据库：`DATABASE_URL` 或 `POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_HOST/POSTGRES_PORT`
- 日志与观测：`SENTRY_DSN`、`PROMETHEUS_ENABLED`
- CORS：`ALLOWED_ORIGINS`
- 管理安全：`ADMIN_IP_WHITELIST`（逗号分隔）

---

## 19. 目录地图（摘录）

```
backend/
  main.py
  app/
    api/ (RAG、文档、管理员等路由)
    core/ (config、logging)
    dependencies/ (admin_security)
    middlewares/ (request_id、rate_limit)
    services/ (rag_service、postgresql_vector_service、document_service、logging_service)
    models/ (rag_models)
  database/ (config、postgresql_config、rag_models、admin_models、schema与初始化脚本)
  requirements.txt
frontend2/
  vite.config.ts
  src/App.tsx
  src/components/ (RAGChat 等)
  src/services/ragApi.ts
scripts/win_push.ps1
```

---

## 20. 新 AI 助手操作速览

- 语言与注释：请统一使用中文；编写代码时添加“函数级注释”
- Windows 命令分隔符：使用 `;;`（不是 `&&`）
- 推送到 GitHub：默认执行“拉取→提交→推送”，仅在明确要求覆盖时使用 `--force-with-lease`
- 代理与证书：推送前可按需执行代理清理与 `schannel/HTTP1.1` 设置
- 变更提交信息：采用明确语义，如 `fix: 上传失败不保留记录；严格拒绝 .xls；清理旧失败`

---

### 附：示例启动与检查

```bash
# 后端（开发环境）
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 前端（开发环境）
npm run dev

# 管理只读巡检（后端脚本）
python backend/test_admin_readonly_endpoints.py
```

---

> 交接完成：本文件位于项目根目录，作为新 AI 助手的统一入口与速成指南。若需进一步生成“接口清单”或“架构图（ASCII/PlantUML）”，可在此基础上扩展。

附：相关附加文件（生成后）

- `WePlus_API接口清单.md` — 按“Swagger式”汇总主要端点、方法、请求/响应模型与示例。
- `WePlus_架构图.puml` — PlantUML 架构图（可在任意 PlantUML 渲染器中生成 PNG/SVG）。
