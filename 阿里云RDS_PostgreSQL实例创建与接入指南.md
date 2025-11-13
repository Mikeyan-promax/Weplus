# 阿里云 RDS PostgreSQL 实例创建与接入指南（WePlus 项目）

> 说明：本文由 GPT-5-high 深度思考模式生成，面向 Windows 11 开发环境，详细指导你在阿里云控制台创建一个与现有配置一致的 RDS PostgreSQL 实例，并安全接入到本项目。所有命令示例均为 PowerShell，多个命令使用 `;;` 连接。

## 适用范围与目标
- 适用对象：阿里云 RDS 新手或需要复现既有配置的使用者。
- 目标：在阿里云控制台创建并配置 PostgreSQL 实例 → 打通本地连接 → 安装必要扩展 → 初始化 WePlus 项目数据结构 → 本地验证。
- 安全原则：不在 URL 中保存令牌；使用白名单与（可选）SSL；推送代码前先在本地确认。

## 前置检查清单
- 阿里云账号：具备 RDS PostgreSQL 创建权限与计费额度。
- 版本与扩展：建议 PostgreSQL 14/15，并支持 `vector`（pgvector）与 `uuid-ossp` 扩展。
- 网络：确定使用的 `VPC` 与 `交换机（vSwitch）`，准备添加本地公网 IP 至白名单（或通过堡垒机/VPN）。
- 项目需求：WePlus 使用豆包嵌入模型（2560维），需将数据库向量列统一为 `vector(2560)`。

## 步骤一：在阿里云控制台创建 RDS PostgreSQL 实例
- 登录：https://rds.console.aliyun.com/
- 选择：左侧“实例列表” → “创建实例”。
- 关键参数：
  - 计费模式：按量付费或包年包月（开发测试推荐按量）。
  - 数据库类型与版本：`PostgreSQL`，建议 `14` 或 `15`（确认支持 pgvector）。
  - 可用区与部署：单可用区或多可用区（高可用更稳）。
  - 规格与存储：根据并发与数据量选择 CPU/内存；存储类型（ESSD）与容量可按需扩容。
  - 网络：`VPC` 与 `vSwitch`（建议与应用服务同一 VPC）。
  - 安全：开启白名单；如需更安全，后续启用 `SSL`（若实例支持）。
- 创建完成后，进入实例详情页，记录：
  - `内网/公网地址（Endpoint）`、`端口（默认 5432）`、`实例 ID`、`VPC` 信息。

## 步骤二：配置网络访问与安全
- 白名单：实例详情 → “**数据安全性**/白名单” → 添加你的本地公网 IP（形如 `x.x.x.x`），确保可访问 `5432`。
- 安全组（若涉及 ECS 同网访问）：在 VPC 中放行 ECS 到 RDS 的入站规则。
- SSL（可选但推荐）：如果实例支持 SSL，在“连接信息”处启用，通过 `DATABASE_URL` 加 `?sslmode=require`。

## 步骤三：创建数据库与用户（DMS 或 psql）
- 打开 DMS（数据管理）：实例详情 → “**数据库连接**/SQL 控制台（DMS）”。
- 创建数据库与用户（示例 SQL）：
  ```sql
  -- 登录为具有创建权限的账号后执行
  CREATE DATABASE weplus_main ENCODING 'UTF8';

  -- 创建业务用户（示例名，可自定）
  CREATE USER weplus_user WITH PASSWORD '强密码请自定';

  -- 授权：连接数据库 + 创建/操作对象
  GRANT ALL PRIVILEGES ON DATABASE weplus_main TO weplus_user;
  ```
- 验证连接（PowerShell，如你安装了 `psql`）：
  ```powershell
  psql "host=<你的RDS地址> port=5432 dbname=weplus_main user=weplus_user password=<你的密码> sslmode=require"
  ```

## 步骤四：安装扩展与初始化（pgvector、uuid-ossp）
- 在 DMS 的 SQL 窗口，切换到 `weplus_main`，执行：
  ```sql
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- 维度一致性（WePlus 规范）：
  - WePlus 使用豆包 `doubao-embedding-text-240715` 的向量维度 `2560`。
  - 初始化脚本 `backend/database/postgresql_complete_schema.sql` 默认 `vector(1536)`，请在首次初始化前改为 `vector(2560)`，避免写入报错。

## 步骤五：本地项目接入与验证（Windows 11）
- 更新项目环境变量（`backend/.env`）：
  ```ini
  DB_HOST=<你的RDS地址>
  DB_PORT=5432
  DB_NAME=weplus_main
  DB_USER=weplus_user
  DB_PASSWORD=<你的密码>
  # 可选：优先使用统一 URL（如启用 SSL）
  # DATABASE_URL=postgresql://weplus_user:<你的密码>@<你的RDS地址>:5432/weplus_main?sslmode=require

  # WePlus RAG 关键参数
  VECTOR_DIMENSION=2560
  ```
- 首次启动与自动建表：
  - 后端在启动事件会检测表是否缺失；若缺失，会自动执行 `database/postgresql_complete_schema.sql`（已修改为 `vector(2560)`）。
- 连接与扩展自检（项目内置脚本）：
  ```powershell
  cd backend ;; python .\final_system_test.py
  ```
  - 期望输出：PostgreSQL 版本成功、关键表存在、`pgvector` 扩展已安装。

## WePlus 项目对齐与注意事项
- 维度统一：
  - 服务层：`app/services/postgresql_vector_service.py` 使用 `embedding_dimension=2560`。
  - Schema：`document_chunks.embedding vector(2560)`。
  - 环境：`.env` 建议设 `VECTOR_DIMENSION=2560`。
- 清理硬编码：
  - 旧 RDS 地址可能出现在 `database/simple_init.py`、`database/study_resources_models.py` 中；实际接入请以 `.env` 为准。
- 推送到 GitHub：
  - 按你的默认流程：`git pull --rebase` → 提交 → 正常 `git push`；仅在你明确要求时使用 `--force-with-lease` 覆盖远程。

## 面板组件与问题诊断（#problems_and_diagnostics）
- 常用面板组件（实例详情页）：
  - `基本信息`：版本、规格、端口、内网/公网地址。
  - `连接信息/白名单`：IP 白名单、SSL 配置、连接示例。
  - `数据库账号`：创建/管理账号与权限。
  - `数据库列表`：当前实例已创建的数据库。
  - `SQL 控制台（DMS）`：在线执行 SQL、导入导出、结果查看。
  - `参数设置`：PostgreSQL 参数（如内存、并发限制等）。
  - `备份与恢复`：自动备份策略与手动备份、基于时间点恢复。
  - `监控与报警`：CPU、连接数、慢查询、磁盘使用等可视化图表。
  - `日志审计`：审计日志与慢查询分析。
  - `安全性`：白名单、SSL、审计、密钥管理。
- 高频问题与处理：
  - 无法连接：检查白名单是否添加本地公网 IP；确认端口 `5432`；是否启用 SSL 且本地连接字符串包含 `sslmode`。
  - 扩展安装失败：检查 RDS 版本是否支持 `vector`；若受限请联系阿里云工单或升级版本。
  - 向量写入报错（维度不一致）：确认列类型为 `vector(2560)`，服务层与 `.env` 维度一致。
  - 权限不足：确保业务用户对目标数据库拥有必要权限（`CONNECT/CREATE/USAGE/INSERT/SELECT/UPDATE/DELETE`）。
  - 性能瓶颈：提升规格或开启索引（必要时考虑 `IVFFlat/HNSW`），优化连接池与查询。

## 附录：常用命令与操作
- 本地一键正常推送（Windows `;;` 连接）：
  ```powershell
  git add -A ;; git commit -m "update" ;; git pull --rebase ;; git push
  ```
- 安全强推（仅在你明确要求覆盖远程时）：
  ```powershell
  git add -A ;; git commit -m "override remote with local state" ;; git push -u origin main --force-with-lease
  ```
- DMS/SQL 校验扩展：
  ```sql
  SELECT extname FROM pg_extension WHERE extname IN ('vector','uuid-ossp');
  ```
- 校验关键表是否存在：
  ```sql
  SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('documents','document_chunks','users','categories');
  ```

---

如需我为你统一修改 `postgresql_complete_schema.sql` 的向量列为 `vector(2560)`、清理硬编码并在本地验证后再按你的推送流程提交，请直接回复新的 RDS 连接信息（地址、端口、数据库名、用户名、密码、是否 `sslmode=require`）。我会在本地完成变更与验证，确认无误后再推送。
