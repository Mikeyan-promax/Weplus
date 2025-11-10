<#
 .SYNOPSIS
  代理感知的一键推送脚本（Win11）。

 .DESCRIPTION
  - 在使用 VPN/代理时，Git 通过 HTTPS(443) 推送可能出现 “Recv failure: Connection was reset”。
  - 本脚本提供系统化流程：检测连接 → 配置 Git 代理 → 拉取/推送 → 恢复环境。
  - 支持自定义代理端口，默认读取常见端口或环境变量。

 .USAGE
  - 直接运行：  .\scripts\win_push.ps1
  - 指定端口：  .\scripts\win_push.ps1 -HttpPort 7890 -SocksPort 7891
  - 仅配置代理不推送： .\scripts\win_push.ps1 -OnlyProxy

 .NOTES
  - 所有步骤包含中文函数级注释；适配 Win11；不修改远程 URL（除非你另行执行）。
  - 建议代理类型为 HTTP（如 Clash 的 7890），若你使用 SOCKS5，请按需启用。
#>

param(
  [int] $HttpPort = $env:HTTP_PROXY_PORT -as [int],
  [int] $SocksPort = $env:SOCKS_PROXY_PORT -as [int],
  [string] $CommitMsg = "chore: proxy-aware push",
  [switch] $OnlyProxy,
  [switch] $UseSocks,
  [switch] $UseOpenSSL
)

$ErrorActionPreference = 'Stop'

function Write-Info {
  param([string]$Msg)
  Write-Host ("[INFO] " + $Msg)
}

function Write-Warn {
  param([string]$Msg)
  Write-Host ("[WARN] " + $Msg) -ForegroundColor Yellow
}

function Write-Err {
  param([string]$Msg)
  Write-Host ("[ERR ] " + $Msg) -ForegroundColor Red
}

function Get-DefaultProxyPorts {
  <#
    .SYNOPSIS
      返回默认/推荐代理端口集合。
    .DESCRIPTION
      - 常见代理端口：HTTP 7890，SOCKS5 7891（以 Clash 默认为例）。
      - 若调用者已传入端口，则优先使用调用者提供的端口。
  #>
  $http = if ($HttpPort -gt 0) { $HttpPort } else { 7890 }
  $socks = if ($SocksPort -gt 0) { $SocksPort } else { 7891 }
  return @{ Http=$http; Socks=$socks }
}

function Test-GitHub443 {
  <#
    .SYNOPSIS
      测试到 GitHub 443 端口的连通性。
    .DESCRIPTION
      - 使用 Test-NetConnection 检测 TCP 443 端口可达性；
      - 若网络层无阻塞但应用层握手失败，仍需代理配置配合。
    .OUTPUTS
      [bool]：true 表示端口可达；false 表示不可达。
  #>
  try {
    $r = Test-NetConnection github.com -Port 443 -WarningAction SilentlyContinue
    if ($r -and $r.TcpTestSucceeded) { return $true }
    return $false
  } catch { return $false }
}

function Set-GitProxy {
  <#
    .SYNOPSIS
      配置 Git 的 HTTP/HTTPS 代理。
    .DESCRIPTION
      - 对 HTTPS 推送，通常设置 https.proxy 为 http://127.0.0.1:PORT 即可（代理会通过 CONNECT 处理 TLS）。
      - 如你的代理是 SOCKS5，启用 -UseSocks 并设置为 socks5://127.0.0.1:PORT。
      - 可选：切换 SSL 后端为 OpenSSL，以提升与部分代理的兼容性。
  #>
  param(
    [int] $HttpPort,
    [int] $SocksPort,
    [switch] $UseSocks,
    [switch] $UseOpenSSL
  )

  if ($UseSocks) {
    $httpUri = "socks5://127.0.0.1:$SocksPort"
    $httpsUri = "socks5://127.0.0.1:$SocksPort"
  } else {
    $httpUri = "http://127.0.0.1:$HttpPort"
    $httpsUri = "http://127.0.0.1:$HttpPort"
  }

  Write-Info "配置 Git 代理：http.proxy=$httpUri ;; https.proxy=$httpsUri"
  git config --global http.proxy $httpUri
  git config --global https.proxy $httpsUri

  if ($UseOpenSSL) {
    Write-Info "切换 SSL Backend 到 OpenSSL（可提升部分代理兼容性）"
    git config --global http.sslBackend "openssl"
  }

  Write-Info ("当前 http.proxy=" + (git config --global --get http.proxy))
  Write-Info ("当前 https.proxy=" + (git config --global --get https.proxy))
}

function Clear-GitProxy {
  <#
    .SYNOPSIS
      清理 Git 的代理设置。
    .DESCRIPTION
      - 取消 http.proxy 与 https.proxy，恢复为直连；
      - 保持其他设置不变。
  #>
  Write-Info "清理 Git 代理配置"
  git config --global --unset http.proxy 2>$null
  git config --global --unset https.proxy 2>$null
}

function Push-WithLease {
  <#
    .SYNOPSIS
      执行一次规范的拉取/推送流程。
    .DESCRIPTION
      - 线性化历史：git pull --rebase
      - 提交变更：git add -A ;; git commit -m "..."（若无变更将跳过）
      - 推送：git push（已建立跟踪关系即可）
      - 如你需要覆盖推送，请手动在终端执行：git push -u origin main --force-with-lease
  #>
  param([string] $CommitMsg)

  Write-Info "开始拉取远程（rebase）"
  git pull --rebase

  try {
    Write-Info "尝试提交变更：$CommitMsg"
    git add -A
    git commit -m $CommitMsg
  } catch {
    Write-Warn "提交阶段：可能无文件变更或已提交，忽略错误并继续"
  }

  Write-Info "推送到远程（正常推送）"
  git push
}

function Main {
  <#
    .SYNOPSIS
      主流程：检测 → 配置代理 → 推送 → 恢复。
    .DESCRIPTION
      - 若 443 端口不可达或你指定了代理，则启用代理；
      - 执行标准推送；
      - 最终清理代理设置（除非你使用 -OnlyProxy）。
  #>
  $ports = Get-DefaultProxyPorts
  $httpP = $ports.Http
  $socksP = $ports.Socks

  Write-Info "检测到代理端口：HTTP=$httpP ;; SOCKS=$socksP"
  $ok443 = Test-GitHub443
  if (-not $ok443) { Write-Warn "到 github.com:443 端口连通性不佳，建议启用代理" }

  Set-GitProxy -HttpPort $httpP -SocksPort $socksP -UseSocks:$UseSocks -UseOpenSSL:$UseOpenSSL
  if ($OnlyProxy) { Write-Info "仅配置代理已完成；不执行推送"; return }

  try {
    Push-WithLease -CommitMsg $CommitMsg
  } finally {
    # 推送完成后恢复环境，避免代理影响其他场景
    Clear-GitProxy
  }
}

try {
  Main
  Write-Info "流程完成：已执行代理配置与推送，并恢复环境"
} catch {
  Write-Err ("执行失败：" + $_.Exception.Message)
  throw
}

