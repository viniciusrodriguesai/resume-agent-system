from resume_ai.agents.job_agent import JobAgent
from resume_ai.settings import Settings


def test_job_intro_is_not_treated_as_requirement(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        history_enabled=False,
    )
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
