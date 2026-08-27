from __future__ import annotations

import pytest

from resume_ai.agents.job_agent import JobAgent
from resume_ai.settings import Settings


def make_settings(tmp_path) -> Settings:
    return Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        history_enabled=False,
    )


@pytest.mark.parametrize(
    "heading",
    [
        "BACKEND",
        "Banco de Dados",
        "MENSAGERIA:",
        "Cache",
        "OBSERVABILIDADE",
        "Cloud:",
        "SEGURANÇA",
        "Data Platform",
        "PLATAFORMA DE DADOS",
        "Überwachung",
        "Sécurité:",
    ],
)
def test_generic_job_subheadings_are_not_requirements(tmp_path, heading: str):
    job_text = f"""BACKEND SOFTWARE ENGINEER

REQUISITOS OBRIGATÓRIOS

{heading}
- Experiência com Python
"""

    profile, _ = JobAgent(make_settings(tmp_path)).run(job_text)

    assert [requirement.text for requirement in profile.requirements] == [
        "Experiência com Python"
    ]


def test_generic_subheadings_preserve_parent_priority(tmp_path):
    job_text = """BACKEND SOFTWARE ENGINEER

REQUISITOS OBRIGATÓRIOS

BACKEND
- Experiência com Python

BANCO DE DADOS
- Experiência com PostgreSQL

MENSAGERIA
- RabbitMQ

CACHE
- Redis

OBSERVABILIDADE
- Prometheus

CLOUD
- AWS

SEGURANÇA
- OAuth

DATA PLATFORM
- Spark
"""

    profile, _ = JobAgent(make_settings(tmp_path)).run(job_text)

    assert len(profile.requirements) == 8
    assert all(requirement.priority == "required" for requirement in profile.requirements)
    assert all(requirement.source_section == "required" for requirement in profile.requirements)


def test_short_normal_sentence_is_not_mistaken_for_heading(tmp_path):
    job_text = """BACKEND SOFTWARE ENGINEER

REQUISITOS OBRIGATÓRIOS

- Boa comunicação é essencial
- Experiência com Python
"""

    profile, _ = JobAgent(make_settings(tmp_path)).run(job_text)

    assert [requirement.text for requirement in profile.requirements] == [
        "Boa comunicação é essencial",
        "Experiência com Python",
    ]
