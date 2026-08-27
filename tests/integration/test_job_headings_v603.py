from __future__ import annotations

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings


def test_headings_never_reach_scoring_or_recommendations(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
        cache_enabled=False,
    )
    result = ResumeAnalysisService(settings).analyze(
        AnalysisRequest(
            resume_text="Candidato sintético\nUtilizei Python em produção.",
            job_text="""BACKEND ENGINEER

REQUISITOS OBRIGATÓRIOS

BACKEND
- Experiência com Python

MENSAGERIA
- Experiência com RabbitMQ

CACHE
- Experiência com Redis

OBSERVABILIDADE
- Experiência com Prometheus
""",
        )
    )

    headings = {"BACKEND", "MENSAGERIA", "CACHE", "OBSERVABILIDADE"}
    requirement_texts = {requirement.text for requirement in result.job.requirements}
    match_texts = {match.requirement.text for match in result.matches}
    downstream = "\n".join(
        [
            result.review_summary,
            result.markdown_report,
            ResumeAnalysisService.to_json(result),
            ResumeAnalysisService.to_csv(result),
            *(recommendation.action for recommendation in result.recommendations),
            *(category.category for category in result.score.categories),
        ]
    )

    assert headings.isdisjoint(requirement_texts)
    assert headings.isdisjoint(match_texts)
    assert len(result.matches) == 4
    assert result.score.matched + result.score.partial + result.score.missing == 4
    for heading in headings:
        assert f'Desenvolva evidência real para “{heading}”' not in downstream
