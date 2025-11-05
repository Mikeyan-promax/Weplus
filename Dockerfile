## 统一前后端的单容器部署 Dockerfile（Railway 友好）
## 说明：
## - 前端：Node 多阶段构建，复制 dist 到 Nginx 静态目录
## - 后端：Python 多阶段构建，使用 Uvicorn 启动 FastAPI
## - 运行时：Alpine + python3 + nginx + supervisord，同容器内同时运行 Nginx 与 Uvicorn
## - 端口：容器监听 80，并通过 Nginx 反向代理 /api/

# === Frontend Build ===
FROM node:18-alpine AS frontend-build
WORKDIR /app
# 仅复制依赖清单加速缓存
COPY frontend2/package.json frontend2/package-lock.json* frontend2/pnpm-lock.yaml* /app/
RUN npm ci --silent || npm install --legacy-peer-deps --silent
# 复制源码并构建
COPY frontend2/ /app/
RUN npm run build

# === Backend Build ===
FROM python:3.11-slim AS backend-build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
# 安装构建所需系统依赖（cryptography 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    openssl \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt
COPY backend/ /app

# === Runtime ===
FROM python:3.11-slim AS runtime
WORKDIR /app
# 安装运行时进程管理与 Nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
  && rm -rf /var/lib/apt/lists/*

# 复制后端依赖与源码
COPY --from=backend-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=backend-build /app /app

# 复制前端构建产物到 Nginx 静态根目录
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# 复制运行时配置
COPY deploy/nginx.railway.conf /etc/nginx/nginx.conf
COPY deploy/supervisord.railway.conf /etc/supervisord.conf

# 缺省环境变量（避免解析报错，实际值建议在 Railway 仪表盘设置）
ENV PORT=80 \
    ENABLE_JSON_LOGGING="true" \
    PROMETHEUS_ENABLED="false" \
    SENTRY_DSN="" \
    ALLOWED_ORIGINS='["*"]' \
    ADMIN_IP_WHITELIST='[]'

# 暴露端口并通过 supervisord 同时启动后端与 Nginx
EXPOSE 80
CMD ["supervisord", "-c", "/etc/supervisord.conf"]

