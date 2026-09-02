from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_group_for
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
    return group, engine.rerank(requirement, candidates)[0]


@pytest.mark.parametrize("concept", ["AlphaDB", "BetaDB", "OmegaMQ", "NovaCache"])
@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_unknown_literal_accepts_explicit_production_evidence(
    tmp_path,
    concept: str,
    reranker_score: float,
) -> None:
    group, result = evaluate(
        tmp_path,
        f"Experiência com {concept} em produção",
        f"Utilizo {concept} em produção.",
        reranker_score,
    )

    assert group.uses_literal_fallback is True
    assert group.concepts[0].canonical == concept.casefold()
    assert result["concept_coverage"] == 1.0
    assert result["operational_experience"] is True
    assert result["professional_experience"] is True
    assert result["production_experience"] is True
    assert classify(result["final_score"], "conservador") == "matched"


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
@pytest.mark.parametrize(
    ("evidence", "expected_negated"),
    [
        ("Utilizo AlphaDB localmente.", False),
        ("Estudei AlphaDB.", False),
        ("AlphaDB", False),
        ("Nunca utilizei AlphaDB.", True),
    ],
)
def test_unknown_literal_without_production_never_fully_matches(
    tmp_path,
    evidence: str,
    expected_negated: bool,
    reranker_score: float,
) -> None:
    _, result = evaluate(
        tmp_path,
        "Experiência com AlphaDB em produção",
        evidence,
        reranker_score,
    )

    assert result["production_experience"] is False
    assert result["explicitly_negated"] is expected_negated
    for strictness in ("flexível", "equilibrado", "conservador"):
        assert classify(result["final_score"], strictness) != "matched"


@pytest.mark.parametrize("reranker_score", [0.0, 1.0])
def test_unknown_literal_negation_remains_missing(
    tmp_path,
    reranker_score: float,
) -> None:
    _, result = evaluate(
        tmp_path,
        "Experiência com AlphaDB em produção",
        "Nunca utilizei AlphaDB.",
        reranker_score,
    )

    assert result["explicitly_negated"] is True
    for strictness in ("flexível", "equilibrado", "conservador"):
        assert classify(result["final_score"], strictness) == "missing"
