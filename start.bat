@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
::  mihomo-proxy-pool Windows 启动脚本
:: ============================================

cd /d "%~dp0"

echo/
echo   === mihomo-proxy-pool ===
echo/

:: ---- 检查 Python ----
python --version >$null 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ---- 安装依赖 ----
echo [1/5] 检查依赖...
pip show flask >$null 2>&1
if %errorlevel% neq 0 (
    echo        正在安装 flask pyyaml ...
    pip install flask pyyaml -q
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请手动执行: pip install flask pyyaml
        pause
        exit /b 1
    )
)
echo        依赖就绪

:: ---- 自动下载 mihomo ----
echo [2/5] 检查 mihomo 二进制...
set "MIHOMO_BIN=bin\mihomo.exe"

if not exist "bin" mkdir bin 2>nul

if exist "%MIHOMO_BIN%" (
    echo        已安装: bin\mihomo.exe
    goto :skip_download
)

echo        正在从 GitHub 下载 mihomo ...
echo        可能需要一两分钟，请耐心等待...

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bin\download.ps1"

if %errorlevel% neq 0 (
    echo/
    echo [提示] 自动下载失败，你可以:
    echo   1. 检查网络（可能需要代理）
    echo   2. 手动下载: https://github.com/MetaCubeX/mihomo/releases
    echo   3. 搜索 windows-amd64-compatible，解压 .exe 放入 bin\mihomo.exe
    echo/
    pause
    exit /b 1
)

:skip_download
echo        就绪

:: ---- 配置订阅地址 ----
echo [3/5] 配置订阅地址...
echo/
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bin\setup_subscription.ps1"

:: ---- 启动 ----
echo [4/5] 启动代理池...
echo/
echo   代理地址: 127.0.0.1:7892  (HTTP + SOCKS5)
echo   Web 面板: http://127.0.0.1:58080
echo   按 Ctrl+C 停止
echo   ===========================================
echo/

set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m proxy_pool %*
pause