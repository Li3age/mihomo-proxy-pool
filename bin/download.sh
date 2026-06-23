#!/usr/bin/env bash
# Download mihomo binary from GitHub releases or copy from existing installation.
set -euo pipefail

DEST_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$DEST_DIR/mihomo"
VERSION="${1:-latest}"

echo "=== mihomo binary installer ==="

# Option 1: copy from existing clash-for-linux
EXISTING="/home/li3age/clash-for-linux/runtime/bin/mihomo"
if [ -f "$EXISTING" ]; then
    echo "Found existing mihomo at $EXISTING"
    read -p "Copy from existing installation? [Y/n] " choice
    choice="${choice:-Y}"
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        cp "$EXISTING" "$DEST"
        chmod +x "$DEST"
        echo "Copied to $DEST ($(du -h "$DEST" | cut -f1))"
        "$DEST" -v
        exit 0
    fi
fi

# Option 2: download from GitHub
REPO="MetaCubeX/mihomo"
echo "Fetching latest release from $REPO..."

OS="linux"
ARCH="amd64"
# compatible build for wider glibc support
SUFFIX="compatible"

API_URL="https://api.github.com/repos/$REPO/releases"
if [ "$VERSION" = "latest" ]; then
    API_URL="$API_URL/latest"
else
    API_URL="$API_URL/tags/$VERSION"
fi

RELEASE_JSON=$(curl -sL "$API_URL")
ASSET_NAME=$(echo "$RELEASE_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for asset in data.get('assets', []):
    name = asset['name']
    if 'linux' in name and 'amd64' in name and 'compatible' in name and name.endswith('.gz'):
        print(name)
        break
")

if [ -z "$ASSET_NAME" ]; then
    echo "ERROR: Could not find a matching release asset."
    echo "Check https://github.com/$REPO/releases"
    exit 1
fi

DOWNLOAD_URL=$(echo "$RELEASE_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for asset in data['assets']:
    if asset['name'] == '$ASSET_NAME':
        print(asset['browser_download_url'])
        break
")

echo "Downloading $ASSET_NAME..."
curl -L -o /tmp/mihomo.gz "$DOWNLOAD_URL"
gzip -d -f /tmp/mihomo.gz
mv /tmp/mihomo "$DEST"
chmod +x "$DEST"

echo "Installed to $DEST ($(du -h "$DEST" | cut -f1))"
"$DEST" -v
