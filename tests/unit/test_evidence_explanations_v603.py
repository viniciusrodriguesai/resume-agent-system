from __future__ import annotations

import uuid

import pytest

from resume_ai.agents.evidence_agent import EvidenceAgent
from resume_ai.domain.models import CandidateProfile, JobProfile, Requirement
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings


def explain(tmp_path, requirement_text: str, evidence: str) -> str:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
        cache_enabled=False,
    )
    requirement = Requirement(id=str(uuid.uuid4()), text=requirement_text)
    matches, _ = EvidenceAgent(EmbeddingEngine(settings)).run(
        CandidateProfile(chunks=[evidence]),
        JobProfile(requirements=[requirement]),
        top_k=1,
    )
    return matches[0].explanation


@pytest.mark.parametrize(
    ("requirement", "evidence", "expected"),
    [
        (
            "Experiência com Redis",
            "Operei Redis em produção.",
            "A evidência demonstra uso operacional de Redis.",
        ),
        (
            "Experiência com Prometheus e Grafana",
            "Operei Prometheus em produção.",
            "Apenas 1 de 2 conceitos obrigatórios foi encontrado.",
        ),
        (
            "Experiência com Terraform ou Pulumi",
            "Operei Pulumi em produção.",
            "Uma alternativa válida do requisito OR foi comprovada.",
        ),
        (
            "Experiência com Terraform",
            "Nunca utilizei Terraform profissionalmente.",
            "Terraform foi explicitamente negado nesta evidência.",
        ),
        (
            "Experiência com SuperDB",
            "Utilizei SuperDB em produção.",
            "Correspondência baseada em conceito literal fora do catálogo.",
        ),
    ],
)
def test_explanation_reflects_actual_evidence_signals(
    tmp_path,
    requirement: str,
    evidence: str,
    expected: str,
):
    assert expected in explain(tmp_path, requirement, evidence)
