from types import SimpleNamespace

import psutil
import pytest

from evaluation.metrics.performance import MemoryTracker, summarize_performance
from resume_ai.infrastructure.telemetry import Telemetry


@pytest.mark.parametrize("error", [psutil.NoSuchProcess(123), psutil.AccessDenied(123), OSError("unavailable")])
def test_unavailable_memory_is_explicitly_unknown(monkeypatch, error):
    def fail():
        raise error

    monkeypatch.setattr(psutil, "Process", fail)
    assert Telemetry.process_memory_mb() is None
    memory = MemoryTracker()
    memory.sample()
    assert summarize_performance([1.0], memory.delta_mb()).peak_memory_delta_mb is None


def test_available_memory_keeps_measured_value(monkeypatch):
    monkeypatch.setattr(psutil, "Process", lambda: SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=1048576)))
    assert Telemetry.process_memory_mb() == 1.0
