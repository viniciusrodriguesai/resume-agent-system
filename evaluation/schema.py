from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrievalCandidate(BaseModel):
    """A synthetic or anonymized passage that can be ranked for a query."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=10_000)


class RetrievalCase(BaseModel):
    """One labeled retrieval query with explicit relevance judgments."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1, max_length=80)
    query: str = Field(min_length=1, max_length=2_000)
    candidates: list[RetrievalCandidate] = Field(min_length=1, max_length=100)
    relevant_candidate_ids: list[str] = Field(min_length=1, max_length=100)
    data_origin: Literal["synthetic", "anonymized"] = "synthetic"
    language: str = Field(default="pt-BR", min_length=2, max_length=20)

    @model_validator(mode="after")
    def validate_relevance_judgments(self) -> RetrievalCase:
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate_id values must be unique within a case")
        relevant_ids = set(self.relevant_candidate_ids)
        if len(relevant_ids) != len(self.relevant_candidate_ids):
            raise ValueError("relevant_candidate_ids must not contain duplicates")
        unknown_ids = relevant_ids - set(candidate_ids)
        if unknown_ids:
            raise ValueError(
                "relevant_candidate_ids reference unknown candidates: "
                + ", ".join(sorted(unknown_ids))
            )
        return self


class AnalysisCase(BaseModel):
    """A privacy-safe end-to-end pipeline case with requirement-level labels."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1, max_length=80)
    resume_text: str = Field(min_length=10, max_length=30_000)
    job_text: str = Field(min_length=10, max_length=30_000)
    expected_status_by_requirement: dict[
        str,
        Literal["matched", "partial", "missing"],
    ] = Field(min_length=1, max_length=30)
    strictness: Literal["flexível", "equilibrado", "conservador"] = "equilibrado"
    data_origin: Literal["synthetic", "anonymized"] = "synthetic"
