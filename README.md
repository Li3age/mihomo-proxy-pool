# mihomo-proxy-pool

Turn your [mihomo](https://github.com/MetaCubeX/mihomo) proxy into a **rotating proxy pool** with a Web GUI.

```
┌─────────────────────────────────────────┐
│  Web GUI (http://127.0.0.1:58080)       │
│  ┌──────┐ ┌──────┐ ┌──────────────┐    │
│  │ Node │ │Rotate│ │  Node Table  │    │
│  │ Card │ │Ctrls │ │              │    │
│  └──────┘ └──────┘ └──────────────┘    │
├─────────────────────────────────────────┤
│  proxy_pool (Python)                    │
│  Rotator → Mihomo REST API (:9091)     │
├─────────────────────────────────────────┤
│  mihomo (:7891 proxy, :9091 API)       │
│  mode: global, proxy-providers: sub    │
└─────────────────────────────────────────┘
```

## Features

- **Web GUI** — dark-themed dashboard to monitor and control the pool
- **Auto rotation** — round-robin or random, configurable interval
- **Node health** — skip dead nodes, sort by latency
- **Subscription-based** — auto-update nodes from your provider
- **Independent instance** — doesn't interfere with your daily proxy

## Quick Start

```bash
# 1. Install mihomo binary
bash bin/download.sh

# 2. Set your subscription URL
#    Edit config.json → set "subscription_url"

# 3. Start
bash start.sh
```

Then open **http://127.0.0.1:58080**

Proxy address: **127.0.0.1:7891** (HTTP + SOCKS5)

## Port Layout

| Port | Service |
|------|---------|
| 7891 | HTTP + SOCKS5 proxy |
| 9091 | Mihomo REST API |
| 58080 | Proxy Pool Web GUI |

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Pool status (current node, strategy, pool size) |
| GET | `/api/nodes` | All nodes with delay and health |
| POST | `/api/rotate` | Rotate to next proxy |
| POST | `/api/switch?name=...` | Switch to a specific node |
| GET/PUT | `/api/settings` | View/update rotation settings |
| POST | `/api/auto-rotate` | Start/stop auto rotation |
| GET | `/api/history` | Rotation history |
| GET | `/api/health` | Health check |

## Usage in scripts

```bash
# Rotate to a new IP
curl -X POST http://127.0.0.1:58080/api/rotate

# Use the proxy
curl -x http://127.0.0.1:7891 https://httpbin.org/ip
```

## License

MIT
