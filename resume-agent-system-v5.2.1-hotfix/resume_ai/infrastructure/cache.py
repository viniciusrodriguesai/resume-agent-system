from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from resume_ai.settings import Settings


class SafeResultCache:
    """Cache opcional. Nunca recebe currículos brutos; a chave deve ser um hash."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.path = settings.cache_dir / "results"
        self.path.mkdir(parents=True, exist_ok=True)
        self._diskcache = None
        if settings.cache_enabled:
            try:
                from diskcache import Cache

                self._diskcache = Cache(str(self.path))
            except Exception:
                self._diskcache = None

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.settings.cache_enabled:
            return None
        if self._diskcache is not None:
            value = self._diskcache.get(key)
            return value if isinstance(value, dict) else None
        file = self.path / f"{key}.json"
        if not file.exists():
            return None
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
            if time.time() - float(payload.get("saved_at", 0)) > self.settings.cache_ttl_seconds:
                file.unlink(missing_ok=True)
                return None
            return payload.get("value")
        except Exception:
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self.settings.cache_enabled:
            return
        if self._diskcache is not None:
            self._diskcache.set(key, value, expire=self.settings.cache_ttl_seconds)
            return
        payload = {"saved_at": time.time(), "value": value}
        (self.path / f"{key}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def clear(self) -> None:
        if self._diskcache is not None:
            self._diskcache.clear()
        for file in self.path.glob("*.json"):
            file.unlink(missing_ok=True)
