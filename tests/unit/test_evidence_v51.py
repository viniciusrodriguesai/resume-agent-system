from __future__ import annotations

import numpy as np
import pytest

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

    assert 0.35 <= partial["final_score"] < 0.60
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

    assert groups == [["Python", "python"], ["Kubernetes", "kubernetes", "k8s"]]
    assert partial["final_score"] < 0.50
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


def test_three_skill_cumulative_requirement_needs_all_concepts(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Python, Kubernetes e AWS"
    groups = concept_alias_groups(requirement)

    partial = engine.retrieve(
        requirement,
        ["Python e AWS"],
        concept_groups=groups,
    )[0]
    complete = engine.retrieve(
        requirement,
        ["Python, Kubernetes e AWS em produção"],
        concept_groups=groups,
    )[0]

    assert len(groups) == 3
    assert partial["concept_coverage"] == 0.6667
    assert partial["final_score"] < 0.50
    assert complete["final_score"] >= 0.80


@pytest.mark.parametrize(
    ("requirement", "expected_minimum", "expected_maximum"),
    [
        ("Python and Kubernetes", 0.35, 0.50),
        ("Python or Kubernetes", 0.80, 1.01),
    ],
)
def test_english_coordination_preserves_and_or_semantics(
    tmp_path,
    requirement: str,
    expected_minimum: float,
    expected_maximum: float,
):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))

    result = engine.retrieve(
        requirement,
        ["Developed production APIs in Python."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert expected_minimum <= result["final_score"] < expected_maximum


def test_reranker_preserves_partial_cumulative_evidence(tmp_path):
    settings = make_settings(tmp_path).model_copy(update={"reranker_enabled": True})
    engine = EmbeddingEngine(settings)

    class RejectingReranker:
        def predict(self, _pairs, **_kwargs):
            return [-10.0]

    engine._reranker = RejectingReranker()
    requirement = "Experiência com Pandas, NumPy e Scikit-learn"
    candidates = engine.retrieve(
        requirement,
        ["Usei Pandas para limpeza de dados."],
        concept_groups=concept_alias_groups(requirement),
    )

    result = engine.rerank(requirement, candidates)[0]

    assert result["final_score"] == 0.35


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


def test_qualified_english_negation_does_not_count_as_evidence(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Java"
    result = engine.retrieve(
        requirement,
        ["No professional experience with Java."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] < 0.32


@pytest.mark.parametrize(
    ("requirement", "resume_line"),
    [
        ("Docker", "Não tenho experiência com Docker."),
        ("AWS", "Sem experiência em AWS."),
        ("Kubernetes", "Never used Kubernetes."),
        ("Java", "No professional experience with Java."),
    ],
)
def test_required_negation_matrix_never_becomes_positive_evidence(
    tmp_path,
    requirement: str,
    resume_line: str,
):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))

    result = engine.retrieve(
        requirement,
        [resume_line],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] < 0.28


@pytest.mark.parametrize(
    "resume_line",
    [
        "Nunca utilizei Terraform em produção.",
        "Nunca usei Terraform.",
        "Jamais utilizei Terraform.",
        "Sem experiência com Terraform.",
        "Não utilizei Terraform profissionalmente.",
        "Never used Terraform.",
        "I have never used Terraform in production.",
        "No Terraform experience.",
    ],
)
def test_negated_terraform_does_not_satisfy_alternative_requirement(
    tmp_path,
    resume_line: str,
):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Terraform ou CloudFormation"

    result = engine.retrieve(
        requirement,
        [resume_line],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["concept_coverage"] == 0.0
    assert result["final_score"] < 0.35


def test_positive_cloudformation_still_satisfies_or_when_terraform_is_negated(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Terraform ou CloudFormation"

    result = engine.retrieve(
        requirement,
        ["Never used Terraform, but I have three years of CloudFormation experience."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["concept_coverage"] == 1.0
    assert result["final_score"] >= 0.80


def test_superficial_reading_is_not_equivalent_to_operational_evidence(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Kubernetes"

    superficial = engine.retrieve(
        requirement,
        ["Li sobre Kubernetes."],
        concept_groups=concept_alias_groups(requirement),
    )[0]
    operational = engine.retrieve(
        requirement,
        ["Operei clusters Kubernetes em produção por dois anos."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert 0.28 <= superficial["final_score"] < 0.50
    assert operational["final_score"] >= 0.80
    assert superficial["final_score"] < operational["final_score"]


def test_superficial_and_negated_kubernetes_mentions_do_not_combine_into_experience(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência prática com Kubernetes em ambientes de produção"

    result = engine.retrieve(
        requirement,
        [
            "Li diversos artigos e tutoriais sobre Kubernetes, mas nunca administrei "
            "clusters Kubernetes em produção."
        ],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["concept_coverage"] == 0.0
    assert result["final_score"] < 0.60


@pytest.mark.parametrize(
    "resume_line",
    [
        "Conhecimento básico de Redis.",
        "Tenho noções de Redis.",
        "Estudei Redis.",
        "Estudei conceitos de Redis.",
        "Li sobre Redis.",
        "Curso introdutório de Redis.",
    ],
)
def test_basic_or_theoretical_redis_is_not_strong_experience(
    tmp_path,
    resume_line: str,
):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Redis ou RabbitMQ"

    result = engine.retrieve(
        requirement,
        [resume_line],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] < 0.50


@pytest.mark.parametrize(
    "resume_line",
    [
        "Utilizei Redis em produção por dois anos.",
        "Implementei cache distribuído com Redis.",
        "Operei Redis em produção.",
        "Desenvolvi serviços utilizando Redis.",
    ],
)
def test_operational_redis_can_satisfy_experience_requirement(
    tmp_path,
    resume_line: str,
):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Redis ou RabbitMQ"

    result = engine.retrieve(
        requirement,
        [resume_line],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] >= 0.80


def test_operational_cicd_outranks_theoretical_knowledge(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com CI/CD"

    operational = engine.retrieve(
        requirement,
        ["Configurei pipelines de CI/CD utilizando GitHub Actions."],
        concept_groups=concept_alias_groups(requirement),
    )[0]
    theoretical = engine.retrieve(
        requirement,
        ["Conhecimento teórico de CI/CD."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert operational["final_score"] >= 0.60
    assert theoretical["final_score"] < 0.50
    assert operational["final_score"] > theoretical["final_score"]


def test_operational_pytest_paraphrase_matches_experience_requirement(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com testes automatizados utilizando pytest"

    result = engine.retrieve(
        requirement,
        ["Implementei testes automatizados utilizando pytest."],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] >= 0.60


def test_quantified_request_volume_outranks_generic_web_experience(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com aplicações de alto volume de requisições"

    quantified = engine.retrieve(
        requirement,
        ["Implementei serviços backend utilizados por aproximadamente 150 mil requisições por dia."],
    )[0]
    generic = engine.retrieve(requirement, ["Desenvolvi aplicações web."])[0]
    production_scale = engine.retrieve(
        requirement,
        ["Operei sistemas que processavam 5 milhões de requisições por dia em produção."],
    )[0]

    assert generic["final_score"] < quantified["final_score"] < 0.50
    assert generic["final_score"] < production_scale["final_score"] < 0.50


def test_experience_requirement_prefers_operational_evidence_over_skill_listing(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Experiência com Docker"
    operational = "Criei imagens Docker e utilizei containers em produção."

    results = engine.retrieve(
        requirement,
        ["Docker", operational],
        top_k=2,
        concept_groups=concept_alias_groups(requirement),
    )

    assert results[0]["text"] == operational
    assert results[0]["final_score"] > results[1]["final_score"]


def test_knowledge_requirement_still_accepts_a_skill_listing(tmp_path):
    engine = EmbeddingEngine(make_settings(tmp_path, embeddings=False))
    requirement = "Conhecimento de Docker"

    result = engine.retrieve(
        requirement,
        ["Docker"],
        concept_groups=concept_alias_groups(requirement),
    )[0]

    assert result["final_score"] >= 0.60


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
