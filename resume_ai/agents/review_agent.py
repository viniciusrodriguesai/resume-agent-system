from __future__ import annotations

from resume_ai.domain.models import AgentTrace, EvidenceMatch, ScoreSummary

from .base import run_agent


class ReviewAgent:
    name = "Agente Revisor"

    def run(self, score: ScoreSummary, matches: list[EvidenceMatch]) -> tuple[str, AgentTrace]:
        borderline = [item for item in matches if 0.30 <= item.final_score <= 0.72]
        required_missing = [
            item
            for item in matches
            if item.requirement.priority == "required" and item.status == "missing"
        ]
        reviewed_items = {
            item.requirement.id: item
            for item in [*required_missing, *borderline]
        }

        def action() -> str:
            if score.required_missing:
                return f"A análise encontrou {score.required_missing} lacuna(s) obrigatória(s). Recomenda-se revisão humana antes de qualquer decisão."
            if borderline:
                return f"A nota é consistente, mas {len(borderline)} requisito(s) estão próximos dos limiares e merecem inspeção manual."
            return "A nota está consistente com as evidências recuperadas e os pesos configurados."

        return run_agent(
            self.name,
            action,
            lambda result: result,
            lambda _: 0.88,
            warnings=lambda _: [
                *(["human-review-required"] if required_missing else []),
                *(["borderline-requirements"] if borderline else []),
            ],
            evidence=lambda _: [
                f"requirement-id:{item.requirement.id}"
                for item in reviewed_items.values()
            ],
            metadata=lambda _: {
                "required_missing_count": len(required_missing),
                "borderline_count": len(borderline),
            },
        )
