# WePlus 在 Railway 部署指南（详细版）

> 本指南为 Railway.com 的图形界面（UI）逐步操作说明，覆盖：项目创建、服务构建、环境变量配置、数据库接入、健康检查、故障排除与发布后联通检查。请严格按照步骤执行。

---

## 前置条件
- 代码仓库：`https://github.com/Mikeyan-promax/Weplus.git`（已推送）
- 仓库根目录存在 `railway.json` 与 `Dockerfile`（已配置）
- 容器启动：使用 `supervisord` 同时运行 `Uvicorn(8000)` 与 `Nginx(80)`，`/api/` 由 Nginx 反向代理到后端
- 健康检查端点：`GET /api/healthz`（后端已实现，对齐 `railway.json`）

---

## 一、在 Railway 创建项目并连接 GitHub 仓库
1. 登录 Railway（浏览器访问 `https://railway.com/`）。
2. 点击右上角 `New Project`。
3. 选择 `Deploy from GitHub`。
4. 在仓库列表中选择 `Mikeyan-promax/Weplus`。
5. 确认后，Railway 将自动识别 `railway.json` 并按 `Dockerfile` 构建服务。

> 提示：Railway 会为你创建一个默认服务（Web Service），并分配一个公共域名如 `https://<project>-up.railway.app`。

---

## 二、服务构建与健康检查设置
- 构建方式：`railway.json` 指定 `builder = DOCKERFILE`，无需额外配置。
- Dockerfile 要点：
  - 前端：Node 18 多阶段构建，静态产物复制到 `/usr/share/nginx/html`
  - 后端：Python 3.11，`uvicorn` 以 8000 端口启动 FastAPI
  - 运行时：同时运行 `nginx(80)` 与 `uvicorn(8000)`（见 `deploy/supervisord.railway.conf`）
- 健康检查：`railway.json` 已配置 `deploy.healthcheckPath = /api/healthz`
  - Nginx 将 `/api/` 代理到 `127.0.0.1:8000`，因此健康检查会命中后端 `/api/healthz`

> 如需手动在 UI 中核对：进入服务 -> Settings -> Health Checks，确认 Path 为 `/api/healthz`。

---

## 三、环境变量配置（Railway Variables 面板）
进入服务页面 → 侧边栏 `Variables` → 逐个 `New Variable` 添加。以下为后端读取的关键变量及建议：

- 基础运行与安全
  - `SECRET_KEY`：JWT签名密钥（必须，生产随机生成，长度≥32）
  - `DEBUG`：`false`（生产禁用调试）
  - `ENABLE_JSON_LOGGING`：`true`（推荐生产启用）
  - `ALLOWED_ORIGINS`：允许跨域源列表。支持逗号分隔或JSON数组
    - 示例：`https://<your-domain>,https://<railway-subdomain>` 或 `["https://foo","https://bar"]`
  - `ADMIN_IP_WHITELIST`：管理员接口来源白名单（建议生产限制，逗号分隔或JSON数组）。示例：`"127.0.0.1,10.0.0.0/24"` 或 `[]`

- 数据库（两种方案，选其一为主）：
  1) 统一连接串（推荐）
     - `DATABASE_URL`：完整连接串。例如：`postgresql://USER:PASS@HOST:PORT/DBNAME`
     - 当设置了 `DATABASE_URL`，`backend/app/core/config.py` 的 `settings.database_url` 会优先使用它。
  2) 明细字段（兼容异处代码）：
     - `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`（用于 `backend/database/config.py`）
     - `POSTGRES_HOST`、`POSTGRES_PORT`、`POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`（用于后端 Settings 构造连接串）
     - 若已设置 `DATABASE_URL`，以上两组可不填；若未设置，请保证两组与真实连接保持一致。

- AI 模型与外部服务
  - `DEEPSEEK_API_KEY`：DeepSeek API 密钥（如使用 DeepSeek）
  - `DEEPSEEK_BASE_URL`：`https://api.deepseek.com`（默认即可）
  - `OPENAI_API_KEY`：备用（如使用 OpenAI）

- 可观测性与监控（按需）：
  - `SENTRY_DSN`：Sentry DSN（可选）
  - `PROMETHEUS_ENABLED`：`false` 或 `true`（启用后会暴露指标端点，详见后端配置）

- 限流与访问控制（按需）：
  - `REQUEST_RATE_LIMIT_ENABLED`：`false` 或 `true`
  - `REQUEST_RATE_LIMIT_PER_MINUTE`：如 `60`

> UI 操作路径提示：服务 → Variables → New Variable → 输入 `Key` 与 `Value` → Save。

---

## 四、数据库接入（Railway Postgres）
Railway 提供托管 Postgres，可在项目中添加数据库并获得连接串：
1. 进入项目主页 → 左侧 `Add` → 选择 `Database` → `PostgreSQL`。
2. 创建数据库后，在其页面找到连接信息（`postgresql://user:pass@host:port/db`）。
3. 回到 Web 服务的 `Variables` 面板：
   - 设置 `DATABASE_URL = <上述连接串>`（推荐）
   - 如选择明细字段方案，同时设置 `DB_*` 与 `POSTGRES_*`。
4. 部署后，后端会自动使用连接串初始化连接池并进行健康检查。

> 提示：如你希望最小配置，设置 `DATABASE_URL` 一项即可覆盖大部分使用场景。

---

## 五、发布与回滚
- 首次连接仓库后，Railway 会自动构建与部署。若失败，转到服务 `Deployments` 查看日志。
- 正常发布后，访问分配的域名验证页面与 API：
  - 前端：`https://<subdomain>.railway.app`（静态站点）
  - API 示例：`https://<subdomain>.railway.app/api/healthz`
- 回滚：在 `Deployments` 列表中选中上一个成功版本，点击 `Roll back`。

---

## 六、故障排除（常见问题）
- 构建失败（Docker）：检查 `Dockerfile` 依赖安装与网络连接；Railway 默认联网权限受限时，可重试。
- 健康检查失败：确认 `/api/healthz` 在后端存在，且 Nginx 代理 `/api/` 到 `127.0.0.1:8000` 正常；查看容器日志。
- 500/数据库错误：
  - 是否已设置 `DATABASE_URL` 或 `DB_*`/`POSTGRES_*`？
  - 防火墙或安全组是否允许数据库连接？
- CORS 错误：`ALLOWED_ORIGINS` 是否包含当前访问域名？
- 认证异常：`SECRET_KEY` 是否正确设置并固定？

---

## 七、启用持久化存储（Persistent Volumes）

> 目的：保证学习资源文件在重部署后仍然存在，避免容器重建导致本地上传文件丢失。

### 1) 在 Railway 服务中添加持久化卷
- 进入项目 → 选择后端 Web 服务（运行 FastAPI + Nginx 的服务）。
- 在服务面板中找到存储相关入口（例如 `Storage`/`Volumes`）。
- 点击 `Add Volume`/`New Volume`，新增一个持久化卷。
  - Mount Path（挂载路径）：推荐设置为 `/data` 或更具体的 `/data/study_resources`。
  - 保存并返回服务页面。

> 说明：不同版本 UI 文案可能略有差异，但总体路径为“服务页面 → 存储/卷（Storage/Volumes）→ 添加（Add）”。如未找到，请使用 Railway 的搜索框搜索 “Volumes”。

### 2) 配置后端环境变量指向持久化路径
- 打开服务 → `Variables` 面板，新增以下变量（至少设置第一条）：
  - `STUDY_RESOURCES_DIR = /data/study_resources`（学习资源主目录，强烈推荐设置）
  - 可选：`ADMIN_UPLOAD_DIR = /data/uploads`（后台通用上传目录，如启用后台文件管理）
  - 可选：`UPLOAD_DIR = /data`（全局基础目录，后端会在其下创建 `study_resources` 子目录）
- 点击保存变量。

> 后端实现说明：`backend/app/api/study_resources_api.py` 会优先读取 `STUDY_RESOURCES_DIR`，不存在时回退到 `settings.UPLOAD_DIR/study_resources`，最后默认项目内目录。`admin_file_api.py` 会优先读取 `ADMIN_UPLOAD_DIR` 或 `UPLOAD_DIR`。

### 3) 重新部署服务
- 进入服务 → `Deployments` → 点击 `Redeploy` 或提交代码触发自动部署。
- 部署完成后，持久化卷将自动挂载到容器的指定路径。

### 4) 验证与迁移旧文件（一次性）
- 验证持久化配置：
  - 管理员巡检接口：`GET /api/study-resources/admin/scan-missing`（需管理员 Token），响应中 `summary.upload_dir` 应为 `/data/study_resources`。
- 迁移旧文件：将本地旧资源打包为 ZIP 并上传修复路径：
  - Windows PowerShell 示例（注意多命令用 `;;` 连接）：
    - `curl.exe -X POST -H "Authorization: Bearer <admin_token>" -F "zip_file=@C:\\path\\to\\resources.zip" -F "overwrite_existing=true" https://<your-domain>.railway.app/api/study-resources/admin/import-zip` ;; 
      `curl.exe -H "Authorization: Bearer <admin_token>" https://<your-domain>.railway.app/api/study-resources/admin/scan-missing`
- 逐条确认无法匹配的文件名（接口返回 `unmatched` 列表），必要时手动整理压缩包中文件名以匹配数据库 `original_filename` 或 `file_path` 的 basename。

> 提示：启用持久化卷后，新上传的文件会直接保存到卷中；重部署不会丢失。

---

## 八、发布后联通检查（一次性脚本）
- 仓库内提供脚本：`deploy/checks/railway_post_deploy_check.py`
- 用法（Windows PowerShell）：
  - `python deploy/checks/railway_post_deploy_check.py --base-url https://<subdomain>.railway.app` ；可串联命令用 `;;`。
- 脚本会依次检查：`/api/healthz`、`/health`、`/readyz`、`/docs` 并输出结果。

---

## 九、UI 路径速查（Railway 面板）
- 新建项目：`New Project` → `Deploy from GitHub` → 选仓库
- 查看构建与发布：服务 → `Deployments`
- 环境变量：服务 → `Variables` → `New Variable`
- 健康检查：服务 → `Settings` → `Health Checks`（Path: `/api/healthz`）
- 数据库：项目主页 → `Add` → `Database (PostgreSQL)` → 复制连接串

---

## 十、附录：后端环境变量清单（对照）
- 运行与安全：`SECRET_KEY`、`DEBUG`、`ENABLE_JSON_LOGGING`、`ALLOWED_ORIGINS`、`ADMIN_IP_WHITELIST`
- 数据库（任选其一或同时）：`DATABASE_URL`；`DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`；`POSTGRES_HOST`、`POSTGRES_PORT`、`POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`
- 模型与外部服务：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`OPENAI_API_KEY`
- 可观测性：`SENTRY_DSN`、`PROMETHEUS_ENABLED`
- 限流：`REQUEST_RATE_LIMIT_ENABLED`、`REQUEST_RATE_LIMIT_PER_MINUTE`

> 注：本指南严格依据仓库内 `Dockerfile`、`railway.json`、`deploy/nginx.railway.conf`、`backend/app/core/config.py` 与 `backend/database/config.py` 的实际实现撰写。

