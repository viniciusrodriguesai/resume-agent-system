from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Priority = Literal["required", "desired", "neutral"]
MatchStatus = Literal["matched", "partial", "missing"]


class AgentTrace(BaseModel):
    agent: str
    summary: str
    duration_ms: float = 0.0
    confidence: float = 0.0
    alerts: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PrivacyEntity(BaseModel):
    entity_type: str
    replacement: str
    count: int = 1


class PrivacyReport(BaseModel):
    method: str
    entities: list[PrivacyEntity] = Field(default_factory=list)
    total_removed: int = 0
    raw_document_stored: bool = False
    anonymized_document_stored: bool = False


class Skill(BaseModel):
    name: str
    category: str = "other"
    aliases: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    candidate_name: str = "Candidato anonimizado"
    skills: list[Skill] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    chunks: list[str] = Field(default_factory=list)
    years_mentioned: list[int] = Field(default_factory=list)


class Requirement(BaseModel):
    id: str
    text: str
    priority: Priority = "neutral"
    category: str = "other"
    aliases: list[str] = Field(default_factory=list)
    source_section: str = ""


class JobProfile(BaseModel):
    title: str = "Vaga não identificada"
    requirements: list[Requirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


class EvidenceCandidate(BaseModel):
    text: str
    lexical_score: float = 0.0
    fuzzy_score: float = 0.0
    semantic_score: float = 0.0
    reranker_score: float = 0.0
    final_score: float = 0.0
    retrieval_method: str = "lexical"


class EvidenceMatch(BaseModel):
    requirement: Requirement
    evidence: str | None = None
    lexical_score: float = 0.0
    fuzzy_score: float = 0.0
    semantic_score: float = 0.0
    reranker_score: float = 0.0
    final_score: float = 0.0
    status: MatchStatus = "missing"
    explanation: str = ""
    top_candidates: list[EvidenceCandidate] = Field(default_factory=list)


class CategoryScore(BaseModel):
    category: str
    score: int
    matched: int = 0
    partial: int = 0
    missing: int = 0


class ScoreSummary(BaseModel):
    overall_score: int
    level: Literal["excelente", "alta", "boa", "moderada", "baixa"]
    matched: int
    partial: int
    missing: int
    required_missing: int
    desired_missing: int = 0
    neutral_missing: int = 0
    categories: list[CategoryScore] = Field(default_factory=list)
    thresholds: dict[str, float] = Field(default_factory=dict)
    explanation: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    priority: Literal["alta", "média", "baixa"]
    category: str
    action: str


class AnalysisRequest(BaseModel):
    resume_text: str = Field(min_length=10)
    job_text: str = Field(min_length=10)
    profile: Literal["demo", "balanced", "complete"] = "demo"
    strictness: Literal["flexível", "equilibrado", "conservador"] = "equilibrado"


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    analysis_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    profile: str
    strictness: str
    candidate: CandidateProfile
    job: JobProfile
    privacy: PrivacyReport
    matches: list[EvidenceMatch]
    score: ScoreSummary
    recommendations: list[Recommendation]
    review_summary: str
    traces: list[AgentTrace]
    engine_status: dict[str, Any] = Field(default_factory=dict)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    markdown_report: str = ""


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "5.2.0"
    profile: str
    model_loaded: bool
    memory_mb: float | None = None
