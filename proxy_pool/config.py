"""Configuration management for proxy_pool."""

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "mihomo": {
        "binary": "./bin/mihomo",
        "api_url": "http://127.0.0.1:9091",
        "api_secret": "",
        "config_template": "./config/config.template.yaml",
        "runtime_config": "./config/runtime.yaml",
        "work_dir": "./runtime",
    },
    "pool": {
        "group": "ProxyPool",
        "strategy": "round-robin",
        "auto_rotate_interval": 300,
        "exclude_keywords": ["剩余流量", "套餐到期", "过滤掉", "DIRECT", "REJECT"],
        "filter_pattern": "",
        "filter_mode": "fuzzy",
    },
    "server": {"host": "127.0.0.1", "port": 58080},
    "subscription_url": "",
}


class Config:
    def __init__(self, path="config.json"):
        self.path = Path(path)
        self.data = DEFAULT_CONFIG.copy()
        if self.path.exists():
            with open(self.path, encoding="utf-8-sig") as f:
                loaded = json.load(f)
                self._deep_update(self.data, loaded)

    def _deep_update(self, base, update):
        for k, v in update.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def save(self):
        with open(self.path, "w", encoding="utf-8-sig") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    @property
    def mihomo(self):
        return self.data["mihomo"]

    @property
    def pool(self):
        return self.data["pool"]

    @property
    def server(self):
        return self.data["server"]

    @property
    def subscription_url(self):
        return self.data.get("subscription_url", "")

    @subscription_url.setter
    def subscription_url(self, value):
        self.data["subscription_url"] = value
        self.save()
