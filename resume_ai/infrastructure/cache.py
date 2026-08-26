from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from resume_ai.settings import Settings


class SafeResultCache:
    """Cache opcional. Nunca recebe currículos brutos; a chave deve ser um hash."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.path = settings.cache_dir / "results"
        self._memory: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.RLock()
        if settings.cache_enabled and settings.cache_backend == "disk":
            self.path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.settings.cache_enabled:
            return None
        if self.settings.cache_backend == "memory":
            with self._lock:
                item = self._memory.get(key)
                if item is None:
                    return None
                saved_at, value = item
                if time.time() - saved_at > self.settings.cache_ttl_seconds:
                    self._memory.pop(key, None)
                    return None
                return value
        file = self.path / f"{key}.json"
        if not file.exists():
            return None
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return None
            if time.time() - float(payload.get("saved_at", 0)) > self.settings.cache_ttl_seconds:
                file.unlink(missing_ok=True)
                return None
            disk_value = payload.get("value")
            return disk_value if isinstance(disk_value, dict) else None
        except Exception:
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self.settings.cache_enabled:
            return
        if self.settings.cache_backend == "memory":
            with self._lock:
                if len(self._memory) >= self.settings.cache_max_entries:
                    oldest = min(self._memory, key=lambda item: self._memory[item][0])
                    self._memory.pop(oldest, None)
                self._memory[key] = (time.time(), value)
            return
        payload = {"saved_at": time.time(), "value": value}
        destination = self.path / f"{key}.json"
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        with self._lock:
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                temporary.replace(destination)
                self._enforce_disk_limit()
            finally:
                temporary.unlink(missing_ok=True)

    def _enforce_disk_limit(self) -> None:
        files = list(self.path.glob("*.json"))
        excess = len(files) - self.settings.cache_max_entries
        if excess <= 0:
            return

        def saved_at(file: Path) -> tuple[float, str]:
            try:
                payload = json.loads(file.read_text(encoding="utf-8"))
                return float(payload.get("saved_at", 0)), file.name
            except Exception:
                return 0.0, file.name

        for stale in sorted(files, key=saved_at)[:excess]:
            stale.unlink(missing_ok=True)

    def clear(self) -> None:
        with self._lock:
            self._memory.clear()
        if self.path.exists():
            for file in self.path.glob("*.json"):
                file.unlink(missing_ok=True)
