from __future__ import annotations

import numpy as np

from resume_ai.agents.catalog import concept_alias_groups
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings
from resume_ai.utils.text import split_chunks


def make_settings(tmp_path, *, embeddings: bool = False) -> Settings:
    return Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=embeddings,
        reranker_enabled=False,
        history_enabled=False,
        cache_enabled=False,
    )


def test_chunks_are_specific_and_hide_privacy_markers():
    chunks = split_chunks(
        """<NOME_CANDIDATO>
E-mail: <EMAIL>
Telefone: <TELEFONE>
Python e SQL.
Projeto com Pandas, NumPy e Scikit-learn."""
    )
    assert chunks == ["Python e SQL.", "Projeto com Pandas, NumPy e Scikit-learn."]
    assert all("<" not in chunk and ">" not in chunk for chunk in chunks)


def test_one_skill_does_not_satisfy_three_skill_requirement(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Pandas, NumPy e Scikit-learn"
    groups = concept_alias_groups(requirement)

    partial = engine.retrieve(requirement, ["Usei Pandas para limpeza de dados."], concept_groups=groups)[0]
    complete = engine.retrieve(
        requirement,
        ["Projeto com Pandas, NumPy e Scikit-learn para classificação."],
        concept_groups=groups,
    )[0]

    assert partial["final_score"] < 0.60
    assert complete["final_score"] >= 0.80


def test_or_requirement_accepts_one_alternative(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Power BI ou Tableau"
    result = engine.retrieve(
        requirement,
        ["Desenvolvi dashboards no Power BI."],
        concept_groups=concept_alias_groups(requirement),
    )[0]
    assert result["final_score"] >= 0.80


def test_mixed_catalog_cumulative_requirement_needs_every_concept(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Python e Kubernetes"
    groups = concept_alias_groups(requirement)

    partial = engine.retrieve(
        requirement,
        ["Desenvolvi serviços em Python."],
        concept_groups=groups,
    )[0]
    complete = engine.retrieve(
        requirement,
        ["Desenvolvi serviços em Python executados no Kubernetes."],
        concept_groups=groups,
    )[0]

    assert groups == [["Python", "python"], ["kubernetes"]]
    assert partial["final_score"] < 0.60
    assert complete["final_score"] >= 0.80


def test_mixed_catalog_alternative_accepts_known_option(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Python ou Kubernetes"

    result = engine.retrieve(
        requirement,
        ["Desenvolvi serviços em Python."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] >= 0.80


def test_explicit_negation_does_not_count_as_evidence(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "NumPy"
    result = engine.retrieve(
        requirement,
        ["Trabalhei com Pandas sem utilizar NumPy."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["concept_coverage"] == 0.0
    assert result["final_score"] < 0.32


def test_embeddings_are_batched_and_candidate_cache_is_reused(tmp_path, monkeypatch):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=True))

    class FakeModel:
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        def encode(self, texts, **kwargs):
            values = list(texts)
            self.calls.append(values)
            rows = []
            for index, _ in enumerate(values):
                vector = np.array([1.0, float(index + 1), 0.5], dtype=float)
                vector /= np.linalg.norm(vector)
                rows.append(vector)
            return np.vstack(rows)

    model = FakeModel()
    monkeypatch.setattr(engine, "_load_model", lambda: model)

    queries = ["Python", "SQL", "Pandas"]
    chunks = ["Python e SQL", "Projeto com Pandas"]
    groups = [concept_alias_groups(query) for query in queries]

    engine.retrieve_many(queries, chunks, concept_groups=groups)
    assert len(model.calls) == 2  # trechos uma vez + consultas em um lote

    engine.retrieve_many(queries, chunks, concept_groups=groups)
    assert len(model.calls) == 3  # trechos vieram do cache; só consultas foram codificadas


def test_embedding_failure_status_does_not_copy_exception_message(tmp_path, monkeypatch):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=True))
    private_detail = "candidate@example.invalid at C:\\private\\model"

    class FailingModel:
        def encode(self, _texts, **_kwargs):
            raise RuntimeError(private_detail)

    monkeypatch.setattr(engine, "_load_model", FailingModel)

    engine.retrieve("Python", ["Python em produção"])

    assert engine.status["embedding_error"] == "inference:RuntimeError"
    assert private_detail not in str(engine.status)


def test_reranker_failure_status_does_not_copy_exception_message(tmp_path):
    settings = make_settings(tmp_path).model_copy(update={"reranker_enabled": True})
    engine = EmbeddingEngine(settings)
    private_detail = "candidate@example.invalid at C:\\private\\reranker"

    class FailingReranker:
        def predict(self, _pairs, **_kwargs):
            raise ValueError(private_detail)

    engine._reranker = FailingReranker()
    candidates = engine.retrieve("Python", ["Python em produção"])

    engine.rerank("Python", candidates)

    assert engine.status["reranker_error"] == "inference:ValueError"
    assert private_detail not in str(engine.status)
