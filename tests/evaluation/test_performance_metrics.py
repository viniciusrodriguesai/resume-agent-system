import math

import pytest

from evaluation.metrics.performance import summarize_performance


def test_summarizes_mean_p95_and_memory_delta() -> None:
    stats = summarize_performance([10.0, 30.0, 20.0, 40.0], peak_memory_delta_mb=2.5)

    assert stats.runs == 4
    assert stats.mean_latency_ms == 25.0
    assert stats.p95_latency_ms == 40.0
    assert stats.peak_memory_delta_mb == 2.5


@pytest.mark.parametrize("latencies", [[], [-1.0], [math.inf], [math.nan]])
def test_rejects_invalid_latency_measurements(latencies: list[float]) -> None:
    with pytest.raises(ValueError):
        summarize_performance(latencies, peak_memory_delta_mb=0.0)


def test_rejects_negative_memory_delta() -> None:
    with pytest.raises(ValueError, match="memory"):
        summarize_performance([1.0], peak_memory_delta_mb=-0.1)
