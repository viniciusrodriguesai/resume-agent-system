import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings


def test_analysis_runs_without_heavy_models(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
    )
    service = ResumeAnalysisService(settings)
    result = service.analyze(AnalysisRequest(
        resume_text="""Candidato
Python, SQL, Pandas e Git. Projeto de machine learning.""",
        job_text="""Estágio em Dados
REQUISITOS OBRIGATÓRIOS
- Python
- SQL
REQUISITOS DESEJÁVEIS
- Docker""",
    ))
    assert result.score.overall_score > 0
    assert result.privacy.total_removed >= 1
    assert len(result.matches) >= 2


def test_cache_hit_gets_new_identity_and_is_not_persisted_by_default(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        history_enabled=False,
    )
    service = ResumeAnalysisService(settings)
    request = AnalysisRequest(
        resume_text="Candidato\nPython, SQL e Git em projetos de dados.",
        job_text="Analista de dados com requisitos Python e SQL.",
    )

    first = service.analyze(request)
    second = service.analyze(request)

    assert first.analysis_id != second.analysis_id
    assert first.engine_status["cache_hit"] is False
    assert second.engine_status["cache_hit"] is True
    assert not (tmp_path / "cache" / "results").exists()


def test_service_rejects_deployment_text_limit(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        history_enabled=False,
        max_document_chars=20,
    )
    service = ResumeAnalysisService(settings)
    request = AnalysisRequest(
        resume_text="Python e SQL em muitos projetos profissionais.",
        job_text="Vaga para pessoa desenvolvedora Python.",
    )

    with pytest.raises(ValueError, match="limite"):
        service.analyze(request)
