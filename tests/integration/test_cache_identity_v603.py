from __future__ import annotations

import json

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings


def analyze_twice(tmp_path):
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
        cache_enabled=True,
    )
    service = ResumeAnalysisService(settings)
    request = AnalysisRequest(
        resume_text="Candidato sintético\nUtilizei Python em produção.",
        job_text="""BACKEND ENGINEER
REQUISITOS OBRIGATÓRIOS
- Experiência com Python
""",
    )
    return service, service.analyze(request), service.analyze(request)


def test_cache_hit_report_id_matches_result_id(tmp_path):
    _, first, second = analyze_twice(tmp_path)

    assert first.engine_status["cache_hit"] is False
    assert second.engine_status["cache_hit"] is True
    assert first.analysis_id != second.analysis_id
    assert f"`{first.analysis_id}`" in first.markdown_report
    assert f"`{second.analysis_id}`" in second.markdown_report
    assert first.analysis_id not in second.markdown_report


def test_cached_export_identity_is_consistent(tmp_path):
    service, first, second = analyze_twice(tmp_path)

    exported = json.loads(service.to_json(second))

    assert exported["analysis_id"] == second.analysis_id
    assert f"`{second.analysis_id}`" in exported["markdown_report"]
    assert first.analysis_id not in exported["markdown_report"]
    assert second.engine_status["cached_execution"] is True
    assert second.engine_status["original_processing_timings"] == first.timings_ms
    assert set(second.timings_ms) == {"cache_lookup", "report_regeneration"}
    assert all(duration >= 0.0 for duration in second.timings_ms.values())


def test_cache_hit_preserves_score_requirements_and_match_semantics(tmp_path):
    _, first, second = analyze_twice(tmp_path)

    assert first.score == second.score
    assert first.job.requirements == second.job.requirements
    assert [
        (match.requirement.id, match.status, match.final_score, match.evidence)
        for match in first.matches
    ] == [
        (match.requirement.id, match.status, match.final_score, match.evidence)
        for match in second.matches
    ]
