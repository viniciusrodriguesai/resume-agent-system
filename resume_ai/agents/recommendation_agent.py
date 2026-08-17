from __future__ import annotations

from resume_ai.domain.models import AgentTrace, CandidateProfile, EvidenceMatch, Recommendation

from .base import run_agent


class RecommendationAgent:
    name = "Agente de Recomendações"

    def run(self, candidate: CandidateProfile, matches: list[EvidenceMatch]) -> tuple[list[Recommendation], AgentTrace]:
        required_missing = [
            match
            for match in matches
            if match.requirement.priority == "required" and match.status == "missing"
        ][:6]
        required_partial = [
            match
            for match in matches
            if match.requirement.priority == "required" and match.status == "partial"
        ][:6]
        desired_missing = [
            match
            for match in matches
            if match.requirement.priority == "desired" and match.status == "missing"
        ][:5]

        def action() -> list[Recommendation]:
            recommendations: list[Recommendation] = []
            for item in required_missing:
                recommendations.append(Recommendation(
                    priority="alta",
                    category="lacuna obrigatória",
                    action=f"Desenvolva evidência real para “{item.requirement.text}”. Não declare domínio antes de estudar ou aplicar a competência.",
                ))
            for item in required_partial:
                recommendations.append(Recommendation(
                    priority="alta",
                    category="evidência insuficiente",
                    action=f"Reescreva a experiência ligada a “{item.requirement.text}” indicando ação, tecnologia e resultado mensurável.",
                ))
            for item in desired_missing:
                recommendations.append(Recommendation(
                    priority="média",
                    category="desenvolvimento",
                    action=f"Considere estudar ou praticar “{item.requirement.text}”, pois aparece como diferencial.",
                ))
            if not candidate.projects:
                recommendations.append(Recommendation(
                    priority="média", category="portfólio",
                    action="Inclua projetos com problema, dados, tecnologias, contribuição individual e resultado.",
                ))
            if not recommendations:
                recommendations.append(Recommendation(
                    priority="baixa", category="refinamento",
                    action="Mantenha o currículo objetivo e acrescente métricas concretas às experiências mais relevantes.",
                ))
            return recommendations

        relevant_matches = [*required_missing, *required_partial, *desired_missing]
        return run_agent(
            self.name,
            action,
            lambda result: f"{len(result)} recomendações priorizadas.",
            lambda _: 0.90,
            evidence=lambda _: [
                f"requirement-id:{match.requirement.id}"
                for match in relevant_matches
            ],
            metadata=lambda result: {
                "recommendation_count": len(result),
                "required_missing_count": len(required_missing),
                "required_partial_count": len(required_partial),
                "desired_missing_count": len(desired_missing),
            },
        )
