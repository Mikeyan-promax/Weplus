<#
函数：Invoke-WeplusSafeForcePush
作用：在 Windows 11 环境下一键执行“拉取→提交→安全强推→恢复安全远程”。
说明：
- 使用一次性令牌认证进行推送，不把令牌写入远程 URL 配置或提交历史；
- 推送后将远程地址恢复为不含令牌的安全 URL；
- 优先正常推送；当你显式选择“覆盖远程”时，使用 --force-with-lease 进行安全强推；
- 全过程输出中文提示，便于新手用户理解进度。
#>
param(
    [string]$RepoUrl = "https://github.com/Mikeyan-promax/Weplus.git",
    [string]$Branch = "main",
    [string]$CommitMessage = "chore: 上传当前工作区（覆盖远程）",
    [switch]$OverrideRemote
)

function Invoke-WeplusSafeForcePush {
    <#
    函数：Invoke-WeplusSafeForcePush
    作用：执行 Git 推送流程（拉取→提交→推送），并在需要时进行安全强推。
    参数：
    - $RepoUrl        远程仓库安全 URL（不含令牌）
    - $Branch         推送分支，默认 main
    - $CommitMessage  本次提交信息
    - $OverrideRemote 是否覆盖远程（安全强推 --force-with-lease）
    #>

    Write-Host "[1/6] 检查/初始化仓库并配置身份..." -ForegroundColor Cyan
    if (-not (Test-Path ".git")) {
        git init
        git config user.name "Mikeyan-promax"
        git config user.email "yanziling@stu.ouc.edu.cn"
    }

    git switch -C $Branch

    Write-Host "[2/6] 拉取远程最新（--rebase，忽略无远程或认证异常）..." -ForegroundColor Cyan
    try { git pull --rebase } catch { Write-Host "拉取失败（可能未设置远程或需认证），继续本地提交" -ForegroundColor Yellow }

    Write-Host "[3/6] 暂存与提交当前变更..." -ForegroundColor Cyan
    git add -A
    try {
        git commit -m $CommitMessage | Out-Null
        Write-Host "已提交：$CommitMessage" -ForegroundColor Green
    } catch {
        Write-Host "没有需要提交的更改（工作区干净），继续推送" -ForegroundColor Yellow
    }

    Write-Host "[4/6] 输入一次性 GitHub 令牌（PAT），不会保存到远程配置或提交历史）" -ForegroundColor Cyan
    $username = "Mikeyan-promax"
    $pat = Read-Host "请输入 GitHub PAT（将仅用于本次推送，不会保存）"
    if ([string]::IsNullOrWhiteSpace($pat)) { throw "未提供 PAT，无法推送" }
    $pushUrl = "https://$username:$pat@github.com/Mikeyan-promax/Weplus.git"

    $pushArgs = if ($OverrideRemote) { "--force-with-lease" } else { "" }
    Write-Host "[5/6] 推送到远程：$RepoUrl （$Branch）" -ForegroundColor Cyan
    if ($OverrideRemote) { Write-Host "本次为安全强推（--force-with-lease）" -ForegroundColor Yellow }

    git push -u $pushUrl $Branch $pushArgs

    Write-Host "[6/6] 恢复安全远程地址（不含令牌）..." -ForegroundColor Cyan
    git remote remove origin 2>$null
    git remote add origin $RepoUrl
    git remote -v
    Write-Host "全部完成：远程已恢复为安全 URL；可前往 GitHub 查看提交。" -ForegroundColor Green
}

# 入口：调用主流程
Invoke-WeplusSafeForcePush -RepoUrl $RepoUrl -Branch $Branch -CommitMessage $CommitMessage -OverrideRemote:$OverrideRemote

