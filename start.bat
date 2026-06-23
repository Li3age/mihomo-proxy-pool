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
echo [1/4] 检查依赖...
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
echo [2/4] 检查 mihomo 二进制...
set "MIHOMO_BIN=bin\mihomo.exe"

if not exist "bin\" mkdir bin

if exist "%MIHOMO_BIN%" (
    echo        已安装: bin\mihomo.exe
    goto :skip_download
)

echo        正在从 GitHub 下载 mihomo ...
echo        这可能需要一两分钟，请耐心等待...

powershell -NoProfile -ExecutionPolicy Bypass -Command "
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
    # fetch releases
    \$releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/MetaCubeX/mihomo/releases?per_page=5' -TimeoutSec 15
    # find best asset
    \$url = \$null; \$name = \$null
    foreach (\$r in \$releases) {
        if (\$r.prerelease -eq \$false -and \$r.draft -eq \$false) {
            foreach (\$a in \$r.assets) {
                if (\$a.name -match 'windows.*amd64.*compatible.*\.zip') {
                    \$url = \$a.browser_download_url; \$name = \$a.name; break
                }
            }
            if (\$url) { break }
        }
    }
    if (-not \$url) {
        foreach (\$r in \$releases) {
            foreach (\$a in \$r.assets) {
                if (\$a.name -match 'windows.*amd64.*compatible.*\.zip') {
                    \$url = \$a.browser_download_url; \$name = \$a.name; break
                }
            }
            if (\$url) { break }
        }
    }
    if (-not \$url) {
        Write-Host '[错误] 未找到合适的 release，请手动下载'
        Write-Host 'https://github.com/MetaCubeX/mihomo/releases'
        exit 1
    }
    Write-Host ('        下载: ' + \$name)
    Invoke-WebRequest -Uri \$url -OutFile 'bin\mihomo.zip' -TimeoutSec 120
    Expand-Archive -Path 'bin\mihomo.zip' -DestinationPath 'bin\tmp' -Force
    # find the exe in extracted files
    \$exe = Get-ChildItem -Path 'bin\tmp' -Recurse -Filter '*.exe' | Select-Object -First 1
    if (\$exe) {
        Move-Item -Path \$exe.FullName -Destination 'bin\mihomo.exe' -Force
    }
    Remove-Item -Recurse -Force 'bin\tmp', 'bin\mihomo.zip' -ErrorAction SilentlyContinue
    Write-Host '        下载完成'
} catch {
    Write-Host ('[错误] 下载失败: ' + \$_.Exception.Message)
    Write-Host '请手动从 https://github.com/MetaCubeX/mihomo/releases 下载'
    Write-Host '解压后将 .exe 放入 bin\ 目录，重命名为 mihomo.exe'
    exit 1
}
" 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [提示] 自动下载失败，你可以:
    echo   1. 检查网络（可能需要代理）
    echo   2. 手动下载: https://github.com/MetaCubeX/mihomo/releases
    echo   3. 搜索 windows-amd64-compatible，解压 .exe 放入 bin\mihomo.exe
    echo.
    pause
    exit /b 1
)

:skip_download
echo        就绪

:: ---- 启动 ----
echo [3/4] 启动代理池...
echo.
echo   代理地址: 127.0.0.1:7892  (HTTP + SOCKS5)
echo   Web 面板: http://127.0.0.1:58080
echo   按 Ctrl+C 停止
echo   ===========================================
echo.

set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m proxy_pool %*
pause
