# 生产就绪清单（WePlus 后端）

面向运维与开发的部署核对表，逐项完成后再上线。

## 环境与基础设施
- 已安装并可用：`Docker`、`Docker Compose`、`Nginx`（或云负载均衡）
- 域名已解析到服务器 IP，并通过 80/443 端口对外开放
- 服务器时间与时区正确，`NTP` 同步正常
- 备份策略明确：数据库与应用数据目录每日/每周备份

## 配置与密钥
- `.env` 已配置并放置到安全位置（示例见 `deploy/.env.sample`）
- `SENTRY_DSN`（可选）已填入，采样率与隐私策略已评估
- `ADMIN_IP_WHITELIST` 已按需填写（生产环境务必限制来源）
- `CORS_ALLOW_ORIGINS` 白名单已核对，防止任意来源
- 任何密钥或凭证不进入代码仓库（使用环境变量或密钥管理）

## 日志与可观测性
- JSON 日志已启用，`LOG_JSON_ENABLED=true`
- Prometheus 指标（可选）已启用：`PROMETHEUS_ENABLED=true`，并通过 `/metrics` 暴露
- 请求 ID 中间件已启用，可在日志中跟踪请求
- Sentry SDK（如启用）能够正常上报错误事件

## 安全与网络
- Nginx 已配置 HTTPS 证书（`/etc/nginx/certs`），访问强制跳转 HTTPS
- 安全响应头（HSTS/X-Frame-Options/NoSniff 等）已开启
- 防火墙与安全组规则：对外仅开放 80/443；后端容器端口不对外暴露
- 管理端路由已启用 IP 白名单依赖，越权访问会被拒绝

## 数据与数据库
- 数据库连接字符串正确，账号权限最小化（只授予必要权限）
- 已执行最新迁移（包含日志索引：`backend/database/migrations/20251105_add_log_indexes.sql`）
- 监控数据库连接与慢查询（按需接入 APM 或数据库监控）

## 部署与回滚
- `docker-compose` 编排已配置（见 `deploy/docker-compose.yml`）
- `nginx.conf` 已部署并生效（检查 `nginx -t` 与重载）
- 灰度与回滚方案明确（镜像版本、Compose 回滚、备份恢复）
- 健康检查：`/healthz` 与 `/readyz` 返回正常

## 运行与维护
- 后端运行参数（如 `UVICORN_WORKERS`）已根据机器核数设定
- 定期轮转日志与清理策略明确（磁盘空间预警）
- Sentry 报警规则与 Prometheus 告警规则已设定（如 CPU/内存/错误率）

---

完成以上检查后，再进行生产上线与对外开放访问。

