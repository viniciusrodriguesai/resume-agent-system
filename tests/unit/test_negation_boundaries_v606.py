from __future__ import annotations

from typing import Any

import pytest

from resume_ai.agents.catalog import concept_group_for
from resume_ai.domain.scoring import classify
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings
from resume_ai.utils.text import exact_phrase, negated_phrase


class FakeReranker:
    def __init__(self, score: float) -> None:
        self.score = score

    def predict(self, pairs: list[list[str]], **_kwargs: Any) -> list[float]:
        return [self.score] * len(pairs)


def evaluate(tmp_path, requirement: str, evidence: str, score: float) -> dict[str, Any]:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=True,
        cache_enabled=False,
        history_enabled=False,
    )
    engine = EmbeddingEngine(settings)
    engine._reranker = FakeReranker(score)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(
        requirement,
        [evidence],
        concept_groups=group.alias_groups,
    )
    return engine.rerank(requirement, candidates)[0]


@pytest.mark.parametrize("boundary", [". ", "! ", "? ", "; ", "\n", "\n- "])
@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_negation_does_not_cross_semantic_boundary_for_or(
    tmp_path,
    boundary: str,
    reranker_score: float,
) -> None:
    evidence = f"Nunca utilizei Terraform{boundary}Utilizo Pulumi profissionalmente."

    result = evaluate(
        tmp_path,
        "Experiência com Terraform ou Pulumi",
        evidence,
        reranker_score,
    )

    assert negated_phrase(evidence, "Terraform") is True
    assert exact_phrase(evidence, "Pulumi") is True
    assert negated_phrase(evidence, "Pulumi") is False
    assert result["concept_coverage"] == 1.0
    assert result["explicitly_negated"] is False
    assert classify(result["final_score"], "conservador") == "matched"


@pytest.mark.parametrize(
    ("requirement", "evidence", "positive"),
    [
        (
            "Experiência com RabbitMQ ou Apache Kafka",
            "Nunca usei RabbitMQ. Uso Apache Kafka em produção.",
            "Apache Kafka",
        ),
        (
            "Experiência com Grafana ou Prometheus",
            "Não tenho experiência com Grafana. Trabalho com Prometheus em produção.",
            "Prometheus",
        ),
        (
            "Experiência com Terraform ou Pulumi",
            "Nunca utilizei Terraform, mas utilizo Pulumi profissionalmente.",
            "Pulumi",
        ),
    ],
)
def test_positive_or_alternative_remains_valid_after_local_negation(
    tmp_path,
    requirement: str,
    evidence: str,
    positive: str,
) -> None:
    result = evaluate(tmp_path, requirement, evidence, 1.0)

    assert exact_phrase(evidence, positive) is True
    assert negated_phrase(evidence, positive) is False
    assert result["concept_coverage"] == 1.0
    assert classify(result["final_score"], "conservador") == "matched"


def test_same_sentence_negation_can_cover_both_or_alternatives(tmp_path) -> None:
    evidence = "Não utilizei Terraform ou Pulumi."

    result = evaluate(
        tmp_path,
        "Experiência com Terraform ou Pulumi",
        evidence,
        1.0,
    )

    assert negated_phrase(evidence, "Terraform") is True
    assert negated_phrase(evidence, "Pulumi") is True
    assert result["concept_coverage"] == 0.0
    assert classify(result["final_score"], "flexível") == "missing"


@pytest.mark.parametrize("boundary", [". ", "! ", "? ", "; ", "\n"])
def test_and_remains_incomplete_when_only_second_concept_is_positive(
    tmp_path,
    boundary: str,
) -> None:
    evidence = f"Não tenho experiência com Grafana{boundary}Trabalho com Prometheus em produção."

    result = evaluate(
        tmp_path,
        "Experiência com Grafana e Prometheus",
        evidence,
        1.0,
    )

    assert result["concept_coverage"] == 0.5
    for strictness in ("flexível", "equilibrado", "conservador"):
        assert classify(result["final_score"], strictness) != "matched"
