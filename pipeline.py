from __future__ import annotations

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.settings import Settings

STRICTNESS = {
    "flexible": "flexível",
    "balanced": "equilibrado",
    "conservative": "conservador",
}


def run_pipeline(
    resume_text: str,
    job_text: str,
    strictness: str = "Balanced",
) -> AnalysisResult:
    normalized_strictness = STRICTNESS.get(strictness.lower(), strictness.lower())
    request = AnalysisRequest(
        resume_text=resume_text,
        job_text=job_text,
        strictness=normalized_strictness,
    )
    return ResumeAnalysisService(Settings.for_profile("demo")).analyze(request)
