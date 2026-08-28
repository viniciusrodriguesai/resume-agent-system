from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_group_for
from resume_ai.domain.scoring import classify
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings


class FakeReranker:
    def __init__(self, *scores: float) -> None:
        self.scores = scores

    def predict(self, pairs, **_kwargs):
        return list(self.scores[: len(pairs)])


def make_engine(tmp_path, *scores: float, top_n: int = 5) -> EmbeddingEngine:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=True,
        reranker_top_n=top_n,
        history_enabled=False,
        cache_enabled=False,
    )
    engine = EmbeddingEngine(settings)
    engine._reranker = FakeReranker(*scores)
    return engine


@pytest.mark.parametrize(
    "requirement",
    [
        "Experiência profissional com Python",
        "Experiência com RabbitMQ ou Apache Kafka",
        "Experiência com Prometheus e Grafana",
        "Experiência com AlphaDB",
        "Experiência com AlphaDB ou BetaDB",
    ],
)
def test_reranker_one_cannot_match_zero_concept_coverage(tmp_path, requirement: str) -> None:
    engine = make_engine(tmp_path, 0.9999)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Engenheira de software com cinco anos em sistemas backend e APIs REST."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert group.concepts
    assert result["concept_coverage"] == 0.0
    assert classify(result["final_score"], "flexível") != "matched"
