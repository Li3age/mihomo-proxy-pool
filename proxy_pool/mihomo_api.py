"""Mihomo REST API client."""

import json
import urllib.request
import urllib.error
import urllib.parse
import logging

log = logging.getLogger(__name__)


class MihomoClient:
    def __init__(self, base_url: str, secret: str = ""):
        self.base_url = base_url.rstrip("/")
        self.secret = secret

    def _req(self, method: str, path: str, data: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {self.secret}"}
        body = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
                if not raw:
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            log.error("Mihomo API error: %s %s", e.code, e.reason)
            raise
        except urllib.error.URLError as e:
            log.error("Mihomo connection error: %s", e.reason)
            raise

    def health_check(self) -> bool:
        try:
            self._req("GET", "/version")
            return True
        except Exception:
            return False

    def get_proxies(self) -> dict:
        return self._req("GET", "/proxies")

    def get_group(self, name: str) -> dict:
        encoded = urllib.parse.quote(name)
        return self._req("GET", f"/proxies/{encoded}")

    def switch_proxy(self, group: str, name: str) -> dict:
        encoded = urllib.parse.quote(group)
        return self._req("PUT", f"/proxies/{encoded}", {"name": name})

    def get_version(self) -> dict:
        return self._req("GET", "/version")
