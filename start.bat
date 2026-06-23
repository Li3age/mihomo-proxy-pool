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
echo [1/5] 检查依赖...
pip show flask >nul 2>&1
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

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bin\download.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [提示] 自动下载失败，请手动下载:
    echo   https://github.com/MetaCubeX/mihomo/releases
    echo   搜索 windows-amd64-compatible，解压 .exe 放入 bin\mihomo.exe
    echo.
    pause
    exit /b 1
)

:skip_download
echo        就绪

:: ---- 配置订阅地址 ----
echo [3/5] 配置订阅地址...

python -c "import json; c=json.load(open('config.json', encoding='utf-8')); exit(0 if c.get('subscription_url') else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   ═══════════════════════════════════════
    echo    尚未配置订阅地址
    echo    请粘贴你的 Clash/Mihomo 订阅 URL：
    echo   ═══════════════════════════════════════
    echo.
    set /p INPUT_URL="  ^> "
    if not "!INPUT_URL!"=="" (
        python -c "import json; c=json.load(open('config.json', encoding='utf-8')); c['subscription_url']='!INPUT_URL!'; json.dump(c, open('config.json','w', encoding='utf-8'), indent=2, ensure_ascii=False)"
        echo   已保存
    ) else (
        echo   未输入，跳过
    )
    echo.
) else (
    echo        已配置
)

:: ---- 启动 ----
echo [4/5] 启动代理池...
echo.
echo   代理地址: 127.0.0.1:7892  (HTTP + SOCKS5)
echo   Web 面板: http://127.0.0.1:58080
echo   按 Ctrl+C 停止
echo   ===========================================
echo.

set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m proxy_pool %*
pause
