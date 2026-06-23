# mihomo-proxy-pool

基于 [mihomo](https://github.com/MetaCubeX/mihomo) 制作的 **代理池**，附带 Web 管理面板。

## 特性

- **Web 面板** — 暗色主题仪表盘，监控和控制代理池
- **自动轮转** — 支持顺序轮转 (round-robin) 和随机 (random)，可配置间隔
- **节点健康** — 跳过离线节点，按延迟排序
- **订阅拉取** — 从订阅 URL 自动拉取节点，定期更新
- **独立实例** — 不干扰你日常使用的代理

## 快速开始

```bash
# 1. 安装 mihomo 二进制
bash bin/download.sh

# 2. 配置订阅 URL
#    编辑 config.json → 设置 "subscription_url"

# 3. 启动
bash start.sh
```

启动后打开 **http://127.0.0.1:58080**

代理地址: **127.0.0.1:7892** (HTTP + SOCKS5)

## 端口说明

| 端口 | 服务 |
|------|------|
| 7892 | HTTP + SOCKS5 代理 |
| 9092 | Mihomo REST API |
| 58080 | 代理池 Web 管理面板 |

## API

| 方法 | 路径 | 说明 |
|--------|------|------|
| GET | `/api/status` | 代理池状态（当前节点、策略、池大小） |
| GET | `/api/nodes` | 所有节点及延迟和存活状态 |
| POST | `/api/rotate` | 轮转到下一个代理节点 |
| POST | `/api/switch?name=...` | 切换到指定节点 |
| GET/PUT | `/api/settings` | 查看/更新轮转设置 |
| POST | `/api/auto-rotate` | 启动/停止自动轮转 |
| GET | `/api/history` | 轮转历史记录 |
| GET | `/api/health` | 健康检查 |

## 脚本调用示例

```bash
# 换 IP
curl -X POST http://127.0.0.1:58080/api/rotate

# 使用代理
curl -x http://127.0.0.1:7892 https://httpbin.org/ip
```

## License

MIT
