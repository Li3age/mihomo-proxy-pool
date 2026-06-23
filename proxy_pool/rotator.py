"""Proxy rotation engine."""

import threading
import time
import random
import logging
from collections import deque
from datetime import datetime, timezone

from .mihomo_api import MihomoClient

log = logging.getLogger(__name__)


class Rotator:
    def __init__(
        self,
        mihomo: MihomoClient,
        group: str = "ProxyPool",
        strategy: str = "round-robin",
        auto_interval: int = 300,
        exclude_keywords: list[str] | None = None,
    ):
        self.mihomo = mihomo
        self.group = group
        self.strategy = strategy
        self.auto_interval = auto_interval
        self.exclude_keywords = exclude_keywords or []
        self._lock = threading.RLock()
        self._index = 0
        self._proxies: list[str] = []
        self._current: str = ""
        self._history: deque[dict] = deque(maxlen=100)
        self._auto_timer: threading.Timer | None = None
        self._running = False
        self._last_rotate: float = 0

    def _is_valid(self, name: str) -> bool:
        for kw in self.exclude_keywords:
            if kw in name:
                return False
        return True

    def refresh(self) -> list[str]:
        """Refresh proxy list from mihomo."""
        data = self.mihomo.get_group(self.group)
        all_proxies = data.get("all", [])
        with self._lock:
            self._proxies = [p for p in all_proxies if self._is_valid(p)]
            self._current = data.get("now", self._current)
        return self._proxies

    def get_nodes(self) -> list[dict]:
        """Get all nodes with delay info."""
        try:
            data = self.mihomo.get_proxies()
            proxies = data.get("proxies", {})
            nodes = []
            with self._lock:
                valid_names = set(self._proxies)
            for name, info in proxies.items():
                if name not in valid_names:
                    continue
                history = info.get("history", [])
                delay = history[-1].get("delay", 0) if history else 0
                nodes.append(
                    {
                        "name": name,
                        "type": info.get("type", "unknown"),
                        "alive": info.get("alive", False),
                        "delay": delay,
                    }
                )
            nodes.sort(key=lambda n: (not n["alive"], n["delay"] if n["delay"] > 0 else 99999))
            return nodes
        except Exception:
            return []

    def rotate(self, strategy: str | None = None) -> dict | None:
        """Rotate to next proxy. Returns info dict or None."""
        with self._lock:
            self.refresh()
            if not self._proxies:
                log.warning("No valid proxies available")
                return None

            strat = strategy or self.strategy
            candidates = self._proxies

            if strat == "random":
                choice = random.choice(candidates)
            elif strat == "round-robin":
                self._index = (self._index + 1) % len(candidates)
                choice = candidates[self._index]
            else:
                choice = candidates[0]

            # Skip the current one if there are alternatives
            if choice == self._current and len(candidates) > 1:
                if strat == "random":
                    others = [p for p in candidates if p != self._current]
                    choice = random.choice(others)
                else:
                    self._index = (self._index + 1) % len(candidates)
                    choice = candidates[self._index]

            try:
                self.mihomo.switch_proxy(self.group, choice)
                self._current = choice
                now = time.time()
                self._last_rotate = now
                entry = {
                    "name": choice,
                    "time": datetime.now(timezone.utc).isoformat(),
                    "timestamp": now,
                }
                self._history.appendleft(entry)
                log.info("Rotated to %s", choice)
                return entry
            except Exception as e:
                log.error("Failed to switch to %s: %s", choice, e)
                return None

    def get_status(self) -> dict:
        with self._lock:
            return {
                "current": self._current,
                "pool_size": len(self._proxies),
                "proxies": self._proxies,
                "strategy": self.strategy,
                "group": self.group,
                "auto_interval": self.auto_interval,
                "auto_running": self._running,
                "last_rotate": self._last_rotate,
            }

    def get_history(self) -> list[dict]:
        with self._lock:
            return list(self._history)

    def set_strategy(self, strategy: str):
        with self._lock:
            self.strategy = strategy

    def set_auto_interval(self, seconds: int):
        with self._lock:
            self.auto_interval = seconds
        if self._running:
            self.stop_auto()
            self.start_auto()

    def set_exclude_keywords(self, keywords: list[str]):
        with self._lock:
            self.exclude_keywords = keywords
        self.refresh()

    def start_auto(self):
        if self.auto_interval <= 0:
            return
        self._running = True
        self._schedule_next()

    def _schedule_next(self):
        if not self._running:
            return
        self._auto_timer = threading.Timer(self.auto_interval, self._auto_rotate)
        self._auto_timer.daemon = True
        self._auto_timer.start()

    def _auto_rotate(self):
        if not self._running:
            return
        try:
            self.rotate()
        except Exception as e:
            log.error("Auto-rotate failed: %s", e)
        self._schedule_next()

    def stop_auto(self):
        self._running = False
        if self._auto_timer:
            self._auto_timer.cancel()
            self._auto_timer = None
