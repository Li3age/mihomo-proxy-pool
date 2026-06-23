"""Entry point for proxy_pool. Run with: python -m proxy_pool"""

import argparse
import sys
from pathlib import Path


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
    from . import config as cfg_module

    app = create_app(proj_root)

    # Access config through the module after create_app has set it
    import proxy_pool.server as srv
    host = args.host or srv.config.server["host"]
    port = args.port or srv.config.server["port"]

    from proxy_pool.server import MIHOMO_PROXY_PORT

    print(f"\n  Proxy Pool: http://{host}:{port}")
    print(f"  Proxy Port: 127.0.0.1:{MIHOMO_PROXY_PORT} (SOCKS5 + HTTP)\n")

    app.run(host=host, port=port, debug=args.debug, use_reloader=False)


if __name__ == "__main__":
    main()
