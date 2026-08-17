from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceStats:
    runs: int
    mean_latency_ms: float
    p95_latency_ms: float
    peak_memory_delta_mb: float


def summarize_performance(
    latencies_ms: Sequence[float],
    peak_memory_delta_mb: float,
) -> PerformanceStats:
    """Summarize measured runs without claiming hardware-independent results."""
    if not latencies_ms:
        raise ValueError("at least one latency measurement is required")
    if any(not math.isfinite(value) or value < 0 for value in latencies_ms):
        raise ValueError("latency measurements must be finite and non-negative")
    if not math.isfinite(peak_memory_delta_mb) or peak_memory_delta_mb < 0:
        raise ValueError("peak memory delta must be finite and non-negative")

    ordered = sorted(float(value) for value in latencies_ms)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return PerformanceStats(
        runs=len(ordered),
        mean_latency_ms=statistics.fmean(ordered),
        p95_latency_ms=ordered[p95_index],
        peak_memory_delta_mb=float(peak_memory_delta_mb),
    )
