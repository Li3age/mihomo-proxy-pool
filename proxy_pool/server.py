"""Flask HTTP server — REST API + Web GUI static files."""

import json
import logging
import os
import secrets
import shutil
import subprocess
import time
import sys
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file

from .config import Config
from .mihomo_api import MihomoClient
from .rotator import Rotator
from .subscription import fetch_subscription, parse_proxies, generate_runtime_config

log = logging.getLogger(__name__)

app = Flask(__name__, static_folder=None)
config: Config = None
rotator: Rotator = None
mihomo_proc: subprocess.Popen | None = None
_project_root: Path = None

# Ports for the 2nd mihomo instance
MIHOMO_PROXY_PORT = 7892
MIHOMO_API_PORT = 9092



# ──────────────────── Web GUI ────────────────────


@app.route("/")
def index():
    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    return send_file(os.path.join(web_dir, "index.html"))


@app.route("/<path:filename>")
def static_files(filename):
    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    return send_from_directory(web_dir, filename)


# ──────────────────── REST API ────────────────────


@app.route("/api/status")
def api_status():
    status = rotator.get_status()
    return jsonify(status)


@app.route("/api/nodes")
def api_nodes():
    nodes = rotator.get_nodes()
    current = rotator.get_status()["current"]
    return jsonify({"current": current, "nodes": nodes})


@app.route("/api/rotate", methods=["POST"])
def api_rotate():
    body = request.get_json(silent=True) or {}
    strategy = body.get("strategy")
    result = rotator.rotate(strategy)
    if result:
        return jsonify({"ok": True, "proxy": result["name"], "time": result["time"]})
    return jsonify({"ok": False, "error": "No valid proxies available"}), 500


@app.route("/api/switch", methods=["POST"])
def api_switch():
    name = request.args.get("name") or (request.get_json(silent=True) or {}).get("name")
    if not name:
        return jsonify({"ok": False, "error": "Missing 'name' parameter"}), 400
    try:
        rotator.mihomo.switch_proxy(config.pool["group"], name)
        rotator.refresh()
        return jsonify({"ok": True, "current": name})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/settings", methods=["GET", "PUT"])
def api_settings():
    if request.method == "GET":
        return jsonify({
            "strategy": rotator.strategy,
            "auto_interval": rotator.auto_interval,
            "auto_running": rotator.get_status()["auto_running"],
            "exclude_keywords": rotator.exclude_keywords,
            "filter_pattern": rotator.filter_pattern,
            "filter_mode": rotator.filter_mode,
            "group": rotator.group,
            "subscription_url": config.subscription_url,
        })
    else:
        body = request.get_json(silent=True) or {}
        need_restart = False
        if "strategy" in body:
            rotator.set_strategy(body["strategy"])
            config.pool["strategy"] = body["strategy"]
        if "auto_interval" in body:
            rotator.set_auto_interval(int(body["auto_interval"]))
            config.pool["auto_rotate_interval"] = int(body["auto_interval"])
        if "subscription_url" in body and body["subscription_url"] != config.subscription_url:
            config.subscription_url = body["subscription_url"]
            need_restart = True
        if "filter_pattern" in body or "filter_mode" in body:
            pat = body.get("filter_pattern", rotator.filter_pattern)
            mode = body.get("filter_mode", rotator.filter_mode)
            rotator.set_filter(pat, mode)
            config.pool["filter_pattern"] = pat
            config.pool["filter_mode"] = mode
        if "exclude_keywords" in body:
            rotator.set_exclude_keywords(body["exclude_keywords"])
            config.pool["exclude_keywords"] = body["exclude_keywords"]
        config.save()

        if need_restart:
            _restart_mihomo()
            time.sleep(3)
            rotator.refresh()

        return jsonify({"ok": True})


@app.route("/api/auto-rotate", methods=["POST"])
def api_auto_rotate():
    action = (request.get_json(silent=True) or {}).get("action", "toggle")
    if action == "start":
        rotator.start_auto()
    elif action == "stop":
        rotator.stop_auto()
    else:
        if rotator.get_status()["auto_running"]:
            rotator.stop_auto()
        else:
            rotator.start_auto()
    return jsonify({"ok": True, "auto_running": rotator.get_status()["auto_running"]})


@app.route("/api/history")
def api_history():
    return jsonify(rotator.get_history())


@app.route("/api/health")
def api_health():
    mihomo_ok = rotator.mihomo.health_check()
    return jsonify({"ok": True, "mihomo": mihomo_ok})


# ──────────────────── Mihomo process management ────────────────────


def _copy_mmdb():
    """Copy MMDB files from common mihomo installation locations."""
    dst_dir = _project_root / config.mihomo["work_dir"].lstrip("./")
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Common mihomo/clash runtime directories
    candidates = [
        Path.home() / ".config" / "mihomo",
        Path.home() / ".local" / "share" / "mihomo",
        Path.home() / "AppData" / "Local" / "mihomo",
        Path.home() / "AppData" / "Roaming" / "mihomo",
        Path.home() / "clash-for-linux" / "runtime",
        Path.home() / "clash-verge" / "runtime",
        Path("/opt/mihomo"),
        Path("/etc/mihomo"),
        _project_root / "bin",
    ]

    for fname in ["Country.mmdb", "geoip.metadb", "GeoLite2-ASN.mmdb",
                   "GeoIP.dat", "GeoSite.dat"]:
        dst = dst_dir / fname
        if dst.exists():
            continue
        for src_dir in candidates:
            src = src_dir / fname
            if src.exists():
                shutil.copy2(src, dst)
                log.info("Copied %s to runtime/", fname)
                break


def _regenerate_mihomo_config():
    """Fetch subscription, parse proxies, generate runtime config."""
    template_path = _project_root / config.mihomo["config_template"].lstrip("./")
    runtime_path = _project_root / config.mihomo["runtime_config"].lstrip("./")
    work_dir = _project_root / config.mihomo["work_dir"].lstrip("./")
    work_dir.mkdir(parents=True, exist_ok=True)

    _copy_mmdb()

    sub_url = config.subscription_url
    if not sub_url:
        log.warning("No subscription URL configured — mihomo will start with no proxies")
        proxies = []
    else:
        try:
            log.info("Fetching subscription...")
            insecure = config.data.get("insecure_tls", False)
            raw = fetch_subscription(sub_url, proxy=None, insecure=insecure)
            proxies = parse_proxies(raw)
        except Exception as e:
            log.warning("Cannot fetch subscription (network not ready): %s", e)
            if runtime_path.exists():
                log.info("Keeping existing runtime config")
                return
            proxies = []

    content = generate_runtime_config(str(template_path), proxies)

    with open(runtime_path, "w", encoding="utf-8") as f:
        f.write(content)

    log.info("Generated runtime config with %d proxies at %s", len(proxies), runtime_path)


def _ensure_mihomo():
    """Start mihomo, or reuse an existing one if already running."""
    global mihomo_proc
    binary = _project_root / config.mihomo["binary"].lstrip("./")
    if sys.platform == "win32":
        binary_exe = binary.with_suffix(binary.suffix + ".exe")
        if binary_exe.exists():
            binary = binary_exe
    work_dir = _project_root / config.mihomo["work_dir"].lstrip("./")
    runtime_config = _project_root / config.mihomo["runtime_config"].lstrip("./")

    if not binary.exists():
        log.error("Mihomo binary not found at %s. Run bin/download.sh first.", binary)
        return False

    api_url = f"http://127.0.0.1:{MIHOMO_API_PORT}"
    saved_secret = config.mihomo.get("api_secret") or ""

    # Try to talk to an existing mihomo first
    if saved_secret:
        try:
            mc = MihomoClient(api_url, saved_secret)
            mc._req("GET", "/version")
            log.info("Reusing existing mihomo on port %d", MIHOMO_API_PORT)
            return True
        except Exception:
            log.debug("No existing mihomo, starting fresh...")

    # Kill any stale process on our port
    _kill_stale_mihomo()

    # Generate a fresh secret
    secret = secrets.token_hex(16)
    config.mihomo["api_secret"] = secret
    config.save()

    cmd = [
        str(binary),
        "-f", str(runtime_config),
        "-d", str(work_dir),
        "-ext-ctl", f"127.0.0.1:{MIHOMO_API_PORT}",
        "-secret", secret,
    ]

    log.info("Starting mihomo: %s", " ".join(cmd))
    mihomo_proc = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return True


def _restart_mihomo():
    global mihomo_proc, rotator
    _regenerate_mihomo_config()
    _stop_mihomo()
    _ensure_mihomo()


def _kill_stale_mihomo():
    """Kill any process listening on our API port."""
    import platform
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 f"Get-NetTCPConnection -LocalPort {MIHOMO_API_PORT} -ErrorAction SilentlyContinue | "
                 f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force }}"],
                capture_output=True, timeout=10
            )
        else:
            subprocess.run(
                ['fuser', '-k', f'{MIHOMO_API_PORT}/tcp'],
                capture_output=True, timeout=5
            )
    except Exception:
        pass
    time.sleep(1)


def _start_mihomo():
    _ensure_mihomo()


def _stop_mihomo():
    global mihomo_proc
    if mihomo_proc:
        mihomo_proc.terminate()
        try:
            mihomo_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mihomo_proc.kill()
        mihomo_proc = None
        log.info("Mihomo stopped")


def _wait_for_mihomo(timeout: float = 30) -> bool:
    """Wait until mihomo API is up AND proxy groups are loaded."""
    deadline = time.time() + timeout
    group = config.pool["group"]
    while time.time() < deadline:
        if mihomo_proc and mihomo_proc.poll() is not None:
            log.error("Mihomo exited with code %s", mihomo_proc.returncode)
            return False
        try:
            resp = rotator.mihomo._req("GET", "/version")
            if not resp:
                time.sleep(1)
                continue
            g = rotator.mihomo.get_group(group)
            if g and g.get("all"):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


# ──────────────────── Entry point ────────────────────


def create_app(proj_root: Path) -> Flask:
    global config, rotator, _project_root
    _project_root = proj_root

    config = Config(str(proj_root / "config.json"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # regenerate runtime config (fetches subscription via existing proxy)
    _regenerate_mihomo_config()

    # start or reuse mihomo
    if not _ensure_mihomo():
        log.error("Failed to start mihomo")
        sys.exit(1)

    # init API client
    api_url = f"http://127.0.0.1:{MIHOMO_API_PORT}"
    mihomo = MihomoClient(api_url, config.mihomo["api_secret"])
    rotator = Rotator(
        mihomo=mihomo,
        group=config.pool["group"],
        strategy=config.pool["strategy"],
        auto_interval=config.pool.get("auto_rotate_interval", 300),
        exclude_keywords=config.pool.get("exclude_keywords", []),
        filter_pattern=config.pool.get("filter_pattern", ""),
        filter_mode=config.pool.get("filter_mode", "fuzzy"),
    )

    log.info("Waiting for mihomo API to be ready...")
    if not _wait_for_mihomo():
        log.error("Mihomo failed to start. Check logs in %s", config.mihomo["work_dir"])
        sys.exit(1)

    # Route all traffic through the pool
    try:
        mihomo.switch_proxy("GLOBAL", config.pool["group"])
        log.info("Switched GLOBAL -> %s", config.pool["group"])
    except Exception as e:
        log.warning("Could not switch GLOBAL: %s", e)

    rotator.refresh()

    # Do initial rotation to skip info-only entries like "剩余流量"
    current = rotator.get_status()["current"]
    if any(kw in current for kw in ["剩余流量", "套餐到期", "过滤掉"]):
        rotator.rotate()

    if config.pool["auto_rotate_interval"] > 0:
        rotator.start_auto()

    log.info("Proxy pool ready — proxy: 127.0.0.1:%d, web: http://%s:%d",
             MIHOMO_PROXY_PORT, config.server["host"], config.server["port"])

    import atexit
    atexit.register(_stop_mihomo)

    return app
