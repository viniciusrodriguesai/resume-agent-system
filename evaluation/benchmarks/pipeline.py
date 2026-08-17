from __future__ import annotations

import statistics
import time
from dataclasses import asdict, dataclass
from typing import Any

import psutil

from evaluation.metrics.performance import PerformanceStats, summarize_performance
from evaluation.schema import AnalysisCase
from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.evaluation import classification_metrics
from resume_ai.utils.text import normalize


@dataclass(frozen=True)
class PipelineBenchmarkResult:
    variant: str
    case_count: int
    metrics: dict[str, object]
    performance: PerformanceStats
    mean_agent_duration_ms: dict[str, float]
    backend_status: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "case_count": self.case_count,
            "metrics": self.metrics,
            "performance": asdict(self.performance),
            "mean_agent_duration_ms": self.mean_agent_duration_ms,
            "backend_status": self.backend_status,
        }


def run_pipeline_benchmark(
    cases: list[AnalysisCase],
    service: ResumeAnalysisService,
    *,
    runs: int = 3,
) -> PipelineBenchmarkResult:
    if not cases:
        raise ValueError("at least one pipeline case is required")
    if runs <= 0:
        raise ValueError("runs must be greater than zero")
    if service.settings.cache_enabled:
        raise ValueError("pipeline benchmarks require cache_enabled=false")

    process = psutil.Process()
    baseline_rss = process.memory_info().rss
    peak_rss = baseline_rss
    latencies_ms: list[float] = []
    agent_durations: dict[str, list[float]] = {}
    expected_labels: list[str] = []
    reference_predictions: list[str] | None = None

    for run_index in range(runs):
        current_predictions: list[str] = []
        for case in cases:
            started = time.perf_counter()
            result = service.analyze(
                AnalysisRequest(
                    resume_text=case.resume_text,
                    job_text=case.job_text,
                    profile=service.settings.profile,
                    strictness=case.strictness,
                )
            )
            latencies_ms.append((time.perf_counter() - started) * 1000.0)
            peak_rss = max(peak_rss, process.memory_info().rss)

            actual_by_requirement = {normalize(match.requirement.text): match.status for match in result.matches}
            expected_by_requirement = {
                normalize(requirement): status
                for requirement, status in case.expected_status_by_requirement.items()
            }
            if set(actual_by_requirement) != set(expected_by_requirement):
                raise ValueError(
                    f"pipeline requirements differ from labels for case {case.case_id}"
                )
            if run_index == 0:
                expected_labels.extend(expected_by_requirement.values())
            current_predictions.extend(
                actual_by_requirement[requirement]
                for requirement in expected_by_requirement
            )
            for trace in result.traces:
                agent_durations.setdefault(trace.agent, []).append(trace.duration_ms)

        if reference_predictions is None:
            reference_predictions = current_predictions
        elif current_predictions != reference_predictions:
            raise RuntimeError("pipeline produced non-deterministic labels across benchmark runs")

    predictions = reference_predictions or []
    memory_delta_mb = max(0.0, (peak_rss - baseline_rss) / 1024 / 1024)
    engine_status = service.engine.status
    backend_status = {
        "profile": service.settings.profile,
        "embedding_loaded": bool(engine_status["embedding_loaded"]),
        "reranker_loaded": bool(engine_status["reranker_loaded"]),
        "embedding_fallback": bool(service.settings.embedding_enabled)
        and not bool(engine_status["embedding_loaded"]),
        "reranker_fallback": bool(service.settings.reranker_enabled)
        and not bool(engine_status["reranker_loaded"]),
    }
    return PipelineBenchmarkResult(
        variant="full-pipeline",
        case_count=len(cases),
        metrics=classification_metrics(expected_labels, predictions),
        performance=summarize_performance(latencies_ms, memory_delta_mb),
        mean_agent_duration_ms={
            agent: statistics.fmean(values)
            for agent, values in sorted(agent_durations.items())
        },
        backend_status=backend_status,
    )
