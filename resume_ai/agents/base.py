from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from resume_ai.domain.models import AgentTrace

T = TypeVar("T")


def run_agent(name: str, action: Callable[[], T], summary: Callable[[T], str], confidence: Callable[[T], float] | None = None) -> tuple[T, AgentTrace]:
    start = time.perf_counter()
    alerts: list[str] = []
    try:
        result = action()
    except Exception as exc:
        alerts.append(f"{type(exc).__name__}: {exc}")
        raise
    duration = round((time.perf_counter() - start) * 1000, 2)
    return result, AgentTrace(
        agent=name,
        summary=summary(result),
        duration_ms=duration,
        confidence=round(confidence(result) if confidence else 0.8, 2),
        alerts=alerts,
    )
