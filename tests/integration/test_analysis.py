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


def test_analysis_uses_injected_history_without_creating_sqlite(tmp_path):
    saved_analysis_ids: list[str] = []

    class RecordingHistory:
        def save(self, result) -> None:
            saved_analysis_ids.append(result.analysis_id)

    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        history_enabled=True,
    )
    service = ResumeAnalysisService(settings, history=RecordingHistory())
    result = service.analyze(
        AnalysisRequest(
            resume_text="Candidato com Python, SQL e Git em produção.",
            job_text="Vaga de engenharia com requisitos Python e SQL.",
        )
    )

    assert saved_analysis_ids == [result.analysis_id]
    assert not settings.history_db.exists()


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


def test_cache_never_returns_one_resume_result_for_another(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
    )
    service = ResumeAnalysisService(settings)
    job_text = """Engenheiro de plataforma
REQUISITOS OBRIGATÓRIOS
- Python
- Docker"""

    result_a = service.analyze(
        AnalysisRequest(
            resume_text="Nome: Candidate A\nPython em produção. SENTINEL-DOC-A",
            job_text=job_text,
        )
    )
    result_b = service.analyze(
        AnalysisRequest(
            resume_text="Nome: Candidate B\nDocker em produção. SENTINEL-DOC-B",
            job_text=job_text,
        )
    )

    payload_a = result_a.model_dump_json()
    payload_b = result_b.model_dump_json()
    assert result_a.engine_status["cache_hit"] is False
    assert result_b.engine_status["cache_hit"] is False
    assert "SENTINEL-DOC-A" in payload_a
    assert "SENTINEL-DOC-B" not in payload_a
    assert "SENTINEL-DOC-B" in payload_b
    assert "SENTINEL-DOC-A" not in payload_b


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
