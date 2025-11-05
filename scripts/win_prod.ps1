#
# WePlus 生产运行脚本（Windows / PowerShell）
# 作用：以多进程（workers）方式启动后端，并加载 .env 环境变量
# 使用：`powershell -ExecutionPolicy Bypass -File .\scripts\win_prod.ps1 -Workers 4`

param(
    [string]$BackendDir = "c:\Users\MikeYan-PC\Desktop\weplus\backend",
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000,
    [int]$Workers = 4
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

# 函数：启动后端（多进程）
function Start-BackendProd {
    <#
    .SYNOPSIS
    启动 FastAPI 后端（多进程模式）
    .PARAMETER Dir
    后端代码所在目录
    .PARAMETER BindHost
    监听地址
    .PARAMETER Port
    监听端口
    .PARAMETER Workers
    进程数（建议=CPU核数或核数*2）
    #>
    param([string]$Dir, [string]$BindHost, [int]$Port, [int]$Workers)
    Write-Host "[PROD] 启动后端（workers=$Workers）: $Dir" -ForegroundColor Green
    Push-Location $Dir
    try {
        Load-DotEnv "$Dir\.env"
        # 注意：Windows 下 uvicorn 的 --workers 使用多进程（spawn），无需 gunicorn
        Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","main:app","--host",$BindHost,"--port",$Port,"--workers",$Workers -NoNewWindow
    } finally {
        Pop-Location
    }
}

# 主流程
Write-Host "[PROD] 准备启动后端（多进程）" -ForegroundColor Cyan
Start-BackendProd -Dir $BackendDir -BindHost $BindHost -Port $Port -Workers $Workers
Write-Host "[PROD] 已启动。请通过 Nginx 反代访问生产端点。健康检查：/healthz /readyz" -ForegroundColor Yellow
