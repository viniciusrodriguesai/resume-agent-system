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
            warnings=lambda result: (
                ["required-requirements-missing"]
                if result.required_missing
                else []
            ),
            evidence=lambda _: [
                f"requirement-id:{match.requirement.id}"
                for match in matches
                if match.status in {"matched", "partial"}
            ],
            metadata=lambda result: {
                "overall_score": result.overall_score,
                "matched_count": result.matched,
                "partial_count": result.partial,
                "missing_count": result.missing,
                "required_missing_count": result.required_missing,
            },
        )
