from __future__ import annotations

import uuid

import pytest

from resume_ai.agents.catalog import concept_group_for
from resume_ai.agents.evidence_agent import EvidenceAgent
from resume_ai.domain.models import CandidateProfile, JobProfile, Requirement
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


class AdversarialStrengthReranker:
    def predict(self, pairs, **_kwargs):
        scores = {
            "Utilizo FastAPI em produção.": 0.0,
            "Desenvolvo APIs REST utilizando FastAPI.": 0.01,
            "FastAPI": 1.0,
            "Estudei FastAPI.": 1.0,
            "Nunca utilizei FastAPI.": 1.0,
        }
        return [scores[text] for _, text in pairs]


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
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Um serviço processa aproximadamente 2 milhões de requisições por dia."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["quantified_scale"] is True
    assert classify(result["final_score"], "conservador") == "partial"


def test_reranked_candidates_are_globally_resorted(tmp_path) -> None:
    engine = make_engine(tmp_path, 0.01, top_n=1)
    candidates = [
        {
            "text": "Candidato A",
            "final_score": 0.90,
            "concept_coverage": 0.0,
            "operational_experience": False,
            "lexical_score": 0.90,
            "reranker_score": 0.0,
            "retrieval_method": "teste",
        },
        {
            "text": "Candidato B",
            "final_score": 0.86,
            "concept_coverage": 0.0,
            "operational_experience": False,
            "lexical_score": 0.86,
            "reranker_score": 0.0,
            "retrieval_method": "teste",
        },
    ]

    results = engine.rerank("requisito genérico", candidates)

    assert len(results) == 2
    assert results[0]["text"] == "Candidato B"
    assert results[0]["final_score"] > results[1]["final_score"]


def test_deterministic_high_value_candidate_survives_pre_rerank_pool(tmp_path) -> None:
    requirement = "Experiência com aplicações de alto volume de requisições"
    engine = make_engine(tmp_path, 0.0, top_n=2)
    quantified = "Um serviço processa aproximadamente 2 milhões de requisições por dia."
    decoys = ["Desenvolvi aplicações de alto volume."] * 13

    candidates = engine.retrieve(requirement, [*decoys, quantified], top_k=12)

    assert any(item["text"] == quantified for item in candidates)


def test_high_volume_candidate_survives_retrieval_and_is_considered(tmp_path) -> None:
    requirement_text = "Experiência com aplicações de alto volume de requisições"
    engine = make_engine(tmp_path, 0.0, top_n=2)
    requirement = Requirement(id=str(uuid.uuid4()), text=requirement_text)
    candidate = CandidateProfile(
        chunks=[
            "Desenvolvi aplicações de alto volume.",
            "Experiência com aplicações web de requisições.",
            "Um serviço processa aproximadamente 2 milhões de requisições por dia.",
        ]
    )

    matches, _ = EvidenceAgent(engine).run(
        candidate,
        JobProfile(requirements=[requirement]),
        top_k=1,
    )

    assert "2 milhões" in (matches[0].evidence or "")
    assert matches[0].top_candidates[0].quantified_scale is True


def test_fastapi_strength_classes_survive_adversarial_reranker(tmp_path) -> None:
    requirement = "Experiência com FastAPI"
    engine = make_engine(tmp_path, *([0.0] * 5), top_n=5)
    engine._reranker = AdversarialStrengthReranker()
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        [
            "FastAPI",
            "Desenvolvo APIs REST utilizando FastAPI.",
            "Utilizo FastAPI em produção.",
            "Estudei FastAPI.",
            "Nunca utilizei FastAPI.",
        ],
        top_k=5,
        concept_groups=group.alias_groups,
    )

    results = engine.rerank(requirement, candidates)

    assert [item["text"] for item in results] == [
        "Utilizo FastAPI em produção.",
        "Desenvolvo APIs REST utilizando FastAPI.",
        "FastAPI",
        "Estudei FastAPI.",
        "Nunca utilizei FastAPI.",
    ]


def test_multiword_concept_negation_also_covers_short_alias(tmp_path) -> None:
    requirement = "Experiência com RabbitMQ ou Apache Kafka"
    engine = make_engine(tmp_path, 1.0)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        ["Não tenho experiência com Apache Kafka."],
        concept_groups=group.alias_groups,
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["concept_coverage"] == 0.0
    assert result["explicitly_negated"] is True
    assert classify(result["final_score"], "flexível") == "missing"


def test_unreranked_candidate_still_receives_final_safety_constraints(tmp_path) -> None:
    engine = make_engine(tmp_path, 0.5, top_n=1)
    candidates = [
        {
            "text": "Top reranqueado",
            "final_score": 0.90,
            "concept_count": 0,
            "concept_coverage": 0.0,
            "lexical_score": 0.9,
            "retrieval_method": "teste",
        },
        {
            "text": "Sem RabbitMQ ou Kafka",
            "final_score": 0.86,
            "concept_count": 2,
            "concept_coverage": 0.0,
            "lexical_score": 0.86,
            "retrieval_method": "teste",
        },
    ]

    results = engine.rerank("Experiência com RabbitMQ ou Apache Kafka", candidates)
    uncovered = next(item for item in results if item["text"] == "Sem RabbitMQ ou Kafka")

    assert classify(uncovered["final_score"], "flexível") != "matched"
