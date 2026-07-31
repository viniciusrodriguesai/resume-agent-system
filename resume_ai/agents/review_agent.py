from __future__ import annotations

from resume_ai.domain.models import AgentTrace, EvidenceMatch, ScoreSummary

from .base import run_agent


class ReviewAgent:
    name = "Agente Revisor"

    def run(self, score: ScoreSummary, matches: list[EvidenceMatch]) -> tuple[str, AgentTrace]:
        def action() -> str:
            borderline = [item for item in matches if 0.30 <= item.final_score <= 0.72]
            if score.required_missing:
                return f"A análise encontrou {score.required_missing} lacuna(s) obrigatória(s). Recomenda-se revisão humana antes de qualquer decisão."
            if borderline:
                return f"A nota é consistente, mas {len(borderline)} requisito(s) estão próximos dos limiares e merecem inspeção manual."
            return "A nota está consistente com as evidências recuperadas e os pesos configurados."

        return run_agent(self.name, action, lambda result: result, lambda _: 0.88)
