$configPath = Join-Path $PSScriptRoot "..\config.json"
$config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

$current = $config.subscription_url
if ($current) {
    Write-Host "        当前订阅: $current"
    Write-Host "        回车保持不变，输入新地址则更新"
} else {
    Write-Host "        尚未配置订阅地址"
    Write-Host "        请输入订阅链接（可从机场/代理服务商获取）"
}

$input = Read-Host "        订阅地址"
if ($input) {
    $config.subscription_url = $input
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    Write-Host "        已保存"
} elseif ($current) {
    Write-Host "        保持不变"
} else {
    Write-Host "        跳过（代理池将为空，可通过 Web 面板 http://127.0.0.1:58080 配置）"
}