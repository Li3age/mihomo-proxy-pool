[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
try {
    Write-Host "         fetching releases..."
    $releases = Invoke-RestMethod -Uri "https://api.github.com/repos/MetaCubeX/mihomo/releases?per_page=5" -TimeoutSec 15
    $url = $null; $name = $null
    foreach ($r in $releases) {
        if ($r.prerelease -eq $false -and $r.draft -eq $false) {
            foreach ($a in $r.assets) {
                if ($a.name -match "windows.*amd64.*compatible.*\.zip") {
                    $url = $a.browser_download_url; $name = $a.name; break
                }
            }
            if ($url) { break }
        }
    }
    if (-not $url) {
        foreach ($r in $releases) {
            foreach ($a in $r.assets) {
                if ($a.name -match "windows.*amd64.*compatible.*\.zip") {
                    $url = $a.browser_download_url; $name = $a.name; break
                }
            }
            if ($url) { break }
        }
    }
    if (-not $url) {
        Write-Host "[错误] 未找到合适的 release"
        Write-Host "https://github.com/MetaCubeX/mihomo/releases"
        exit 1
    }
    Write-Host ("        下载: " + $name)
    Invoke-WebRequest -Uri $url -OutFile "bin\mihomo.zip" -TimeoutSec 120
    Expand-Archive -Path "bin\mihomo.zip" -DestinationPath "bin\tmp" -Force
    $exe = Get-ChildItem -Path "bin\tmp" -Recurse -Filter "*.exe" | Select-Object -First 1
    if ($exe) {
        Move-Item -Path $exe.FullName -Destination "bin\mihomo.exe" -Force
    }
    Remove-Item -Recurse -Force "bin\tmp", "bin\mihomo.zip" -ErrorAction SilentlyContinue
    Write-Host "        下载完成"

    # Download MMDB files
    Write-Host "        下载 MMDB 数据库..."
    $root = Split-Path $PSScriptRoot -Parent
    $runtime = Join-Path $root "runtime"
    if (-not (Test-Path $runtime)) { New-Item -ItemType Directory $runtime -Force | Out-Null }
    $mmdbBase = "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest"
    $mmdbFiles = @("geoip.metadb", "geosite.dat", "country.mmdb")
    foreach ($f in $mmdbFiles) {
        $dest = Join-Path $runtime $f
        if (-not (Test-Path $dest)) {
            try {
                Invoke-WebRequest -Uri "$mmdbBase/$f" -OutFile $dest -TimeoutSec 60
                Write-Host ("          " + $f)
            } catch {
                Write-Host ("          [跳过] " + $f)
            }
        }
    }
} catch {
    Write-Host ("[错误] 下载失败: " + $_.Exception.Message)
    Write-Host "请手动从 https://github.com/MetaCubeX/mihomo/releases 下载"
    Write-Host "解压后将 .exe 放入 bin\ 目录，重命名为 mihomo.exe"
    exit 1
}