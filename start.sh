#!/usr/bin/env bash
# Quick start script for mihomo-proxy-pool
set -euo pipefail

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required"
    exit 1
fi

# Check dependencies
python3 -c "import flask" 2>/dev/null || {
    echo "Installing dependencies..."
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null || \
    pip3 install -r requirements.txt
}

# Check/copy mihomo binary
if [ ! -f "bin/mihomo" ]; then
    echo "Mihomo binary not found. Running download script..."
    bash bin/download.sh
fi

export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

echo ""
echo "Starting mihomo-proxy-pool..."
python3 -m proxy_pool "$@"
