from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_group_for
from resume_ai.agents.evidence_agent import _explain_evidence
from resume_ai.domain.models import Requirement
from resume_ai.domain.scoring import classify
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


def assert_never_matched(result) -> None:
    for strictness in ("flexível", "equilibrado", "conservador"):
        assert classify(result["final_score"], strictness) != "matched"


def test_knowledge_accepts_explicit_skill_list(tmp_path) -> None:
    result = evaluate(tmp_path, "Conhecimento de Python", "Python", 0.0)

    assert classify(result["final_score"], "equilibrado") == "matched"


@pytest.mark.parametrize("reranker_score", [0.0, 0.01, 0.5, 0.99, 1.0])
def test_experience_skill_list_is_at_most_partial(
    tmp_path,
    reranker_score: float,
) -> None:
    result = evaluate(tmp_path, "Experiência com Python", "Python", reranker_score)

    assert_never_matched(result)


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_professional_experience_rejects_skill_list(
    tmp_path,
    reranker_score: float,
) -> None:
    result = evaluate(
        tmp_path,
        "Experiência profissional com Python",
        "Python",
        reranker_score,
    )

    assert result.get("professional_experience") is False
    assert_never_matched(result)


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
@pytest.mark.parametrize(
    "evidence",
    [
        "Desenvolvi um projeto pessoal em Python.",
        "Desenvolvi uma aplicação pessoal em Python.",
        "Desenvolvi uma API pessoal em Python.",
    ],
)
def test_professional_experience_rejects_personal_project(
    tmp_path,
    reranker_score: float,
    evidence: str,
) -> None:
    result = evaluate(
        tmp_path,
        "Experiência profissional com Python",
        evidence,
        reranker_score,
    )

    assert result.get("personal_project_context") is True
    assert result.get("professional_experience") is False
    assert_never_matched(result)


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_professional_experience_accepts_professional_evidence(
    tmp_path,
    reranker_score: float,
) -> None:
    result = evaluate(
        tmp_path,
        "Experiência profissional com Python",
        "Trabalhei profissionalmente com Python na Empresa X.",
        reranker_score,
    )

    assert result.get("professional_experience") is True
    assert classify(result["final_score"], "conservador") == "matched"


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_production_experience_rejects_personal_project(
    tmp_path,
    reranker_score: float,
) -> None:
    result = evaluate(
        tmp_path,
        "Experiência com Kubernetes em produção",
        "Utilizei Kubernetes em projeto pessoal.",
        reranker_score,
    )

    assert result.get("production_experience") is False
    assert_never_matched(result)


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_production_experience_accepts_production_evidence(
    tmp_path,
    reranker_score: float,
) -> None:
    result = evaluate(
        tmp_path,
        "Experiência com Kubernetes em produção",
        "Administrei Kubernetes em produção por dois anos.",
        reranker_score,
    )

    assert result.get("production_experience") is True
    assert result.get("professional_experience") is True
    assert classify(result["final_score"], "conservador") == "matched"


def test_normal_experience_accepts_applied_personal_project(tmp_path) -> None:
    result = evaluate(
        tmp_path,
        "Experiência com Docker",
        "Utilizei Docker em projeto pessoal.",
        0.0,
    )

    assert result["operational_experience"] is True
    assert classify(result["final_score"], "conservador") == "matched"


@pytest.mark.parametrize(
    "requirement",
    [
        "Experiência profissional com Docker",
        "Experiência em produção com Docker",
    ],
)
def test_personal_docker_project_cannot_satisfy_stronger_intents(
    tmp_path,
    requirement: str,
) -> None:
    result = evaluate(
        tmp_path,
        requirement,
        "Utilizei Docker em projeto pessoal.",
        1.0,
    )

    assert_never_matched(result)


@pytest.mark.parametrize(
    ("requirement_text", "evidence", "expected_explanation"),
    [
        ("Experiência com Python", "Python", "uso aplicado"),
        (
            "Experiência profissional com Python",
            "Desenvolvi um projeto pessoal em Python.",
            "contexto profissional",
        ),
        (
            "Experiência com Kubernetes em produção",
            "Utilizei Kubernetes em projeto pessoal.",
            "ambiente de produção",
        ),
    ],
)
def test_intent_policy_is_explained(
    tmp_path,
    requirement_text: str,
    evidence: str,
    expected_explanation: str,
) -> None:
    candidate = evaluate(tmp_path, requirement_text, evidence, 1.0)
    requirement = Requirement(id="requirement", text=requirement_text)

    explanation = _explain_evidence(
        requirement,
        concept_group_for(requirement_text),
        candidate,
    )

    assert expected_explanation in explanation
