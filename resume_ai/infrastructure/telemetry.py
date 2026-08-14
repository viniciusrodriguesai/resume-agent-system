from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psutil

from resume_ai.settings import Settings


@dataclass
class Timing:
    name: str
    duration_ms: float


class Telemetry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
        self.logger = logging.getLogger("resume_ai")
        try:
            import structlog

            self.logger = structlog.get_logger("resume_ai")
        except Exception:
            pass

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
        return round(process.memory_info().rss / 1024 / 1024, 2)

    def info(self, event: str, **safe_fields: object) -> None:
        safe_fields.pop("resume_text", None)
        safe_fields.pop("job_text", None)
        try:
            self.logger.info(event, **safe_fields)
        except TypeError:
            self.logger.info("%s %s", event, safe_fields)
