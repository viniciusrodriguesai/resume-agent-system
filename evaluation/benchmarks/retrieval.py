from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

import psutil

from evaluation.benchmarks.rankers import Ranker
from evaluation.metrics.classification import f1_score, precision, recall
from evaluation.metrics.performance import PerformanceStats, summarize_performance
from evaluation.metrics.ranking import mean_reciprocal_rank, ndcg_at_k, precision_at_k, recall_at_k
from evaluation.schema import RetrievalCase


@dataclass(frozen=True)
class RetrievalBenchmarkResult:
    variant: str
    case_count: int
    k: int
    metrics: dict[str, float]
    performance: PerformanceStats
    backend_status: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "case_count": self.case_count,
            "k": self.k,
            "metrics": self.metrics,
            "performance": asdict(self.performance),
            "backend_status": self.backend_status,
        }


def run_retrieval_benchmark(
    cases: list[RetrievalCase],
    ranker: Ranker,
    *,
    k: int = 3,
    runs: int = 3,
) -> RetrievalBenchmarkResult:
    if not cases:
        raise ValueError("at least one retrieval case is required")
    if k <= 0:
        raise ValueError("k must be greater than zero")
    if runs <= 0:
        raise ValueError("runs must be greater than zero")

    process = psutil.Process()
    baseline_rss = process.memory_info().rss
    peak_rss = baseline_rss
    latencies_ms: list[float] = []
    reference_rankings: list[list[str]] | None = None

    for _ in range(runs):
        current_rankings: list[list[str]] = []
        for case in cases:
            started = time.perf_counter()
            ranking = ranker.rank(case)
            latencies_ms.append((time.perf_counter() - started) * 1000.0)
            peak_rss = max(peak_rss, process.memory_info().rss)
            current_rankings.append(ranking)
        if reference_rankings is None:
            reference_rankings = current_rankings
        elif current_rankings != reference_rankings:
            raise RuntimeError("ranker produced non-deterministic results across benchmark runs")

    rankings = reference_rankings or []
    relevance_sets = [set(case.relevant_candidate_ids) for case in cases]
    expected_binary: list[bool] = []
    predicted_binary: list[bool] = []
    for case, ranking, relevant_ids in zip(cases, rankings, relevance_sets, strict=True):
        predicted_ids = set(ranking[:k])
        for candidate in case.candidates:
            expected_binary.append(candidate.candidate_id in relevant_ids)
            predicted_binary.append(candidate.candidate_id in predicted_ids)

    metrics = {
        "precision": precision(expected_binary, predicted_binary),
        "recall": recall(expected_binary, predicted_binary),
        "f1": f1_score(expected_binary, predicted_binary),
        "precision_at_k": sum(
            precision_at_k(ranking, relevant_ids, k)
            for ranking, relevant_ids in zip(rankings, relevance_sets, strict=True)
        ) / len(cases),
        "recall_at_k": sum(
            recall_at_k(ranking, relevant_ids, k)
            for ranking, relevant_ids in zip(rankings, relevance_sets, strict=True)
        ) / len(cases),
        "mrr": mean_reciprocal_rank(rankings, relevance_sets),
        "ndcg_at_k": sum(
            ndcg_at_k(ranking, relevant_ids, k)
            for ranking, relevant_ids in zip(rankings, relevance_sets, strict=True)
        ) / len(cases),
    }
    memory_delta_mb = max(0.0, (peak_rss - baseline_rss) / 1024 / 1024)
    return RetrievalBenchmarkResult(
        variant=ranker.name,
        case_count=len(cases),
        k=k,
        metrics=metrics,
        performance=summarize_performance(latencies_ms, memory_delta_mb),
        backend_status=ranker.status(),
    )
