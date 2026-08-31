from __future__ import annotations

from pathlib import Path

import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.settings import Settings

FIXTURES = Path(__file__).parents[1] / "fixtures" / "v605"


def analyze_fixture(
    tmp_path,
    resume_name: str,
    job_name: str,
    *,
    profile: str,
    strictness: str,
) -> AnalysisResult:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        presidio_enabled=False,
        history_enabled=False,
        cache_enabled=False,
    )
    return ResumeAnalysisService(settings).analyze(
        AnalysisRequest(
            resume_text=(FIXTURES / resume_name).read_text(encoding="utf-8"),
            job_text=(FIXTURES / job_name).read_text(encoding="utf-8"),
            profile=profile,
            strictness=strictness,
        )
    )


@pytest.mark.parametrize(
    ("profile", "strictness"),
    [("balanced", "equilibrado"), ("complete", "conservador")],
)
def test_professional_fixture_enforces_each_requirement_intent(
    tmp_path,
    profile: str,
    strictness: str,
) -> None:
    result = analyze_fixture(
        tmp_path / profile,
        "professional_resume.txt",
        "professional_job.txt",
        profile=profile,
        strictness=strictness,
    )
    matches = {match.requirement.text: match for match in result.matches}

    python = matches["Experiência profissional com Python"]
    postgresql = matches["Experiência profissional com PostgreSQL"]
    docker = matches["Experiência com Docker"]
    kubernetes = matches["Experiência com Kubernetes em produção"]
    redis = matches["Experiência com Redis em produção"]

    assert python.status == "matched"
    assert python.top_candidates[0].professional_experience is True
    assert python.top_candidates[0].production_experience is True
    assert "produção" in (python.evidence or "")
    assert postgresql.status == "matched"
    assert postgresql.top_candidates[0].professional_experience is True
    assert docker.status == "matched"
    assert docker.top_candidates[0].operational_experience is True
    assert kubernetes.status != "matched"
    assert kubernetes.top_candidates[0].production_experience is False
    assert redis.status == "matched"
    assert redis.top_candidates[0].production_experience is True


@pytest.mark.parametrize(
    ("profile", "strictness"),
    [("balanced", "equilibrado"), ("complete", "conservador")],
)
def test_personal_only_fixture_never_becomes_professional_or_production_match(
    tmp_path,
    profile: str,
    strictness: str,
) -> None:
    result = analyze_fixture(
        tmp_path / profile,
        "personal_only_resume.txt",
        "personal_only_job.txt",
        profile=profile,
        strictness=strictness,
    )

    assert result.matches
    assert all(match.status != "matched" for match in result.matches)
    assert all(
        not candidate.professional_experience
        for match in result.matches
        for candidate in match.top_candidates
    )
    assert all(
        not candidate.production_experience
        for match in result.matches
        for candidate in match.top_candidates
    )
