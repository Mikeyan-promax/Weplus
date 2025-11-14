## 结论与现象解释
- 根因：本地与 Railway 共用同一云数据库，但文件系统各自独立。上传时写入的是“当前环境磁盘路径”，另一端找不到该文件，所以预览/下载失败；删除是数据库层操作，因此两端都生效。
- 日志证据：后端打印“资源文件定位失败……返回候选=/data/study_resources/xxx.pdf”（backend/app/api/study_resources_api.py:200-215），说明另一端无法在本地磁盘找到对方上传的文件。
- 另一个性能问题：Railway Nginx日志显示“a client request body is buffered to a temporary file /var/lib/nginx/body/xxxx”，意味着大文件上传被 Nginx 缓冲到临时文件；再加上 Python 进程直接读取磁盘进行预览/下载，整体耗时较长。

## 快速成功方案（不引入外部对象存储）
目标：实现跨环境可预览/下载，并显著改善 Railway 预览/下载速度；改动小、部署快。

### 1. 统一外部访问 URL（优先使用 source_url 兜底）
- 上传时：在 Railway 后端将每个文件生成对外可访问的直链，并写入到 `source_url` 字段；另一端找不到本地文件时，直接重定向到 `source_url` 完成预览/下载（现代码已支持兜底重定向）。
- 具体实现：
  1) Nginx 映射静态文件目录 `/files/*` → `/data/study_resources/`（静态直出，绕过 Python 读盘）
     - 修改文件：`deploy/nginx.railway.conf`（或 `nginx.conf`）
     - 参考配置：
       ```nginx
       location /files/ {
         alias /data/study_resources/;
         add_header Cache-Control "public, max-age=604800";
         sendfile on;
         tcp_nopush on;
       }
       ```
  2) 上传接口（Railway环境）：保存文件后，给 `metadata.source_url` 写入 `https://weplus-production.up.railway.app/files/<唯一文件名>`
     - 代码位置：`backend/app/api/study_resources_api.py:502-520`（管理员上传）和 `414-427`（普通上传）
     - 写法：在 metadata 中加入 `source_url` 字段（现接口已包含 `source_url` 字段，直接赋值即可）
  3) 预览/下载：现代码在找不到本地文件时已优先重定向到 `source_url`（backend/app/api/study_resources_api.py:1328-1334、1373-1378）。无需前端改动。

### 2. 统一数据库字段写法（已完成）
- 与现有表结构完全一致：上传时写入 `file_name` 而不是不存在的 `original_filename`；读取时将 `name → title` 并严格构造数据类实例（已完成，文件：`backend/database/study_resources_models.py:339-370、396-473`）。

### 3. Railway 预览/下载性能优化
- 减少上传缓冲：在 Nginx 的 `/api` 反代配置中关闭请求体缓冲，将上传直接转发给 Uvicorn，提高吞吐；同时增加允许的上传大小。
  - 修改文件：`deploy/nginx.railway.conf`
  - 参考配置：
    ```nginx
    client_max_body_size 100m;
    client_body_buffer_size 128k;
    proxy_request_buffering off;  # 关闭请求体缓存，避免写入 /var/lib/nginx/body
    proxy_buffering on;
    ```
- 静态文件直出：通过 `/files/*` 静态直出，避免 Python Streaming 的额外开销；开启 `sendfile on` 与合理的 `Cache-Control`。
- 说明：日志中多次出现 4.25MB 级别流量（4459701 bytes）在多次预览/下载；静态直出能显著减少 CPU/IO 跳转，提高传输速度。

### 4. 本地环境的可用性
- 本地上传仍写入本地磁盘；另一端找不到时会自动重定向到 Railway 的 `source_url` 完成下载/预览。由此实现跨环境可用。
- 如需“本地也能提供公共直链”，可以在本地 Nginx 也映射 `/files/*` 到本地上传目录，并将本地 `source_url` 指向 `http://localhost:8000/files/<filename>`。

## 可选更优方案（对象存储，一次到位）
- 引入 S3/R2/OSS 等对象存储：上传写入对象存储，数据库保存 `file_name + source_url`（公共直链），彻底解决跨环境互通与静态资源传输性能问题，同时具备 CDN 可选。
- 改动点：在 `backend/app/api/study_resources_api.py` 增加 `STORAGE_MODE=local|s3` 开关，`s3` 模式走对象存储 SDK；失败时仍可回写本地并提供 `source_url` 兜底。
- 环境变量：`S3_ENDPOINT/S3_BUCKET/S3_ACCESS_KEY/S3_SECRET_KEY/S3_PUBLIC_BASE_URL`。

## 现有 RailWay 性能日志的解释
- `client request body is buffered to a temporary file /var/lib/nginx/body/…`：上传被 Nginx缓存到临时文件，导致 IO 较多、吞吐降低。关闭 `proxy_request_buffering` 可改善。
- 多次出现 `PostgreSQL连接池初始化成功`：说明服务每次请求时会打印连接池初始化日志；可以将初始化日志调至应用启动时打印一次，避免请求日志冗余（位置：`backend/postgresql_config.py` 或 `app/services/...`）。
- `增加下载次数失败 id=14: object int can't be used in 'await' expression`：这是在下载时异步计数逻辑与实际返回类型不一致导致（`await` 了一个同步返回的 int）。已在本地修正为严格映射的数据类构造方式，下一步我会把计数更新函数改成同步执行或确保内部使用异步方法，避免该警告。

## 我将实施的具体改动（确认后开始）
1) Railway Nginx：新增 `location /files/` 静态映射；在 `/api` 代理中关闭 `proxy_request_buffering` 并设定合理的 `client_max_body_size` 与 `client_body_buffer_size`。
2) 后端上传：当检测到运行在 Railway（或通过 `ENV=production`）时，自动设置 `metadata.source_url` 为 `https://weplus-production.up.railway.app/files/<唯一文件名>`。
3) 计数更新：将 `increment_view_count/increment_download_count` 的内部 DB 调用统一为同步或协程，移除“await int”的错误源。
4) 文档与部署指引：更新 `deploy/RAILWAY_部署指南.md`，记录 `/files` 映射与缓冲策略，以及必要的环境变量。

## 验证清单（我会在本地与Railway分别执行）
- 上传：本地/云端均上传成功，数据库写入 `file_name` 与 `source_url`（Railway）
- 预览/下载：
  - 本地找不到云端文件 → 自动跳转 `source_url` 成功预览
  - 云端找不到本地文件 → 自动跳转 `source_url` 成功预览
  - Railway 预览 4.5MB PDF：相较于 Python 直读有明显速度提升（静态直出）
- 删除：两端删除生效（数据库删除+文件删除），列表刷新正常

---
请确认采用“快速成功方案（source_url + /files 静态映射）”。确认后我将在本地实现上述改动，并进行完整验证，再等待你的最终“允许推送”指令后推送到 GitHub。