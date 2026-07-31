from __future__ import annotations

from resume_ai.domain.models import AgentTrace, EvidenceMatch, ScoreSummary
from resume_ai.domain.scoring import calculate_score

from .base import run_agent


class ScoringAgent:
    name = "Agente de Pontuação Explicável"

    def run(self, matches: list[EvidenceMatch], strictness: str) -> tuple[ScoreSummary, AgentTrace]:
        return run_agent(
            self.name,
            lambda: calculate_score(matches, strictness),
            lambda result: f"Compatibilidade {result.level}: {result.overall_score}%.",
            lambda result: min(0.98, 0.55 + 0.004 * result.overall_score),
        )
