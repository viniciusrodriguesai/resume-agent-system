from typing import Any

import pytest

from evaluation.benchmarks.rankers import TfidfRanker
from evaluation.benchmarks.retrieval import run_retrieval_benchmark
from evaluation.schema import RetrievalCase


def benchmark_case() -> RetrievalCase:
    return RetrievalCase(
        case_id="python",
        query="Python",
        candidates=[
            {"candidate_id": "hit", "text": "Desenvolvi serviços em Python."},
            {"candidate_id": "noise", "text": "Desenhei telas no Figma."},
        ],
        relevant_candidate_ids=["hit"],
    )


def test_runner_reports_quality_performance_and_backend() -> None:
    result = run_retrieval_benchmark([benchmark_case()], TfidfRanker(), k=1, runs=2)

    assert result.metrics == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "precision_at_k": 1.0,
        "recall_at_k": 1.0,
        "mrr": 1.0,
        "ndcg_at_k": 1.0,
    }
    assert result.performance.runs == 2
    assert result.performance.mean_latency_ms >= 0.0
    assert result.backend_status["actual_backend"] == "tfidf"


class AlternatingRanker:
    name = "alternating"

    def __init__(self) -> None:
        self._reverse = False

    def rank(self, case: RetrievalCase) -> list[str]:
        self._reverse = not self._reverse
        values = [candidate.candidate_id for candidate in case.candidates]
        return list(reversed(values)) if self._reverse else values

    def status(self) -> dict[str, Any]:
        return {"available": True}


def test_runner_rejects_non_deterministic_rankings() -> None:
    with pytest.raises(RuntimeError, match="non-deterministic"):
        run_retrieval_benchmark([benchmark_case()], AlternatingRanker(), runs=2)
