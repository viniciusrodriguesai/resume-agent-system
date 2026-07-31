from __future__ import annotations

import csv
import io
import json
import uuid
from dataclasses import dataclass
from typing import Any

from resume_ai.agents import (
    CandidateAgent,
    EvidenceAgent,
    JobAgent,
    PrivacyAgent,
    RecommendationAgent,
    ReportAgent,
    ReviewAgent,
    ScoringAgent,
)
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.infrastructure.cache import SafeResultCache
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.infrastructure.history import HistoryRepository
from resume_ai.infrastructure.observability import METRICS
from resume_ai.infrastructure.privacy import PrivacyService
from resume_ai.infrastructure.telemetry import Telemetry
from resume_ai.settings import Settings
from resume_ai.utils.text import content_hash


class ResumeAnalysisService:
    """Serviço de aplicação independente de Streamlit e FastAPI."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.telemetry = Telemetry(self.settings)
        self.cache = SafeResultCache(self.settings)
        self.engine = EmbeddingEngine(self.settings)
        self.history = HistoryRepository(self.settings)
        self.privacy_agent = PrivacyAgent(PrivacyService(self.settings))
        self.candidate_agent = CandidateAgent(self.settings)
        self.job_agent = JobAgent(self.settings)
        self.evidence_agent = EvidenceAgent(self.engine)
        self.scoring_agent = ScoringAgent()
        self.review_agent = ReviewAgent()
        self.recommendation_agent = RecommendationAgent()
        self.report_agent = ReportAgent()

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        timings: dict[str, float] = {}
        key = content_hash(request.profile, request.strictness, request.resume_text, request.job_text)
        cached = self.cache.get(key)
        if cached:
            return AnalysisResult.model_validate(cached)

        traces = []
        with self.telemetry.timer("total", timings):
            with self.telemetry.timer("privacy", timings):
                (anonymized, privacy), trace = self.privacy_agent.run(request.resume_text)
                traces.append(trace)
            with self.telemetry.timer("candidate", timings):
                candidate, trace = self.candidate_agent.run(request.resume_text, anonymized)
                traces.append(trace)
            with self.telemetry.timer("job", timings):
                job, trace = self.job_agent.run(request.job_text)
                traces.append(trace)
            with self.telemetry.timer("evidence", timings):
                matches, trace = self.evidence_agent.run(candidate, job, self.settings.top_k)
                traces.append(trace)
            with self.telemetry.timer("scoring", timings):
                score, trace = self.scoring_agent.run(matches, request.strictness)
                traces.append(trace)
            with self.telemetry.timer("review", timings):
                review, trace = self.review_agent.run(score, matches)
                traces.append(trace)
            with self.telemetry.timer("recommendations", timings):
                recommendations, trace = self.recommendation_agent.run(candidate, matches)
                traces.append(trace)

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
                engine_status={**self.engine.status, "memory_mb": self.telemetry.process_memory_mb()},
                timings_ms=timings,
            )
            with self.telemetry.timer("report", timings):
                markdown, trace = self.report_agent.run(result)
                result.markdown_report = markdown
                result.traces.append(trace)

        result.timings_ms = dict(timings)
        payload = result.model_dump(mode="json")
        self.cache.set(key, payload)
        self.history.save(result)
        METRICS.record_success(request.profile, result.timings_ms.get("total", 0.0) / 1000, result.score.overall_score)
        self.telemetry.info(
            "analysis_completed",
            analysis_id=result.analysis_id,
            profile=request.profile,
            score=result.score.overall_score,
            duration_ms=result.timings_ms.get("total"),
        )
        return result

    @staticmethod
    def to_json(result: AnalysisResult) -> str:
        return result.model_dump_json(indent=2)

    @staticmethod
    def to_csv(result: AnalysisResult) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["requisito", "prioridade", "categoria", "status", "score", "evidencia"])
        for match in result.matches:
            writer.writerow([
                match.requirement.text,
                match.requirement.priority,
                match.requirement.category,
                match.status,
                f"{match.final_score:.4f}",
                match.evidence or "",
            ])
        return output.getvalue()
