from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_group_for
from resume_ai.domain.scoring import THRESHOLDS, classify
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings


class FakeReranker:
    def __init__(self, score: float) -> None:
        self.score = score

    def predict(self, pairs, **_kwargs):
        return [self.score] * len(pairs)


def evaluate(tmp_path, requirement: str, evidence: str, reranker_score: float):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=True,
        history_enabled=False,
        cache_enabled=False,
    )
    engine = EmbeddingEngine(settings)
    engine._reranker = FakeReranker(reranker_score)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        [evidence],
        concept_groups=group.alias_groups,
    )
    return engine.rerank(requirement, candidates)[0]


@pytest.mark.parametrize("reranker_score", [0.0, 0.5, 0.99, 1.0])
@pytest.mark.parametrize(
    "requirement",
    [
        "Experiência com RabbitMQ",
        "Experiência com RabbitMQ ou Apache Kafka",
        "Experiência com Prometheus e Grafana",
        "Experiência com AlphaDB",
    ],
    ids=["single", "or", "and", "literal"],
)
def test_zero_concept_coverage_is_missing_at_every_strictness(
    tmp_path,
    requirement: str,
    reranker_score: float,
) -> None:
    result = evaluate(
        tmp_path,
        requirement,
        "Engenheiro backend experiente.",
        reranker_score,
    )

    minimum_partial = min(limits["partial"] for limits in THRESHOLDS.values())
    assert result["concept_coverage"] == 0.0
    assert result["semantic_rule_match"] is False
    assert result["final_score"] < minimum_partial
    for strictness in ("flexível", "equilibrado", "conservador"):
        assert classify(result["final_score"], strictness) == "missing"


def test_deterministic_semantic_rule_remains_a_valid_partial_exception(tmp_path) -> None:
    result = evaluate(
        tmp_path,
        "Experiência com aplicações de alto volume de requisições",
        "2 milhões de requisições por dia.",
        0.0,
    )

    assert result["semantic_rule_match"] is True
    assert result["quantified_scale"] is True
    assert classify(result["final_score"], "conservador") == "partial"
