## 变更摘要
- 已更新 `frontend2/vite.config.ts` 将代理目标从 `http://127.0.0.1:8001` 改为 `http://127.0.0.1:8000`，并完成本地验证。

## 推送步骤
1) 查看仓库与分支状态
- 执行 `git status`、`git branch --show-current`、`git remote -v`，确认当前分支与远程 `origin`

2) 暂存并提交
- 执行 `git add frontend2/vite.config.ts`
- 执行 `git commit -m "chore(frontend): point Vite proxy to backend :8000"`

3) 推送到 GitHub
- 若已存在远程：执行 `git push origin <当前分支>`；如未设置上游，执行 `git push -u origin <当前分支>`
- 若未配置远程，将添加 `origin`：需要你的 GitHub 仓库 URL（例如 `https://github.com/<user>/<repo>.git`），然后 `git remote add origin <url>` 并进行推送

4) 验证
- 查看推送输出确认成功；必要时打开仓库页面核对提交是否到位

## 注意事项
- 若凭据提示，使用 GitHub PAT 或已登录凭据；Windows 会使用凭据管理器缓存
- 推送仅包含本次端口修复变更，不影响其他文件

## 验收标准
- GitHub 仓库出现新的提交，消息为上述 commit message
- 远程分支与本地分支同步，无错误提示