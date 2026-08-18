from __future__ import annotations

from typing import Protocol

from resume_ai.domain.models import AnalysisResult


class AnalysisHistoryWriter(Protocol):
    """Application boundary for persisting privacy-safe analysis summaries."""

    def save(self, result: AnalysisResult) -> None: ...
