#!/usr/bin/env bash
# Quick start script for mihomo-proxy-pool
set -euo pipefail

cd "$(dirname "$0")"

# ── Check Python ──
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required"
    exit 1
fi

# ── Install dependencies ──
python3 -c "import flask" 2>/dev/null || {
    echo "Installing dependencies..."
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null || \
    pip3 install -r requirements.txt
}

# ── Check/download mihomo binary ──
if [ ! -f "bin/mihomo" ]; then
    echo "Mihomo binary not found. Downloading..."
    bash bin/download.sh
fi

# ── Configure subscription URL ──
SUB_URL=$(python3 -c "import json; print(json.load(open('config.json')).get('subscription_url',''))")
if [ -z "$SUB_URL" ]; then
    echo ""
    echo "  ═══════════════════════════════════════"
    echo "   尚未配置订阅地址"
    echo "   请粘贴你的订阅 URL："
    echo "  ═══════════════════════════════════════"
    echo ""
    read -rp "  > " INPUT_URL
    if [ -n "$INPUT_URL" ]; then
        python3 -c "
import json
with open('config.json') as f:
    c = json.load(f)
c['subscription_url'] = '$INPUT_URL'
with open('config.json', 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)
"
        echo "  已保存"
    else
        echo "  未输入，跳过（可在 config.json 中手动设置）"
    fi
    echo ""
fi

export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

echo "Starting mihomo-proxy-pool..."
python3 -m proxy_pool "$@"
