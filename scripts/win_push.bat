@echo off
setlocal enabledelayedexpansion

REM =========================================
REM 文件名：scripts/win_push.bat
REM 作用：一键执行 拉取→提交→推送（可选强推），遵循你的标准 Git 流程
REM 说明：本脚本使用 CMD 解析，命令以换行或 & 连接；不使用 ;;（;; 适用于 PowerShell）。
REM 参数：
REM   -m "提交说明"            设置本次提交信息，默认：update
REM   --force-with-lease        安全强推（推荐，仅在你明确要求覆盖时使用）
REM   --force                   绝对强推（不保留远程历史，慎用）
REM   -t <PAT>                  一次性使用令牌推送（令牌不会保存在远程 URL）
REM   --no-pull                 跳过 pull --rebase（无上游或你明确要求时）
REM   --branch <name>           目标分支，默认：main
REM   --repo <url>              远程仓库地址，默认：https://github.com/Mikeyan-promax/Weplus.git
REM   -h / --help               显示帮助
REM 用法示例：
REM   scripts\win_push.bat -m "更新说明" 
REM   scripts\win_push.bat -m "覆盖远程" --force-with-lease
REM   scripts\win_push.bat -m "用令牌推送一次" -t ghp_xxx --force-with-lease
REM =========================================

goto :main

REM =========================================
REM 函数：show_help
REM 作用：显示帮助与参数说明
REM =========================================
:show_help
  echo.
  echo [用法] win_push.bat [选项]
  echo   -m "提交说明"            设置本次提交信息，默认：update
  echo   --force-with-lease        安全强推（推荐，仅在你明确要求覆盖时使用）
  echo   --force                   绝对强推（不保留远程历史，慎用）
  echo   -t ^<PAT^>                一次性使用令牌推送（令牌不会保存在远程 URL）
  echo   --no-pull                 跳过 pull --rebase（无上游或你明确要求时）
  echo   --branch ^<name^>         目标分支，默认：main
  echo   --repo ^<url^>            远程仓库地址，默认：https://github.com/Mikeyan-promax/Weplus.git
  echo   -h / --help               显示帮助
  echo.
  echo [示例]
  echo   scripts\win_push.bat -m "更新说明"
  echo   scripts\win_push.bat -m "覆盖远程" --force-with-lease
  echo   scripts\win_push.bat -m "用令牌推送一次" -t ghp_xxx --force-with-lease
  echo.
  exit /b 0

REM =========================================
REM 函数：parse_args
REM 作用：解析命令行参数，设置变量
REM =========================================
:parse_args
  set COMMIT_MSG=update
  set FORCE_MODE=
  set USE_TOKEN=
  set SKIP_PULL=0
  set BRANCH=main
  set REPO_URL=https://github.com/Mikeyan-promax/Weplus.git
  set GIT_USER=Mikeyan-promax

  :parse_loop
    if "%~1"=="" goto :parse_done

    if /i "%~1"=="-m" (
      set COMMIT_MSG=%~2
      shift
      shift
      goto :parse_loop
    )
    if /i "%~1"=="--force-with-lease" (
      set FORCE_MODE=--force-with-lease
      shift
      goto :parse_loop
    )
    if /i "%~1"=="--force" (
      set FORCE_MODE=--force
      shift
      goto :parse_loop
    )
    if /i "%~1"=="-t" (
      set USE_TOKEN=%~2
      shift
      shift
      goto :parse_loop
    )
    if /i "%~1"=="--no-pull" (
      set SKIP_PULL=1
      shift
      goto :parse_loop
    )
    if /i "%~1"=="--branch" (
      set BRANCH=%~2
      shift
      shift
      goto :parse_loop
    )
    if /i "%~1"=="--repo" (
      set REPO_URL=%~2
      shift
      shift
      goto :parse_loop
    )
    if /i "%~1"=="-h" (
      call :show_help
      exit /b 0
    )
    if /i "%~1"=="--help" (
      call :show_help
      exit /b 0
    )
    echo 未知参数：%~1
    call :show_help
    exit /b 1

  :parse_done
  exit /b 0

REM =========================================
REM 函数：ensure_git
REM 作用：检测 Git 是否可用
REM =========================================
:ensure_git
  git --version >nul 2>&1
  if errorlevel 1 (
    echo 未检测到 Git；请安装 Git 后重试。
    exit /b 1
  )
  exit /b 0

REM =========================================
REM 函数：ensure_repo
REM 作用：检测当前目录是否是 Git 仓库；否则初始化
REM =========================================
:ensure_repo
  if not exist ".git" (
    echo 未检测到 .git，正在初始化仓库...
    git init
    if errorlevel 1 exit /b 1
  )
  exit /b 0

REM =========================================
REM 函数：ensure_identity
REM 作用：确保提交身份信息（user.name / user.email）存在
REM =========================================
:ensure_identity
  set CUR_NAME=
  set CUR_EMAIL=
  for /f "tokens=*" %%i in ('git config user.name 2^>nul') do set CUR_NAME=%%i
  for /f "tokens=*" %%i in ('git config user.email 2^>nul') do set CUR_EMAIL=%%i
  if "!CUR_NAME!"=="" (
    git config user.name "!GIT_USER!"
  )
  if "!CUR_EMAIL!"=="" (
    git config user.email "yanziling@stu.ouc.edu.cn"
  )
  exit /b 0

REM =========================================
REM 函数：ensure_remote
REM 作用：确保存在 origin 远程；如无则添加
REM =========================================
:ensure_remote
  set ORIGIN_URL=
  for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set ORIGIN_URL=%%i
  if "!ORIGIN_URL!"=="" (
    echo 未检测到 origin，正在添加：!REPO_URL!
    git remote add origin "!REPO_URL!"
    if errorlevel 1 exit /b 1
  ) else (
    echo 当前 origin：!ORIGIN_URL!
  )
  exit /b 0

REM =========================================
REM 函数：ensure_branch_main
REM 作用：确保当前分支为目标分支；若分离 HEAD 则创建/切换
REM =========================================
:ensure_branch_main
  set CUR_BRANCH=
  for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CUR_BRANCH=%%i
  if /i "!CUR_BRANCH!"=="HEAD" (
    echo 当前处于分离 HEAD，切换/创建分支：!BRANCH!
    git switch -C "!BRANCH!" >nul 2>&1
    if errorlevel 1 (
      git checkout -B "!BRANCH!"
      if errorlevel 1 exit /b 1
    )
  ) else (
    if /i "!CUR_BRANCH!" NEQ "!BRANCH!" (
      echo 切换分支到：!BRANCH!
      git switch "!BRANCH!" >nul 2>&1
      if errorlevel 1 (
        git checkout "!BRANCH!"
        if errorlevel 1 exit /b 1
      )
    )
  )
  exit /b 0

REM =========================================
REM 函数：ensure_tracking
REM 作用：检查是否存在上游分支；若不存在，在推送时建立
REM =========================================
:ensure_tracking
  git rev-parse --abbrev-ref --symbolic-full-name @{u} >nul 2>&1
  if errorlevel 1 (
    set HAS_UPSTREAM=0
    echo 尚未建立上游跟踪，将在推送时自动建立。
  ) else (
    set HAS_UPSTREAM=1
  )
  exit /b 0

REM =========================================
REM 函数：do_pull_rebase
REM 作用：在存在上游的情况下执行 git pull --rebase
REM =========================================
:do_pull_rebase
  if "!SKIP_PULL!"=="1" goto :skip_pull
  if "!HAS_UPSTREAM!"=="0" goto :skip_pull
  echo 拉取远程并变基...
  git pull --rebase
  if errorlevel 1 (
    echo 拉取/变基失败；请解决冲突后继续（git rebase --continue）。
    exit /b 1
  )
  :skip_pull
  exit /b 0

REM =========================================
REM 函数：do_commit
REM 作用：根据变更状态执行暂存与提交
REM =========================================
:do_commit
  git rev-parse --verify HEAD >nul 2>&1
  if errorlevel 1 (
    echo 首次提交，暂存并提交：!COMMIT_MSG!
    git add -A
    if errorlevel 1 exit /b 1
    git commit -m "!COMMIT_MSG!"
    if errorlevel 1 exit /b 1
    exit /b 0
  )

  git diff-index --quiet HEAD -- 2>nul
  if errorlevel 1 (
    echo 检测到变更，暂存并提交：!COMMIT_MSG!
    git add -A
    if errorlevel 1 exit /b 1
    git commit -m "!COMMIT_MSG!"
    if errorlevel 1 exit /b 1
  ) else (
    echo 无变更需要提交，跳过 commit。
  )
  exit /b 0

REM =========================================
REM 函数：do_push
REM 作用：执行推送；支持正常推送、with-lease 强推、绝对强推；支持一次性令牌 URL 推送
REM =========================================
:do_push
  if not "!USE_TOKEN!"=="" (
    set PUSH_URL=https://!GIT_USER!:!USE_TOKEN!@github.com/Mikeyan-promax/Weplus.git
    echo 使用一次性令牌推送（不会将令牌保存到远程 URL）...
    if "!FORCE_MODE!"=="" (
      git push -u "!PUSH_URL!" HEAD:!BRANCH!
    ) else (
      git push -u "!PUSH_URL!" HEAD:!BRANCH! !FORCE_MODE!
    )
    if errorlevel 1 exit /b 1
    echo 恢复安全远程 URL：!REPO_URL!
    git remote set-url origin "!REPO_URL!" >nul 2>&1
    exit /b 0
  )

  echo 推送到远程 origin/!BRANCH! ...
  if "!FORCE_MODE!"=="" (
    if "!HAS_UPSTREAM!"=="1" (
      git push
    ) else (
      git push -u origin "!BRANCH!"
    )
  ) else (
    git push -u origin "!BRANCH!" !FORCE_MODE!
  )
  if errorlevel 1 exit /b 1
  exit /b 0

REM =========================================
REM 函数：main
REM 作用：脚本主流程；按步骤执行 检查→拉取→提交→推送
REM =========================================
:main
  echo [win_push.bat] 开始执行推送流程...
  REM 切换到项目根目录（脚本位于 scripts/ 下）
  cd /d "%~dp0.."

  call :parse_args %*
  if errorlevel 1 exit /b 1

  call :ensure_git
  if errorlevel 1 exit /b 1

  call :ensure_repo
  if errorlevel 1 exit /b 1

  call :ensure_identity
  if errorlevel 1 exit /b 1

  call :ensure_remote
  if errorlevel 1 exit /b 1

  call :ensure_branch_main
  if errorlevel 1 exit /b 1

  call :ensure_tracking
  if errorlevel 1 exit /b 1

  call :do_pull_rebase
  if errorlevel 1 exit /b 1

  call :do_commit
  if errorlevel 1 exit /b 1

  call :do_push
  if errorlevel 1 exit /b 1

  echo 完成：本地分支 !BRANCH! 已推送到远程 origin/!BRANCH!。
  exit /b 0

