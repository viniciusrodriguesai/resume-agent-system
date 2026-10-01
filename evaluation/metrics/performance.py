from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

import psutil


class MemoryTracker:
    """Sample RSS; report unknown if any required measurement is unavailable."""

    def __init__(self) -> None:
        self.baseline: int | None = None
        self.peak = 0
        self.available = True
        self.sample()

    def sample(self) -> None:
        if not self.available:
            return
        try:
            rss = psutil.Process().memory_info().rss
        except (psutil.Error, OSError):
            self.available = False
            return
        if self.baseline is None:
            self.baseline = rss
        self.peak = max(self.peak, rss)

    def delta_mb(self) -> float | None:
        if not self.available or self.baseline is None:
            return None
        return max(0.0, (self.peak - self.baseline) / 1024 / 1024)


@dataclass(frozen=True)
class PerformanceStats:
    runs: int
    mean_latency_ms: float
    p95_latency_ms: float
    peak_memory_delta_mb: float | None


def summarize_performance(
    latencies_ms: Sequence[float],
    peak_memory_delta_mb: float | None,
) -> PerformanceStats:
    """Summarize measured runs without claiming hardware-independent results."""
    if not latencies_ms:
        raise ValueError("at least one latency measurement is required")
    if any(not math.isfinite(value) or value < 0 for value in latencies_ms):
        raise ValueError("latency measurements must be finite and non-negative")
    if peak_memory_delta_mb is not None and (not math.isfinite(peak_memory_delta_mb) or peak_memory_delta_mb < 0):
        raise ValueError("peak memory delta must be finite and non-negative")

    ordered = sorted(float(value) for value in latencies_ms)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return PerformanceStats(
        runs=len(ordered),
        mean_latency_ms=statistics.fmean(ordered),
        p95_latency_ms=ordered[p95_index],
        peak_memory_delta_mb=float(peak_memory_delta_mb) if peak_memory_delta_mb is not None else None,
    )
