from __future__ import annotations

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
from resume_ai.application.pipeline import AnalysisAgents
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.infrastructure.privacy import PrivacyService
from resume_ai.settings import Settings


def build_analysis_agents(settings: Settings, engine: EmbeddingEngine) -> AnalysisAgents:
    """Compose the default application graph at the system boundary."""
    return AnalysisAgents(
        privacy=PrivacyAgent(PrivacyService(settings)),
        candidate=CandidateAgent(settings),
        job=JobAgent(settings),
        evidence=EvidenceAgent(engine),
        scoring=ScoringAgent(),
        review=ReviewAgent(),
        recommendation=RecommendationAgent(),
        report=ReportAgent(),
    )
