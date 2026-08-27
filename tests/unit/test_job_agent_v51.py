import pytest

from resume_ai.agents.job_agent import JobAgent
from resume_ai.settings import Settings

MANUAL_VALIDATION_JOB = """BACKEND SOFTWARE ENGINEER

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


def make_settings(tmp_path) -> Settings:
    return Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        history_enabled=False,
    )


def test_job_intro_is_not_treated_as_requirement(tmp_path):
    settings = make_settings(tmp_path)
    profile, _ = JobAgent(settings).run(
        """ESTÁGIO EM CIÊNCIA DE DADOS
Estamos procurando uma pessoa estagiária para integrar nosso time de dados.

REQUISITOS OBRIGATÓRIOS
- Python
- SQL

RESPONSABILIDADES
- Limpar e analisar dados
"""
    )

    texts = [item.text for item in profile.requirements]
    assert texts == ["Python", "SQL"]
    assert profile.responsibilities == ["Limpar e analisar dados"]


def test_manual_validation_job_headers_are_not_requirements(tmp_path):
    profile, _ = JobAgent(make_settings(tmp_path)).run(MANUAL_VALIDATION_JOB)
    texts = {item.text for item in profile.requirements}

    assert {
        "REQUISITOS OBRIGATÓRIOS",
        "REQUISITOS DE INFRAESTRUTURA",
        "REQUISITOS ALTERNATIVOS",
        "DIFERENCIAIS",
        "RESPONSABILIDADES",
    }.isdisjoint(texts)
    assert "Experiência com Terraform ou CloudFormation" in texts
    assert "Experiência com Redis ou RabbitMQ" in texts


@pytest.mark.parametrize(
    "heading",
    [
        "Requisitos obrigatórios",
        "REQUISITOS:",
        "Requirements",
        "Required Qualifications",
        "Preferred Qualifications",
        "Nice to Have",
        "Responsibilities",
        "Qualifications",
        "Infraestrutura",
        "Requisitos técnicos",
    ],
)
def test_short_unbulleted_section_headings_are_not_requirements(tmp_path, heading: str):
    job_text = f"Engenheiro de Software\n{heading}\n- Python"

    profile, _ = JobAgent(make_settings(tmp_path)).run(job_text)

    assert heading.rstrip(":") not in {item.text for item in profile.requirements}
