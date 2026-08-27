from __future__ import annotations

from resume_ai.agents.catalog import concept_alias_groups
from resume_ai.domain.concepts import RequirementIntent
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings
from resume_ai.utils.text import requirement_intent


def make_engine(tmp_path) -> EmbeddingEngine:
    return EmbeddingEngine(
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            embedding_enabled=False,
            reranker_enabled=False,
            history_enabled=False,
            cache_enabled=False,
        )
    )


def test_requirement_intent_is_explicitly_classified():
    assert requirement_intent("Conhecimento de Git") is RequirementIntent.KNOWLEDGE
    assert requirement_intent("Experiência com FastAPI") is RequirementIntent.EXPERIENCE
    assert (
        requirement_intent("Experiência profissional com Python")
        is RequirementIntent.PROFESSIONAL_EXPERIENCE
    )
    assert (
        requirement_intent("Experiência prática com Kubernetes em produção")
        is RequirementIntent.PRODUCTION_EXPERIENCE
    )


def test_operational_fastapi_evidence_ranks_above_skill_list(tmp_path):
    requirement = "Experiência com FastAPI"
    candidates = [
        "FastAPI",
        "Desenvolvo APIs REST utilizando FastAPI.",
        "Utilizei FastAPI em produção por 2 anos.",
        "Estudei FastAPI.",
        "Nunca utilizei FastAPI.",
    ]

    results = make_engine(tmp_path).retrieve(
        requirement,
        candidates,
        top_k=len(candidates),
        concept_groups=concept_alias_groups(requirement),
    )
    scores = {result["text"]: result["final_score"] for result in results}

    assert scores[candidates[2]] > scores[candidates[1]] > scores[candidates[0]]
    assert scores[candidates[0]] > scores[candidates[3]] > scores[candidates[4]]


def test_knowledge_requirement_can_use_skill_list(tmp_path):
    requirement = "Conhecimento de Git"

    result = make_engine(tmp_path).retrieve(
        requirement,
        ["Git"],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] >= 0.60
