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
        if len(self.scores) == 1:
            return [self.scores[0]] * len(pairs)
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


@pytest.mark.parametrize("reranker_score", [0.0, 0.01])
def test_reranker_zero_cannot_destroy_strong_operational_evidence(
    tmp_path,
    reranker_score: float,
) -> None:
    requirement = "Experiência profissional com Python"
    engine = make_engine(tmp_path, reranker_score)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Opero serviços Python em produção há cinco anos."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["operational_experience"] is True
    assert classify(result["final_score"], "conservador") == "matched"


@pytest.mark.parametrize("reranker_score", [0.99, 1.0])
def test_negated_evidence_ceiling_survives_reranker(
    tmp_path,
    reranker_score: float,
) -> None:
    requirement = "Experiência com Terraform"
    engine = make_engine(tmp_path, reranker_score)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Nunca utilizei Terraform profissionalmente."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["explicitly_negated"] is True
    assert classify(result["final_score"], "flexível") == "missing"


@pytest.mark.parametrize("reranker_score", [0.99, 1.0])
def test_weak_experience_ceiling_survives_reranker(
    tmp_path,
    reranker_score: float,
) -> None:
    requirement = "Experiência profissional com Java"
    engine = make_engine(tmp_path, reranker_score)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Tenho conhecimento teórico de Java."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["weak_experience"] is True
    assert classify(result["final_score"], "flexível") != "matched"


def test_incomplete_and_never_becomes_full_after_rerank(tmp_path) -> None:
    requirement = "Experiência com Prometheus e Grafana"
    engine = make_engine(tmp_path, 1.0)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Trabalhei com Prometheus em produção e nunca utilizei Grafana."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["concept_coverage"] < 1.0
    assert classify(result["final_score"], "flexível") != "matched"


def test_positive_or_survives_low_reranker(tmp_path) -> None:
    requirement = "Experiência com Terraform ou Pulumi"
    engine = make_engine(tmp_path, 0.0)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        [
            "Nunca utilizei Terraform.",
            "Utilizo Pulumi profissionalmente há 3 anos.",
        ],
        top_k=2,
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["concept_coverage"] == 1.0
    assert result["operational_experience"] is True
    assert classify(result["final_score"], "conservador") == "matched"


def test_quantified_scale_floor_survives_low_reranker(tmp_path) -> None:
    requirement = "Experiência com aplicações de alto volume de requisições"
    engine = make_engine(tmp_path, 0.0)
    candidates = engine.retrieve(
        requirement,
        ["Um serviço processa aproximadamente 2 milhões de requisições por dia."],
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["quantified_scale"] is True
    assert classify(result["final_score"], "conservador") == "partial"
