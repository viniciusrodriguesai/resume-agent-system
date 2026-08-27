from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_group_for
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
    ("requirement", "expected"),
    [
        ("Experiência com Terraform ou Pulumi", ["Terraform", "pulumi"]),
        ("Experiência com Redis ou Memcached", ["Redis", "memcached"]),
        ("Experiência com RabbitMQ ou Apache Kafka", ["RabbitMQ", "apache kafka"]),
        ("Experiência com AlphaDB ou BetaDB", ["alphadb", "betadb"]),
    ],
)
def test_unknown_or_concepts_are_all_extracted(requirement: str, expected: list[str]):
    group = concept_group_for(requirement)

    assert group.operator == "OR"
    assert [concept.canonical for concept in group.concepts] == expected


def test_known_and_unknown_or_concepts_work(tmp_path):
    requirement = "Experiência com Terraform ou Pulumi"
    group = concept_group_for(requirement)

    result = make_engine(tmp_path).retrieve(
        requirement,
        ["Operei Pulumi profissionalmente em produção."],
        concept_groups=group.alias_groups,
    )[0]

    assert len(group.concepts) == 2
    assert result["concept_coverage"] == 1.0
    assert result["final_score"] >= 0.80


def test_negated_first_or_positive_second_still_matches(tmp_path):
    requirement = "Experience with Terraform or Pulumi"
    group = concept_group_for(requirement)

    result = make_engine(tmp_path).retrieve(
        requirement,
        ["Never used Terraform, but operated Pulumi professionally."],
        concept_groups=group.alias_groups,
    )[0]

    assert result["concept_coverage"] == 1.0
    assert result["final_score"] >= 0.80


@pytest.mark.parametrize(
    "evidence",
    [
        "Never used AlphaDB and never used BetaDB.",
        "Li artigos sobre AlphaDB e li artigos sobre BetaDB.",
    ],
)
def test_all_or_options_negative_or_superficial_do_not_match(tmp_path, evidence: str):
    requirement = "Experiência com AlphaDB ou BetaDB"
    group = concept_group_for(requirement)

    result = make_engine(tmp_path).retrieve(
        requirement,
        [evidence],
        concept_groups=group.alias_groups,
    )[0]

    assert result["concept_coverage"] == 0.0
    assert result["final_score"] < 0.50


@pytest.mark.parametrize(
    ("requirement", "partial_evidence", "full_evidence"),
    [
        (
            "Experiência com Prometheus e Grafana",
            "Operei Prometheus em produção.",
            "Operei Prometheus e Grafana em produção.",
        ),
        (
            "Experiência com AlphaTool e BetaTool",
            "Implementei AlphaTool.",
            "Implementei AlphaTool e BetaTool.",
        ),
    ],
)
def test_and_requirement_requires_all_concepts_for_full_match(
    tmp_path,
    requirement: str,
    partial_evidence: str,
    full_evidence: str,
):
    group = concept_group_for(requirement)
    engine = make_engine(tmp_path)

    partial = engine.retrieve(
        requirement,
        [partial_evidence],
        concept_groups=group.alias_groups,
    )[0]
    full = engine.retrieve(
        requirement,
        [full_evidence],
        concept_groups=group.alias_groups,
    )[0]

    assert group.operator == "AND"
    assert len(group.concepts) == 2
    assert partial["concept_coverage"] == 0.5
    assert partial["final_score"] < 0.60
    assert full["concept_coverage"] == 1.0
    assert full["final_score"] >= 0.80
