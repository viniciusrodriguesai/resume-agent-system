from __future__ import annotations

import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.settings import Settings

RESUME_TEXT = """Marina Costa
Fortaleza, CE
marina.costa@example.invalid
+55 85 98888-7777

SENIOR BACKEND ENGINEER

RESUMO

Engenheira de software com 5 anos de experiência em sistemas backend, APIs REST e plataformas de processamento de dados.

EXPERIÊNCIA PROFISSIONAL

Senior Backend Engineer — Orion Systems
Março de 2023 — Atual

- Desenvolvo APIs REST em Python utilizando FastAPI.
- Opero serviços Python em produção.
- Modelei bancos PostgreSQL e otimizei consultas SQL.
- Implementei cache distribuído utilizando Redis em produção.
- Configurei e mantive pipelines de CI/CD utilizando GitHub Actions.
- Escrevi testes unitários e de integração com pytest.
- Criei imagens Docker e mantive aplicações containerizadas em produção.
- Administrei serviços na AWS utilizando EC2, RDS e S3.
- Um dos serviços processa aproximadamente 2 milhões de requisições por dia.
- Implementei métricas e dashboards utilizando Prometheus e Grafana.
- Trabalhei em sistemas distribuídos e arquiteturas orientadas a eventos.

Backend Developer — NovaTech
Janeiro de 2021 — Fevereiro de 2023

- Desenvolvi aplicações backend em Python.
- Trabalhei com PostgreSQL.
- Automatizei testes com pytest.
- Utilizei Git diariamente em equipe.

TECNOLOGIAS

Python
FastAPI
PostgreSQL
Redis
Docker
AWS
Git
GitHub Actions
pytest
Linux
Prometheus
Grafana

CONHECIMENTOS E LIMITAÇÕES

- Tenho conhecimento básico de Kubernetes.
- Estudei conceitos de Terraform.
- Nunca administrei Kubernetes em produção.
- Nunca utilizei Terraform profissionalmente.
- Não tenho experiência com RabbitMQ.
- Li artigos sobre Apache Kafka.
- Tenho conhecimento teórico de Java.

FORMAÇÃO

Bacharelado em Engenharia de Software
Universidade Exemplo
2017 — 2021

IDIOMAS

Português — Nativo
Inglês — Avançado
"""

JOB_TEXT = """SENIOR BACKEND SOFTWARE ENGINEER

Buscamos uma pessoa para desenvolver e operar serviços backend de alta disponibilidade.

REQUISITOS OBRIGATÓRIOS

- Experiência profissional com Python.
- Experiência com FastAPI.
- Experiência com PostgreSQL.
- Experiência com Docker.
- Experiência com AWS.
- Experiência com testes automatizados utilizando pytest.
- Experiência com CI/CD.
- Conhecimento de Git.

INFRAESTRUTURA E PLATAFORMA

- Experiência prática com Kubernetes em produção.
- Experiência com Terraform ou Pulumi.

MENSAGERIA

- Experiência com RabbitMQ ou Apache Kafka.

CACHE

- Experiência com Redis ou Memcached.

OBSERVABILIDADE

- Experiência com Prometheus e Grafana.

DIFERENCIAIS

- Experiência com sistemas distribuídos.
- Experiência com aplicações de alto volume de requisições.
- Linux.
- GitHub Actions.

RESPONSABILIDADES

- Desenvolver APIs REST em Python.
- Operar aplicações em produção.
- Trabalhar com bancos relacionais.
- Criar pipelines de CI/CD.
- Monitorar aplicações e investigar problemas de desempenho.
"""

HEADINGS = {"MENSAGERIA", "CACHE", "OBSERVABILIDADE"}


def analyze_scenario(tmp_path, strictness: str = "equilibrado") -> AnalysisResult:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
        cache_enabled=False,
        store_raw_documents=False,
        store_anonymized_documents=False,
    )
    return ResumeAnalysisService(settings).analyze(
        AnalysisRequest(
            resume_text=RESUME_TEXT,
            job_text=JOB_TEXT,
            profile="balanced",
            strictness=strictness,
        )
    )


def test_manual_603_fixture_has_17_real_requirements(tmp_path):
    result = analyze_scenario(tmp_path)

    assert result.job.title == "SENIOR BACKEND SOFTWARE ENGINEER"
    assert len(result.job.requirements) == len(result.matches) == 17
    assert sum(item.priority == "required" for item in result.job.requirements) == 13
    assert sum(item.priority == "desired" for item in result.job.requirements) == 4


def test_manual_603_fixture_has_no_heading_requirements(tmp_path):
    result = analyze_scenario(tmp_path)
    requirement_texts = {item.text for item in result.job.requirements}
    downstream = "\n".join(
        [
            result.review_summary,
            result.markdown_report,
            ResumeAnalysisService.to_json(result),
            ResumeAnalysisService.to_csv(result),
            *(item.action for item in result.recommendations),
        ]
    )

    assert HEADINGS.isdisjoint(requirement_texts)
    assert all(f'Desenvolva evidência real para “{heading}”' not in downstream for heading in HEADINGS)


def test_distributed_systems_fixture_is_not_missing(tmp_path):
    result = analyze_scenario(tmp_path)
    matches = {item.requirement.text: item for item in result.matches}

    assert matches["Experiência com sistemas distribuídos"].status == "matched"
    assert "Trabalhei em sistemas distribuídos" in (
        matches["Experiência com sistemas distribuídos"].evidence or ""
    )


def test_manual_603_semantic_expectations(tmp_path):
    result = analyze_scenario(tmp_path)
    matches = {item.requirement.text: item for item in result.matches}

    for requirement in (
        "Experiência profissional com Python",
        "Experiência com FastAPI",
        "Experiência com PostgreSQL",
        "Experiência com Docker",
        "Experiência com AWS",
        "Experiência com testes automatizados utilizando pytest",
        "Experiência com CI/CD",
        "Conhecimento de Git",
        "Experiência com Redis ou Memcached",
        "Experiência com Prometheus e Grafana",
        "Linux",
        "GitHub Actions",
    ):
        assert matches[requirement].status == "matched", requirement

    assert matches["Experiência prática com Kubernetes em produção"].status != "matched"
    assert matches["Experiência com Terraform ou Pulumi"].status != "matched"
    assert matches["Experiência com RabbitMQ ou Apache Kafka"].status == "missing"
    assert matches["Experiência com aplicações de alto volume de requisições"].status in {
        "matched",
        "partial",
    }


def test_manual_603_candidate_sections_are_consistent(tmp_path):
    result = analyze_scenario(tmp_path)

    assert "Implementei cache distribuído utilizando Redis em produção." in result.candidate.experience
    assert "Implementei métricas e dashboards utilizando Prometheus e Grafana." in result.candidate.experience
    assert "Desenvolvi aplicações backend em Python." in result.candidate.experience
    assert result.candidate.projects == []


def test_privacy_manual_603_fixture(tmp_path):
    result = analyze_scenario(tmp_path)
    serialized = result.model_dump_json()

    assert result.candidate.candidate_name == "Candidato anonimizado"
    assert {"EMAIL", "TELEFONE", "NOME_CANDIDATO"} <= {
        entity.entity_type for entity in result.privacy.entities
    }
    assert result.privacy.raw_document_stored is False
    assert result.privacy.anonymized_document_stored is False
    for pii in ("Marina Costa", "marina.costa@example.invalid", "+55 85 98888-7777"):
        assert pii not in serialized


@pytest.mark.parametrize("strictness", ["flexível", "equilibrado", "conservador"])
def test_strictness_regression_manual_603_fixture(tmp_path, strictness: str):
    result = analyze_scenario(tmp_path / strictness, strictness)
    matches = {item.requirement.text: item for item in result.matches}

    assert HEADINGS.isdisjoint(matches)
    assert matches["Experiência prática com Kubernetes em produção"].status != "matched"
    assert matches["Experiência com Terraform ou Pulumi"].status != "matched"
    assert matches["Experiência com RabbitMQ ou Apache Kafka"].status != "matched"


def test_strictness_statuses_are_monotonic_for_manual_603_fixture(tmp_path):
    strength = {"missing": 0, "partial": 1, "matched": 2}
    results = {
        strictness: analyze_scenario(tmp_path / strictness, strictness)
        for strictness in ("flexível", "equilibrado", "conservador")
    }
    statuses = {
        strictness: {match.requirement.text: match.status for match in result.matches}
        for strictness, result in results.items()
    }

    for requirement in statuses["equilibrado"]:
        assert strength[statuses["flexível"][requirement]] >= strength[
            statuses["equilibrado"][requirement]
        ]
        assert strength[statuses["equilibrado"][requirement]] >= strength[
            statuses["conservador"][requirement]
        ]
