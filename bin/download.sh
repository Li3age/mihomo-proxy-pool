#!/usr/bin/env bash
# Auto-download mihomo binary from GitHub releases.
set -euo pipefail

DEST_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$DEST_DIR/mihomo"
REPO="MetaCubeX/mihomo"

echo "=== mihomo binary installer ==="

# ── already installed ──
if [ -f "$DEST" ]; then
    echo "Already installed: $("$DEST" -v 2>&1 | head -1)"
    exit 0
fi

# ── helper: find best asset from JSON ──
find_asset() {
    python3 -c "
import json, sys
data = json.load(sys.stdin)
# prefer non-prerelease
for r in data:
    if not r.get('prerelease') and not r.get('draft'):
        for a in r['assets']:
            name = a['name']
            if 'linux' in name and 'amd64' in name and 'compatible' in name and name.endswith('.gz'):
                print(a['browser_download_url'])
                print(name, file=sys.stderr)
                sys.exit(0)
# fallback to prerelease
for r in data:
    for a in r['assets']:
        name = a['name']
        if 'linux' in name and 'amd64' in name and 'compatible' in name and name.endswith('.gz'):
            print(a['browser_download_url'])
            print(name, file=sys.stderr)
            sys.exit(0)
print('', file=sys.stderr)
"
}

# ── download ──
echo "Fetching latest release from $REPO..."
RELEASES_JSON=$(curl -sL --max-time 15 "https://api.github.com/repos/$REPO/releases?per_page=5")

ASSET_URL=$(echo "$RELEASES_JSON" | find_asset 2>/tmp/mihomo_asset_name)
ASSET_NAME=$(cat /tmp/mihomo_asset_name)
rm -f /tmp/mihomo_asset_name

if [ -z "$ASSET_URL" ]; then
    echo "ERROR: Could not find a matching release."
    echo "Download manually from https://github.com/$REPO/releases"
    echo "Place the binary at: $DEST"
    exit 1
fi

echo "Downloading $ASSET_NAME ..."
curl -L --max-time 120 -o /tmp/mihomo.gz "$ASSET_URL"
gzip -d -f /tmp/mihomo.gz
mv /tmp/mihomo "$DEST"
chmod +x "$DEST"

echo "Installed ($(du -h "$DEST" | cut -f1))"
"$DEST" -v
