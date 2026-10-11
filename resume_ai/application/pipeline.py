from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol, TypeVar

from resume_ai.domain.models import (
    AgentTrace,
    AnalysisRequest,
    AnalysisResult,
    CandidateProfile,
    EvidenceMatch,
    JobProfile,
    PrivacyReport,
    Recommendation,
    ScoreSummary,
)


class PrivacyStage(Protocol):
    def run(self, text: str) -> tuple[tuple[str, PrivacyReport], AgentTrace]: ...


class CandidateStage(Protocol):
    def run(
        self, original: str, anonymized: str, /
    ) -> tuple[CandidateProfile, AgentTrace]: ...


class JobStage(Protocol):
    def run(self, text: str) -> tuple[JobProfile, AgentTrace]: ...


class EvidenceStage(Protocol):
    def run(
        self, candidate: CandidateProfile, job: JobProfile, top_k: int
    ) -> tuple[list[EvidenceMatch], AgentTrace]: ...


class ScoringStage(Protocol):
    def run(
        self, matches: list[EvidenceMatch], strictness: str
    ) -> tuple[ScoreSummary, AgentTrace]: ...


class ReviewStage(Protocol):
    def run(self, score: ScoreSummary, matches: list[EvidenceMatch]) -> tuple[str, AgentTrace]: ...


class RecommendationStage(Protocol):
    def run(
        self, candidate: CandidateProfile, matches: list[EvidenceMatch]
    ) -> tuple[list[Recommendation], AgentTrace]: ...


class ReportStage(Protocol):
    def run(self, result: AnalysisResult) -> tuple[str, AgentTrace]: ...


@dataclass(frozen=True)
class AnalysisAgents:
    """Replaceable stage implementations consumed by the application pipeline."""

    privacy: PrivacyStage
    candidate: CandidateStage
    job: JobStage
    evidence: EvidenceStage
    scoring: ScoringStage
    review: ReviewStage
    recommendation: RecommendationStage
    report: ReportStage


AgentTraceHandler = Callable[[str, AgentTrace], None]
T = TypeVar("T")


class AnalysisPipeline:
    """Runs the domain stages in their required order and returns one result."""

    def __init__(self, agents: AnalysisAgents, top_k: int) -> None:
        self.agents = agents
        self.top_k = top_k

    def run(
        self,
        request: AnalysisRequest,
        *,
        engine_status: dict[str, object],
        memory_mb: float,
        on_agent_result: AgentTraceHandler,
    ) -> AnalysisResult:
        timings: dict[str, float] = {}
        traces: list[AgentTrace] = []
        total_started = perf_counter()

        (anonymized, privacy), trace = self._run_stage(
            "privacy", lambda: self.agents.privacy.run(request.resume_text), timings
        )
        traces.append(trace)
        on_agent_result("privacy", trace)

        candidate, trace = self._run_stage(
            "candidate",
            lambda: self.agents.candidate.run(request.resume_text, anonymized),
            timings,
        )
        traces.append(trace)
        on_agent_result("candidate", trace)

        job, trace = self._run_stage(
            "job", lambda: self.agents.job.run(request.job_text), timings
        )
        traces.append(trace)
        on_agent_result("job", trace)

        matches, trace = self._run_stage(
            "evidence",
            lambda: self.agents.evidence.run(candidate, job, self.top_k),
            timings,
        )
        traces.append(trace)
        on_agent_result("evidence", trace)

        score, trace = self._run_stage(
            "scoring",
            lambda: self.agents.scoring.run(matches, request.strictness),
            timings,
        )
        traces.append(trace)
        on_agent_result("scoring", trace)

        review, trace = self._run_stage(
            "review", lambda: self.agents.review.run(score, matches), timings
        )
        traces.append(trace)
        on_agent_result("review", trace)

        recommendations, trace = self._run_stage(
            "recommendations",
            lambda: self.agents.recommendation.run(candidate, matches),
            timings,
        )
        traces.append(trace)
        on_agent_result("recommendations", trace)

        result = AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            profile=request.profile,
            strictness=request.strictness,
            candidate=candidate,
            job=job,
            privacy=privacy,
            matches=matches,
            score=score,
            recommendations=recommendations,
            review_summary=review,
            traces=traces,
            engine_status={**engine_status, "memory_mb": memory_mb, "cache_hit": False},
            timings_ms=timings,
        )
        markdown, trace = self._run_stage(
            "report", lambda: self.agents.report.run(result), timings
        )
        result.markdown_report = markdown
        result.traces.append(trace)
        on_agent_result("report", trace)

        timings["total"] = round((perf_counter() - total_started) * 1000, 2)
        result.timings_ms = dict(timings)
        return result

    @staticmethod
    def _run_stage(
        stage: str,
        action: Callable[[], T],
        timings: dict[str, float],
    ) -> T:
        started = perf_counter()
        try:
            return action()
        finally:
            timings[stage] = round((perf_counter() - started) * 1000, 2)
