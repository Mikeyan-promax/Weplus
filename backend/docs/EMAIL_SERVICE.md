# 邮件服务使用说明（EmailService）

## 概览
- 位置：`app/services/email_service.py`
- 职责：发送验证码邮件、验证与冷却时间管理；在开发模式下（`DEBUG=True`）不发信直接返回验证码。
- 初始化策略：惰性初始化，仅在第一次发送邮件时创建 `FastMail/ConnectionConfig`，避免应用启动阶段阻塞。

## 环境变量（.env）
- `MAIL_USERNAME`：SMTP 登录用户名（通常是邮箱账号）。
- `MAIL_PASSWORD`：SMTP 登录密码或授权码（不提交到仓库）。
- `MAIL_FROM`：发件人邮箱地址。
- `MAIL_FROM_NAME`：发件人显示名称（可选）。
- `MAIL_PORT`：SMTP 端口（示例：`465`）。
- `MAIL_SERVER`：SMTP 服务器地址（示例：`smtp.qq.com`）。
- `MAIL_STARTTLS`：`true/false`，是否启用 STARTTLS。
- `MAIL_SSL_TLS`：`true/false`，是否启用 SSL/TLS。

## 关键方法
- `ensure_mail_client()`：
  - 从环境变量构造 `ConnectionConfig`；
  - 验证必要配置项，缺失时抛出异常；
  - 只初始化一次，后续直接复用。
- `send_verification_code(email: str)`：
  - 生成 6 位验证码；
  - `DEBUG=True` 时不实际发信，直接返回验证码（用于本地调试）。
  - 生产模式下发送 HTML 模板邮件，并记录日志与错误。
- `verify_code(email: str, code: str)`：
  - 验证并清理过期验证码；
  - 冷却与失败次数管理，避免暴力尝试。

## 调试与常见问题
- 本地调试：在 `.env` 设置 `DEBUG=true`，调用 `send_verification_code` 将直接得到验证码；确认渲染的 HTML 模板是否正常。
- 发信失败：
  - 检查 SMTP 用户名/密码/端口/服务器；
  - `MAIL_SSL_TLS` 与 `MAIL_STARTTLS` 不要同时为 `true`（常见冲突）；
  - 部分邮箱需要开启“第三方客户端授权码”。
- 安全建议：
  - PAT/密码不写入代码与仓库；
  - 使用系统“凭据管理器”或 Git Credential Manager 保存。

## 参考
- `.env.example`：提供示例配置字段与说明。
- `app/core/config.py`：通用 Settings；邮件服务独立读取环境变量。

