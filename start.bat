  @echo off
  chcp 65001 >nul
  setlocal enabledelayedexpansion

  :: ============================================
  ::  mihomo-proxy-pool Windows 启动脚本
  :: ============================================

  cd /d "%~dp0"

  echo.
  echo   === mihomo-proxy-pool ===
  echo.

  :: ---- 检查 Python ----
  python --version >nul 2>&1
  if %errorlevel% neq 0 (
      echo [错误] 未找到 Python，请先安装 Python 3.10+
      echo         https://www.python.org/downloads/
      pause
      exit /b 1
  )

  :: ---- 安装依赖 ----
  echo [1/3] 检查依赖...
  pip show flask >nul 2>&1
  if %errorlevel% neq 0 (
      echo        正在安装 flask pyyaml ...
      pip install flask pyyaml -q
      if %errorlevel% neq 0 (
          echo [错误] 依赖安装失败
          pause
          exit /b 1
      )
  )
  echo        依赖就绪

  :: ---- 检查 mihomo 二进制 ----
  echo [2/3] 检查 mihomo 二进制...
  set "MIHOMO_BIN="
  if exist "bin\mihomo.exe" set "MIHOMO_BIN=bin\mihomo.exe"
  if exist "bin\mihomo-windows-amd64.exe" set "MIHOMO_BIN=bin\mihomo-windows-amd64.exe"

  if "!MIHOMO_BIN!"=="" (
      echo.
      echo [提示] 未找到 mihomo 二进制，请下载后放入 bin\ 目录:
      echo   https://github.com/MetaCubeX/mihomo/releases
      echo   搜索 mihomo-windows-amd64 开头的 .zip，解压出 .exe
      echo   重命名为 mihomo.exe 放入 bin\
      echo.
      pause
      exit /b 1
  )
  echo        !MIHOMO_BIN!

  :: ---- 启动 ----
  echo [3/3] 启动代理池...
  echo.
  echo   代理地址: 127.0.0.1:7892  (HTTP + SOCKS5)
  echo   Web 面板: http://127.0.0.1:58080
  echo   按 Ctrl+C 停止
  echo   ===========================================
  echo.

  set "PYTHONPATH=%~dp0;%PYTHONPATH%"
  python -m proxy_pool %*
  pause