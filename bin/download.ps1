[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
try {
    # fetch releases
    $releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/MetaCubeX/mihomo/releases?per_page=5' -TimeoutSec 15
    # find best asset
    $url = $null; $name = $null
    foreach ($r in $releases) {
        if ($r.prerelease -eq $false -and $r.draft -eq $false) {
            foreach ($a in $r.assets) {
                if ($a.name -match 'windows.*amd64.*compatible.*\.zip') {
                    $url = $a.browser_download_url; $name = $a.name; break
                }
            }
            if ($url) { break }
        }
    }
    if (-not $url) {
        foreach ($r in $releases) {
            foreach ($a in $r.assets) {
                if ($a.name -match 'windows.*amd64.*compatible.*\.zip') {
                    $url = $a.browser_download_url; $name = $a.name; break
                }
            }
            if ($url) { break }
        }
    }
    if (-not $url) {
        Write-Host '[错误] 未找到合适的 release，请手动下载'
        Write-Host 'https://github.com/MetaCubeX/mihomo/releases'
        exit 1
    }
    Write-Host ('        下载: ' + $name)
    Invoke-WebRequest -Uri $url -OutFile 'bin\mihomo.zip' -TimeoutSec 120
    Expand-Archive -Path 'bin\mihomo.zip' -DestinationPath 'bin\tmp' -Force
    # find the exe in extracted files
    $exe = Get-ChildItem -Path 'bin\tmp' -Recurse -Filter '*.exe' | Select-Object -First 1
    if ($exe) {
        Move-Item -Path $exe.FullName -Destination 'bin\mihomo.exe' -Force
    }
    Remove-Item -Recurse -Force 'bin\tmp', 'bin\mihomo.zip' -ErrorAction SilentlyContinue
    Write-Host '        下载完成'
} catch {
    Write-Host ('[错误] 下载失败: ' + $_.Exception.Message)
    Write-Host '请手动从 https://github.com/MetaCubeX/mihomo/releases 下载'
    Write-Host '解压后将 .exe 放入 bin\ 目录，重命名为 mihomo.exe'
    exit 1
}
