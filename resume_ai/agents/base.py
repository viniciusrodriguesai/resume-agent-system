from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from resume_ai.domain.models import AgentResult

T = TypeVar("T")


class AgentExecutionError(RuntimeError):
    """Carry a PII-safe failed agent result while preserving the private cause."""

    def __init__(self, result: AgentResult) -> None:
        super().__init__(f"{result.agent} failed")
        self.result = result


def run_agent(
    name: str,
    action: Callable[[], T],
    summary: Callable[[T], str],
    confidence: Callable[[T], float] | None = None,
    *,
    warnings: Callable[[T], list[str]] | None = None,
    evidence: Callable[[T], list[str]] | None = None,
    metadata: Callable[[T], dict[str, Any]] | None = None,
) -> tuple[T, AgentResult]:
    start = time.perf_counter()
    try:
        result = action()
    except Exception as exc:
        duration = round((time.perf_counter() - start) * 1000, 2)
        failed = AgentResult(
            agent=name,
            summary="Agent execution failed.",
            status="error",
            duration_ms=duration,
            confidence=0.0,
            alerts=["Execution failed; inspect sanitized server diagnostics."],
            metadata={"exception_type": type(exc).__name__},
        )
        raise AgentExecutionError(failed) from exc
    duration = round((time.perf_counter() - start) * 1000, 2)
    alerts = warnings(result) if warnings else []
    return result, AgentResult(
        agent=name,
        summary=summary(result),
        status="warning" if alerts else "success",
        duration_ms=duration,
        confidence=round(confidence(result) if confidence else 0.8, 2),
        alerts=alerts,
        evidence=evidence(result) if evidence else [],
        metadata=metadata(result) if metadata else {},
    )
