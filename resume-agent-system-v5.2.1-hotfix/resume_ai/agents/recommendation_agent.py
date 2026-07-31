from __future__ import annotations

from resume_ai.domain.models import AgentTrace, CandidateProfile, EvidenceMatch, Recommendation

from .base import run_agent


class RecommendationAgent:
    name = "Agente de Recomendações"

    def run(self, candidate: CandidateProfile, matches: list[EvidenceMatch]) -> tuple[list[Recommendation], AgentTrace]:
        def action() -> list[Recommendation]:
            recommendations: list[Recommendation] = []
            for item in [m for m in matches if m.requirement.priority == "required" and m.status == "missing"][:6]:
                recommendations.append(Recommendation(
                    priority="alta",
                    category="lacuna obrigatória",
                    action=f"Desenvolva evidência real para “{item.requirement.text}”. Não declare domínio antes de estudar ou aplicar a competência.",
                ))
            for item in [m for m in matches if m.requirement.priority == "required" and m.status == "partial"][:6]:
                recommendations.append(Recommendation(
                    priority="alta",
                    category="evidência insuficiente",
                    action=f"Reescreva a experiência ligada a “{item.requirement.text}” indicando ação, tecnologia e resultado mensurável.",
                ))
            for item in [m for m in matches if m.requirement.priority == "desired" and m.status == "missing"][:5]:
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

        return run_agent(self.name, action, lambda result: f"{len(result)} recomendações priorizadas.", lambda _: 0.90)
