# WePlus（最简说明）

> 校园智能助手（前后端同仓），含 Railway 单容器部署。详细部署见 `deploy/RAILWAY_部署指南.md`。

## 目录结构（简要）
- `backend/` 后端 FastAPI 源码与依赖
- `frontend2/` 前端 React + Vite 源码
- `deploy/` 部署相关配置（Nginx、supervisord、检查脚本、清单）
  - `nginx.railway.conf.template` 单容器 Nginx 配置模板（运行时渲染监听 `$PORT`）
  - `supervisord.railway.conf` 同时启动 Uvicorn 与 Nginx
  - `checks/railway_post_deploy_check.py` 发布后联通检查脚本
  - `DEPLOYMENT_CHECKLIST.md` 生产就绪核对表
  - `RAILWAY_部署指南.md` Railway 详细部署手册
- `Dockerfile` 前后端统一单容器镜像构建
- `railway.json` Railway 构建与健康检查配置（`/api/healthz`）

## 部署入口
- Railway 部署手册：`deploy/RAILWAY_部署指南.md`
- 一次性巡检脚本：`python deploy/checks/railway_post_deploy_check.py --base-url https://<subdomain>.railway.app`

## 备注
- 健康检查端点：`/api/healthz`（与 `railway.json` 对齐）
- 生产务必设置环境变量：`SECRET_KEY`、`ALLOWED_ORIGINS`、`DATABASE_URL` 等
