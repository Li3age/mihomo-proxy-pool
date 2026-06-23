$configPath = Join-Path $PSScriptRoot "..\config.json"
$config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

$current = $config.subscription_url

if ($current) {
    Write-Host ""
    Write-Host "  +-------------------------------------------+"
    Write-Host "  |  Current: $current"
    Write-Host "  +-------------------------------------------+"
    Write-Host ""
    Write-Host "  Press Enter to keep, or type a new URL"
} else {
    Write-Host ""
    Write-Host "  +-------------------------------------------+"
    Write-Host "  |  No subscription URL configured"
    Write-Host "  |  Paste your Clash/Mihomo subscription link"
    Write-Host "  +-------------------------------------------+"
    Write-Host ""
}

$input = Read-Host "  URL"
if ($input) {
    $config.subscription_url = $input
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    Write-Host ""
    Write-Host "  [OK] Saved"
    Write-Host ""
} elseif ($current) {
    Write-Host ""
    Write-Host "  [OK] Unchanged"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "  Skipped (can configure later at http://127.0.0.1:58080)"
    Write-Host ""
}