from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_alias_groups
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings


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


@pytest.mark.parametrize(
    ("requirement", "evidence", "literal"),
    [
        (
            "Experiência com SuperDB",
            "Utilizei SuperDB em produção durante três anos.",
            "superdb",
        ),
        (
            "Experiência com sistemas distribuídos",
            "Trabalhei em sistemas distribuídos e arquiteturas orientadas a eventos.",
            "sistemas distribuidos",
        ),
        (
            "Experiência com observabilidade distribuída",
            "Implementei observabilidade distribuída nos serviços em produção.",
            "observabilidade distribuida",
        ),
        (
            "Experiência com processamento de eventos",
            "Operei uma plataforma de processamento de eventos.",
            "processamento de eventos",
        ),
        (
            "Experiência profissional com ÜberDB",
            "Utilizei ÜberDB profissionalmente.",
            "uberdb",
        ),
    ],
)
def test_unknown_literal_concept_can_match_operational_evidence(
    tmp_path,
    requirement: str,
    evidence: str,
    literal: str,
):
    engine = make_engine(tmp_path)
    groups = concept_alias_groups(requirement)

    result = engine.retrieve(requirement, [evidence], concept_groups=groups)[0]

    assert groups == [[literal]]
    assert result["concept_coverage"] == 1.0
    assert result["final_score"] >= 0.80


def test_unknown_literal_concept_does_not_match_generic_text(tmp_path):
    engine = make_engine(tmp_path)
    requirement = "Experiência com SuperDB"

    result = engine.retrieve(
        requirement,
        ["Tenho experiência com bancos de dados."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["concept_coverage"] == 0.0
    assert result["final_score"] < 0.50
