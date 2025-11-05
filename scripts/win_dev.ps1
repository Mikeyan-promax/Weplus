#
# WePlus 开发环境启动脚本（Windows / PowerShell）
# 作用：并行启动后端（uvicorn --reload）与前端（npm run dev）
# 使用：右键 PowerShell 运行或在终端执行 `powershell -ExecutionPolicy Bypass -File .\scripts\win_dev.ps1`

param(
    [string]$BackendDir = "c:\Users\MikeYan-PC\Desktop\weplus\backend",
    [string]$FrontendDir = "c:\Users\MikeYan-PC\Desktop\weplus\frontend2",
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000
)

# 函数：加载 .env 文件到当前进程环境变量（简单实现）
function Load-DotEnv {
    <#
    .SYNOPSIS
    加载 .env 文件，将键值对注入到当前进程环境变量中
    .PARAMETER Path
    .NOTES
    仅支持基本 KEY=VALUE 格式；忽略注释与空行
    #>
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        $kv = $line -split '=', 2
        if ($kv.Length -eq 2) {
            $key = $kv[0].Trim()
            $val = $kv[1].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $val)
        }
    }
}

# 函数：启动后端（热重载）
function Start-BackendDev {
    <#
    .SYNOPSIS
    启动 FastAPI 后端（热重载模式）
    .PARAMETER Dir
    后端代码所在目录
    .PARAMETER BindHost
    监听地址
    .PARAMETER Port
    监听端口
    #>
    param([string]$Dir, [string]$BindHost, [int]$Port)
    Write-Host "[DEV] 启动后端（热重载）: $Dir" -ForegroundColor Green
    Push-Location $Dir
    try {
        Load-DotEnv "$Dir\.env"
        Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","main:app","--host",$BindHost,"--port",$Port,"--reload" -NoNewWindow
    } finally {
        Pop-Location
    }
}

# 函数：启动前端（Vite dev server）
function Start-FrontendDev {
    <#
    .SYNOPSIS
    启动前端开发服务器（npm run dev）
    .PARAMETER Dir
    前端项目目录
    #>
    param([string]$Dir)
    if (-not (Test-Path $Dir)) { Write-Warning "前端目录不存在，跳过前端启动：$Dir"; return }
    Write-Host "[DEV] 启动前端开发服务器: $Dir" -ForegroundColor Green
    Push-Location $Dir
    try {
        Start-Process -FilePath "npm" -ArgumentList "run","dev" -NoNewWindow
    } finally {
        Pop-Location
    }
}

# 主流程：并行启动后端与前端
Write-Host "[DEV] 准备启动后端与前端（并行）" -ForegroundColor Cyan
Start-BackendDev -Dir $BackendDir -BindHost $BindHost -Port $Port
Start-FrontendDev -Dir $FrontendDir

Write-Host "[DEV] 已启动。可访问后端 http://localhost:$Port/ ，前端请查看终端输出地址。" -ForegroundColor Yellow
