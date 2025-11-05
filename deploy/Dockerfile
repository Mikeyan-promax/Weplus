## 后端服务 Dockerfile（多阶段构建）
## 说明：
## - 使用 python:3.11-slim 作为基础镜像
## - 先安装依赖，再复制源码，减小镜像层变动
## - 运行命令默认使用 uvicorn 暴露 8000 端口

FROM python:3.11-slim AS base

# 基础环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统依赖安装已临时禁用（Debian 源 502）；如需编译特定库可后续按需开启

# 先复制并安装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# 再复制源码
COPY . /app

# 暴露端口
EXPOSE 8000

# 默认启动命令（可在 docker-compose 中覆盖）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

