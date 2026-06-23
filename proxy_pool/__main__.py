"""Entry point for proxy_pool. Run with: python -m proxy_pool"""

import argparse
import socket
import sys
from pathlib import Path


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def main():
    parser = argparse.ArgumentParser(
        description="mihomo-proxy-pool — rotating proxy pool on top of mihomo"
    )
    parser.add_argument(
        "-c", "--config", default="config.json", help="Path to project config (default: config.json)"
    )
    parser.add_argument(
        "--host", help="Override server host"
    )
    parser.add_argument(
        "-p", "--port", type=int, help="Override server port"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run Flask in debug mode"
    )
    args = parser.parse_args()

    proj_root = Path(args.config).resolve().parent

    from .server import create_app

    app = create_app(proj_root)

    import proxy_pool.server as srv
    host = args.host or srv.config.server["host"]
    port = args.port or srv.config.server["port"]

    from proxy_pool.server import MIHOMO_PROXY_PORT

    if _port_in_use(host, port):
        print(f"\n  !!! 端口 {port} 已被占用，请先释放:")
        print(f"      Linux: fuser -k {port}/tcp")
        print(f"      Windows: netstat -ano | findstr :{port}  然后 taskkill /PID xxx /F")
        print(f"      或使用其他端口: python -m proxy_pool -p {port + 1}\n")
        sys.exit(1)

    print(f"\n  Proxy Pool: http://{host}:{port}")
    print(f"  Proxy Port: 127.0.0.1:{MIHOMO_PROXY_PORT} (SOCKS5 + HTTP)\n")

    try:
        app.run(host=host, port=port, debug=args.debug, use_reloader=False)
    finally:
        # Only stop mihomo if we started it; atexit handles _stop_mihomo
        pass


if __name__ == "__main__":
    main()
