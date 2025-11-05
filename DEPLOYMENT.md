# WePlus 部署指南

## 环境变量配置

WePlus系统使用了两个AI模型：
1. **DeepSeek LLM模型** - 用于对话生成
2. **豆包嵌入模型** - 用于文本向量嵌入

### 环境变量设置

部署时，请确保在 `.env` 文件中正确配置以下环境变量：

#### 1. DeepSeek模型配置
```
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

#### 2. 豆包嵌入模型配置
```
ARK_API_KEY=your_ark_api_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_EMBEDDING_MODEL=doubao-embedding-text-240715
```

#### 3. 数据库配置
```
DATABASE_URL=postgresql://username:password@host:port/dbname
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

#### 4. 其他必要配置
请参考 `.env.example` 文件中的其他配置项，确保所有必要的环境变量都已正确设置。

## 部署步骤

1. 克隆代码库到服务器
2. 复制 `.env.example` 为 `.env` 并填入正确的配置值
3. 安装依赖：`pip install -r requirements.txt`
4. 初始化数据库：`python -m app.database.init_db`
5. 启动应用：`python -m app.main`

## 注意事项

- 确保两个模型的API密钥都已正确配置
- 确保数据库连接信息正确
- 在生产环境中，建议将 `DEBUG` 设置为 `False`
- 确保服务器防火墙允许应用端口的访问

## 学习资源文件存储（Railway 持久化）

为确保“学习资源”上传的文件在 Railway 上持久化保存，请配置以下环境变量并挂载持久化卷：

- 环境变量：
  - `STUDY_RESOURCES_DIR=/data/study_resources`
    - 后端会优先使用该目录保存和解析资源文件。

- Railway Volumes：
  - 在 Railway 项目中添加 Volume，并将其挂载到容器路径 `/data`
  - 后端会自动在 `/data/study_resources` 下创建子目录。

说明：
- 本地开发默认使用项目内 `backend/app/data/study_resources`。
- 生产（Railway）建议使用 `/data/study_resources`（持久化卷）。
- 预览/下载端点会在多个候选目录中回退查找（包含历史默认目录与 `STUDY_RESOURCES_DIR`），便于跨环境迁移。
