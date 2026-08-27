import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.settings import Settings

RESUME_TEXT = """Lucas Almeida
Recife, PE
lucas.almeida@example.invalid
+55 81 99999-9999

ENGENHEIRO DE SOFTWARE

Engenheiro de software com 4 anos de experiência no desenvolvimento de aplicações backend, APIs REST e sistemas distribuídos.
Experiência profissional com Python, FastAPI, PostgreSQL, Docker e AWS.

- Desenvolvi APIs REST utilizando Python e FastAPI.
- Implementei serviços backend utilizados por aproximadamente 150 mil requisições por dia.
- Modelei e otimizei bancos PostgreSQL.
- Criei imagens Docker e utilizei containers nos ambientes de desenvolvimento e produção.
- Configurei pipelines de CI/CD utilizando GitHub Actions.
- Utilizei AWS EC2, S3 e RDS em aplicações de produção.
- Implementei testes automatizados utilizando pytest.
- Trabalhei com Git e revisão de código em equipe.
- Li diversos artigos e tutoriais sobre Kubernetes, mas nunca administrei clusters Kubernetes em produção.

TECNOLOGIAS

Python
FastAPI
PostgreSQL
Docker
Git
GitHub Actions
pytest
REST APIs
Linux

CONHECIMENTOS ADICIONAIS

- Conhecimento básico de Redis.
- Estudei conceitos de Kubernetes.
- Não tenho experiência profissional com Java.
- Nunca utilizei Terraform em produção.
"""

JOB_TEXT = """BACKEND SOFTWARE ENGINEER

Estamos procurando uma pessoa desenvolvedora backend para atuar na construção e evolução de APIs e serviços de alta disponibilidade.

REQUISITOS OBRIGATÓRIOS

- Experiência profissional com Python.
- Experiência com FastAPI.
- Experiência com PostgreSQL.
- Experiência com Docker.
- Experiência com Python e Kubernetes.
- Experiência com AWS.
- Experiência com testes automatizados utilizando pytest.
- Conhecimento de Git.

REQUISITOS DE INFRAESTRUTURA

- Experiência prática com Kubernetes em ambientes de produção.
- Experiência com Terraform ou CloudFormation.

REQUISITOS ALTERNATIVOS

- Experiência com Redis ou RabbitMQ.

DIFERENCIAIS

- Experiência com CI/CD.
- GitHub Actions.
- Linux.
- Sistemas distribuídos.
- Observabilidade e monitoramento.
- Experiência com aplicações de alto volume de requisições.

RESPONSABILIDADES

- Desenvolver APIs REST utilizando Python e FastAPI.
- Criar serviços escaláveis e de fácil manutenção.
- Trabalhar com bancos PostgreSQL.
- Criar e manter containers Docker.
- Participar da evolução da infraestrutura em AWS e Kubernetes.
- Escrever testes automatizados.
- Participar de revisão de código.
"""

HEADINGS = {
    "REQUISITOS OBRIGATÓRIOS",
    "REQUISITOS DE INFRAESTRUTURA",
    "REQUISITOS ALTERNATIVOS",
    "DIFERENCIAIS",
    "RESPONSABILIDADES",
}


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


def test_complete_manual_validation_scenario(tmp_path):
    result = analyze_scenario(tmp_path)
    matches = {item.requirement.text: item for item in result.matches}

    assert result.job.title == "BACKEND SOFTWARE ENGINEER"
    assert len(result.job.requirements) == len(result.matches) == 17
    assert HEADINGS.isdisjoint(matches)
    assert matches["Experiência com Terraform ou CloudFormation"].status == "missing"
    assert matches["Experiência com Redis ou RabbitMQ"].status == "partial"
    assert matches["Experiência com Python e Kubernetes"].status == "partial"
    assert matches["Experiência prática com Kubernetes em ambientes de produção"].status != "matched"
    for requirement in (
        "Experiência profissional com Python",
        "Experiência com FastAPI",
        "Experiência com PostgreSQL",
        "Experiência com Docker",
        "Experiência com AWS",
        "Experiência com testes automatizados utilizando pytest",
        "Conhecimento de Git",
        "Experiência com CI/CD",
        "GitHub Actions",
        "Sistemas distribuídos",
    ):
        assert matches[requirement].status == "matched"
    assert matches["Observabilidade e monitoramento"].status == "missing"
    assert matches["Experiência com aplicações de alto volume de requisições"].status == "partial"

    assert result.score.matched + result.score.partial + result.score.missing == len(result.matches)
    assert result.score.required_missing == sum(
        item.status == "missing" and item.requirement.priority == "required"
        for item in result.matches
    )
    downstream = "\n".join(
        [
            result.review_summary,
            result.markdown_report,
            *(item.action for item in result.recommendations),
        ]
    )
    assert all(heading not in downstream for heading in HEADINGS)

    privacy_types = {item.entity_type for item in result.privacy.entities}
    assert {"EMAIL", "TELEFONE", "NOME_CANDIDATO"} <= privacy_types
    assert result.privacy.raw_document_stored is False
    assert result.privacy.anonymized_document_stored is False
    serialized = result.model_dump_json()
    assert "lucas.almeida@example.invalid" not in serialized
    assert "+55 81 99999-9999" not in serialized
    assert "Lucas Almeida" not in serialized


@pytest.mark.parametrize("strictness", ["flexível", "equilibrado", "conservador"])
def test_negation_and_headers_are_invariant_across_strictness(tmp_path, strictness: str):
    result = analyze_scenario(tmp_path / strictness, strictness)
    matches = {item.requirement.text: item for item in result.matches}

    assert HEADINGS.isdisjoint(matches)
    assert matches["Experiência com Terraform ou CloudFormation"].status != "matched"
    assert matches["Experiência prática com Kubernetes em ambientes de produção"].status != "matched"
    assert matches["Experiência com Redis ou RabbitMQ"].status != "matched"


def test_strictness_is_monotonic_for_manual_validation_scenario(tmp_path):
    strength = {"missing": 0, "partial": 1, "matched": 2}
    results = {
        strictness: analyze_scenario(tmp_path / strictness, strictness)
        for strictness in ("flexível", "equilibrado", "conservador")
    }
    by_strictness = {
        strictness: {item.requirement.text: item.status for item in result.matches}
        for strictness, result in results.items()
    }

    for requirement in by_strictness["equilibrado"]:
        assert strength[by_strictness["flexível"][requirement]] >= strength[
            by_strictness["equilibrado"][requirement]
        ]
        assert strength[by_strictness["equilibrado"][requirement]] >= strength[
            by_strictness["conservador"][requirement]
        ]
