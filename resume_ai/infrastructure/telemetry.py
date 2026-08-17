from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

import psutil

from resume_ai.settings import Settings

from .log_sanitizer import sanitize_log_event, sanitize_log_fields

_HANDLER_MARKER = "_resume_ai_json_handler"
_LOGGER_LOCK = threading.Lock()


@dataclass
class Timing:
    name: str
    duration_ms: float


class JsonLogFormatter(logging.Formatter):
    """Serialize one bounded operational event per line without exception payloads."""

    def format(self, record: logging.LogRecord) -> str:
        raw_fields = getattr(record, "telemetry_fields", {})
        fields = sanitize_log_fields(raw_fields) if isinstance(raw_fields, dict) else {}
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": sanitize_log_event(record.getMessage()),
            **fields,
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class Telemetry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("resume_ai")
        self.logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        with _LOGGER_LOCK:
            if not any(getattr(handler, _HANDLER_MARKER, False) for handler in self.logger.handlers):
                handler = logging.StreamHandler()
                handler.setFormatter(JsonLogFormatter())
                setattr(handler, _HANDLER_MARKER, True)
                self.logger.addHandler(handler)
        self.logger.propagate = False

    @contextmanager
    def timer(self, name: str, target: dict[str, float]) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            target[name] = round((time.perf_counter() - start) * 1000, 2)

    @staticmethod
    def process_memory_mb() -> float:
        process = psutil.Process()
        return float(round(process.memory_info().rss / 1024 / 1024, 2))

    def info(self, event: str, **safe_fields: object) -> None:
        self.logger.info(
            sanitize_log_event(event),
            extra={"telemetry_fields": sanitize_log_fields(safe_fields)},
        )
