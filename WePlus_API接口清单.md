# WePlus API 接口清单（Swagger式汇总）

> 说明：本清单基于现有后端源码自动汇总，按路由前缀分组，列出方法、路径、用途与请求/响应要点。管理员端点默认受“IP 白名单”与认证保护；部分模块使用 HTTP Bearer 认证。

---

## 概览

- 后端框架：FastAPI（`backend/main.py`）
- 全局前缀：开发态通过前端代理 `/api` → 后端；生产通过 Nginx 反代
- 文档/模型：Pydantic 模型分布在 `app/models` 与各 API 文件中

---

## 认证（Auth，前缀 `/auth`）

- POST `/auth/send-verification-code` — 发送邮箱验证码
- POST `/auth/register` — 注册，响应令牌
- POST `/auth/login` — 登录，响应令牌
- POST `/auth/refresh` — 刷新令牌
- GET `/auth/me` — 获取当前用户信息
- POST `/auth/verify-email` — 验证邮箱
- POST `/auth/logout` — 用户登出
- POST `/auth/resend-verification` — 重发验证码

请求要点：
- 认证端点通常接收 `email`/`username`/`password` JSON 字段，返回 `access_token`/`refresh_token` 与用户基本信息。
- 响应模型：`TokenResponse` / `UserResponse`（详见 `backend/auth_routes.py`）。

---

## RAG 系统（前缀 `/api/rag`）

- POST `/api/rag/chat` — 智能聊天（RAG/普通），返回 `ChatResponse`
- POST `/api/rag/chat/stream` — 流式聊天（SSE），返回事件流（`content/finished/error`）
- POST `/api/rag/documents/process` — 文档分块与向量化入库，返回 `DocumentProcessResponse`
- POST `/api/rag/documents/upload` — 直接上传文档并处理（上传文件 `multipart/form-data`）
- GET `/api/rag/documents` — 列出已处理文档
- DELETE `/api/rag/documents/{document_id}` — 删除文档
- GET `/api/rag/health` — RAG 服务健康
- POST `/api/rag/search` — 语义检索，接收 `QueryRequest{ query, top_k, similarity_threshold }`
- GET `/api/rag/stats` — RAG 状态与统计

请求要点：
- 聊天：`ChatRequest{ messages: ChatMessage[], rag_enabled?: boolean }`
- 文档处理：`DocumentProcessRequest{ document_id 或 文件上传 }`
- 检索：`QueryRequest{ query: string, top_k?: number, similarity_threshold?: number }`

---

## 文档管理（前缀 `/api/documents`）

- GET `/api/documents/supported-types` — 支持的上传类型
- POST `/api/documents/upload` — 上传单个文档（`multipart/form-data`）
- POST `/api/documents/batch-upload` — 批量上传
- GET `/api/documents/list` — 文档列表
- GET `/api/documents/{document_id}` — 文档详情
- PUT `/api/documents/{document_id}` — 更新文档元数据
- DELETE `/api/documents/{document_id}` — 删除文档
- POST `/api/documents/categories` — 创建分类
- GET `/api/documents/categories` — 分类列表
- PUT `/api/documents/categories/{category_id}` — 更新分类
- DELETE `/api/documents/categories/{category_id}` — 删除分类
- POST `/api/documents/tags` — 创建标签
- GET `/api/documents/tags` — 标签列表
- DELETE `/api/documents/tags/{tag_id}` — 删除标签
- POST `/api/documents/batch-operation` — 批量操作（分类/标签/状态）
- POST `/api/documents/search` — 文档搜索（关键词/组合条件）
- GET `/api/documents/advanced-search` — 高级搜索（Query 参数）
- GET `/api/documents/stats/overview` — 文档统计概览
- GET `/api/documents/vector-store/health` — 向量存储健康
- GET `/api/documents/vector-store/stats` — 向量存储统计
- GET `/api/documents/health` — 文档模块健康

请求要点：
- 上传：`UploadFile`，拒绝 `.xls`；服务端自动解析→分块→嵌入→入库
- 分类/标签：`name/description` 等；返回创建结果或列表
- 搜索：支持 `query`/`category`/`tags` 等过滤参数

---

## 管理后台（Admin，受 IP 白名单与认证保护）

### 仪表板（前缀 `/api/admin/dashboard`）
- GET `/overview` — 系统概览
- GET `/users` — 用户统计
- GET `/files` — 文件统计
- GET `/documents` — 文档统计
- GET `/health` — 系统健康
- GET `/activities` — 活动日志
- GET `/` — 完整仪表板数据

### 日志管理（前缀 `/api/admin/logs`）
- GET `/query` — 查询日志
- GET `/statistics` — 日志统计
- GET `/export` — 导出日志
- POST `/cleanup` — 清理日志
- GET `/tables` — 日志相关表
- POST `/test` — 日志系统自检

### 文件管理（前缀 `/api/admin/files`）
- POST `/upload` — 上传文件
- GET `/` — 列出文件
- GET `/{file_id}` — 文件详情
- GET `/{file_id}/download` — 下载文件
- PUT `/{file_id}` — 更新文件元数据
- DELETE `/{file_id}` — 删除文件
- POST `/batch-delete` — 批量删除
- GET `/stats/summary` — 文件统计

### 备份管理（前缀 `/api/admin/backup`）
- POST `/create` — 创建备份
- GET `/list` — 备份列表
- GET `/statistics` — 备份统计
- DELETE `/{backup_id}` — 删除备份
- POST `/restore` — 恢复备份
- GET `/download/{backup_id}` — 下载备份
- GET `/config` — 备份配置
- PUT `/config` — 更新备份配置
- POST `/schedule/start` — 启动备份计划
- POST `/schedule/stop` — 停止备份计划
- GET `/health` — 备份模块健康

### RAG 知识库管理（前缀 `/api/admin/rag`）
- POST `/documents` — 新增知识文档
- GET `/documents` — 知识文档列表
- GET `/documents/{document_id}` — 知识文档详情
- PUT `/documents/{document_id}` — 更新知识文档
- DELETE `/documents/{document_id}` — 删除知识文档
- GET `/documents/{document_id}/chunks` — 查看文档分块
- GET `/sessions` — 聊天会话列表
- GET `/sessions/{session_id}/messages` — 会话消息列表
- GET `/stats` — RAG 统计
- POST `/search` — 知识检索
- POST `/reprocess/{document_id}` — 重新处理文档

### 向量数据库管理（在主应用注册为前缀 `/api/admin/vector`）
- GET `/stats` — 向量库统计
- GET `/indexes` — 已建索引（如 `ivfflat/hnsw`）
- POST `/rebuild/{index_name}` — 重建索引
- DELETE `/clear/{index_name}` — 清空索引数据
- DELETE `/indexes/{index_name}` — 删除索引
- GET `/performance` — 性能数据
- POST `/performance/reset` — 重置性能统计

### 用户管理（前缀 `/api/admin/users`）
- POST `/register` — 管理员注册
- POST `/login` — 管理员登录
- GET `/me` — 当前管理员信息
- GET `/` — 分页查询用户
- GET `/{user_id}` — 获取用户
- PUT `/{user_id}` — 更新用户
- DELETE `/{user_id}` — 删除用户
- POST `/{user_id}/activate` — 激活用户
- POST `/{user_id}/deactivate` — 停用用户
- POST `/{user_id}/reset-password` — 重置密码

---

## 学习资源（前缀 `/api/study-resources`）

- GET `/` — 获取资源列表
- POST `/upload` — 上传资源
- POST `/admin/upload` — 管理员上传资源
- GET `/search` — 搜索资源
- GET `/admin/resources` — 管理员资源列表
- PUT `/admin/resource/{resource_id}` — 管理员更新资源
- DELETE `/admin/resource/{resource_id}` — 管理员删除资源
- POST `/admin/resources/batch-delete` — 管理员批量删除
- GET `/admin/scan-missing` — 巡检缺失文件
- POST `/admin/import-zip` — 管理员 ZIP 批量导入
- POST `/admin/category` — 管理员创建分类
- GET `/categories` — 分类列表
- GET `/resources` — 资源列表
- GET `/{resource_id}` — 资源详情
- GET `/{resource_id}/preview` — 预览资源
- GET `/{resource_id}/download` — 下载资源
- GET `/categories/list` — 分类列表
- POST `/categories` — 创建分类
- POST `/{resource_id}/rate` — 评分资源
- GET `/{resource_id}/ratings` — 获取评分
- POST `/{resource_id}/progress` — 更新进度
- DELETE `/{resource_id}` — 删除资源

---

## 用户 API（前缀 `/api/users`）

- GET `/profile` — 获取用户资料
- PUT `/profile` — 更新用户资料

---

## 测试中心（前缀 `/api/test`）

- GET `/summary` — 系统组件健康与汇总信息

---

## 请求示例（片段）

```json
// ChatRequest
{
  "messages": [
    { "role": "user", "content": "帮我查一下校园网使用教程" }
  ],
  "rag_enabled": true
}
```

```json
// QueryRequest
{ "query": "校园网连接步骤", "top_k": 8, "similarity_threshold": 0.35 }
```

```json
// TokenResponse（示意）
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 认证与安全说明

- 管理端路由（`/api/admin/*`）默认受“管理员 IP 白名单”保护，需在后端配置中启用或在开发模式放行。
- 部分模块启用 `HTTPBearer`，需要在 `Authorization: Bearer <token>` 中传入有效令牌。
- CORS：开发态允许 `http://localhost:5173,5174`；生产需限制为正式域名。

---

## 备注

- 本清单来源于以下文件自动汇总：
  - `backend/main.py` 路由注册
  - `backend/app/api/*` 路由实现
  - `backend/auth_routes.py` 认证模块
- 若新增/修改端点，请同步更新本清单或依赖 FastAPI 自带的 `/docs`。

