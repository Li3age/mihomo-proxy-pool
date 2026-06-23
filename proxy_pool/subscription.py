"""Fetch and parse mihomo/clash subscriptions."""

import logging
import urllib.request
import urllib.error
import ssl
import yaml
import os

log = logging.getLogger(__name__)


def fetch_subscription(url: str, proxy: str = "", timeout: int = 15, insecure: bool = False) -> str:
    """Fetch subscription content via optional proxy. Returns raw YAML text."""
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    handlers.append(urllib.request.HTTPSHandler(context=ctx))
    opener = urllib.request.build_opener(*handlers)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "clash-verge/1.0"},
        )
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            log.info("Fetched subscription: %d bytes", len(raw))
            return raw
    except Exception as e:
        log.warning("Failed to fetch subscription: %s", e)
        raise


def parse_proxies(raw_yaml: str) -> list[dict]:
    """Parse clash config YAML and extract proxy nodes."""
    data = yaml.safe_load(raw_yaml)
    if not data:
        return []

    proxies = data.get("proxies", [])
    if not proxies:
        log.warning("No proxies found in subscription")
        return []

    valid_types = {"vmess", "vless", "trojan", "ss", "ssr", "hysteria", "hysteria2", "tuic", "http", "socks5"}
    result = []
    seen = set()

    for p in proxies:
        if not isinstance(p, dict):
            continue
        name = p.get("name", "")
        ptype = p.get("type", "")
        if ptype not in valid_types:
            continue
        if name in seen:
            continue
        seen.add(name)
        result.append(p)

    log.info("Parsed %d proxies from subscription", len(result))
    return result


def generate_runtime_config(template_path: str, proxies: list[dict]) -> str:
    """Insert inline proxies into the config template."""
    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    # Build proxy name list for the ProxyPool group
    proxy_names = [p["name"] for p in proxies]

    # Format proxies as YAML
    import io
    buf = io.StringIO()

    # Write proxies inline
    buf.write("proxies:\n")
    for p in proxies:
        _write_proxy(buf, p, indent=2)

    # Update proxy-groups with actual proxy names
    content = content.replace("proxies: []", buf.getvalue().rstrip())

    # Replace ProxyPool group's proxies list
    old_group = "    proxies:\n      - DIRECT"
    new_group_proxies = "    proxies:\n"
    for name in proxy_names:
        new_group_proxies += f"      - {yaml_dump_str(name)}\n"
    if not proxy_names:
        new_group_proxies += "      - DIRECT\n"

    content = content.replace(old_group, new_group_proxies.rstrip())

    return content


def _write_proxy(buf, p: dict, indent: int = 0):
    """Write a single proxy entry in Clash YAML format."""
    prefix = " " * indent
    buf.write(f"{prefix}- name: {yaml_dump_str(p.get('name', ''))}\n")
    buf.write(f"{prefix}  type: {p.get('type', '')}\n")
    buf.write(f"{prefix}  server: {p.get('server', '')}\n")
    buf.write(f"{prefix}  port: {p.get('port', 0)}\n")

    for field in ["uuid", "password", "cipher", "alterId", "udp", "network",
                   "sni", "alpn", "skip-cert-verify", "tls", "servername",
                   "client-fingerprint", "up", "down", "auth", "auth-str",
                   "obfs", "obfs-password", "protocol", "protocol-param"]:
        val = p.get(field)
        if val is not None:
            if isinstance(val, bool):
                buf.write(f"{prefix}  {field}: {str(val).lower()}\n")
            elif isinstance(val, str):
                buf.write(f"{prefix}  {field}: {yaml_dump_str(val)}\n")
            else:
                buf.write(f"{prefix}  {field}: {val}\n")

    # nested objects
    for nested_field in ["ws-opts", "ws-path", "ws-headers", "grpc-opts",
                           "hysteria-opts", "hysteria2-opts", "tuic-opts",
                           "smux", "plugin", "plugin-opts", "reality-opts"]:
        val = p.get(nested_field)
        if val is not None:
            if isinstance(val, dict):
                buf.write(f"{prefix}  {nested_field}:\n")
                _write_dict(buf, val, indent + 4)
            else:
                buf.write(f"{prefix}  {nested_field}: {yaml_dump_str(str(val))}\n")


def _write_dict(buf, d: dict, indent: int):
    """Write a flat dict in YAML style."""
    prefix = " " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            buf.write(f"{prefix}{k}:\n")
            _write_dict(buf, v, indent + 2)
        elif isinstance(v, bool):
            buf.write(f"{prefix}{k}: {str(v).lower()}\n")
        elif isinstance(v, str):
            buf.write(f"{prefix}{k}: {yaml_dump_str(v)}\n")
        else:
            buf.write(f"{prefix}{k}: {v}\n")


def yaml_dump_str(s: str) -> str:
    """Safely quote a string for YAML inline use."""
    if any(c in s for c in ['"', "'", ":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`"]):
        return f'"{s}"'
    return s
