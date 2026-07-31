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
