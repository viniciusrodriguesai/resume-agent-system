from __future__ import annotations

from resume_ai.domain.models import AgentTrace, AnalysisResult

from .base import run_agent

STATUS_LABELS = {"matched": "Correspondido", "partial": "Parcial", "missing": "Ausente"}
PRIORITY_LABELS = {"required": "Obrigatório", "desired": "Desejável", "neutral": "Neutro"}
PROFILE_LABELS = {"demo": "Demonstração", "balanced": "Equilibrado", "complete": "Completo"}


class ReportAgent:
    name = "Agente de Relatório"

    def run(self, result: AnalysisResult) -> tuple[str, AgentTrace]:
        def action() -> str:
            lines = [
                "# Relatório de compatibilidade curricular",
                "",
                f"- **ID:** `{result.analysis_id}`",
                f"- **Vaga:** {result.job.title}",
                f"- **Perfil de execução:** {PROFILE_LABELS.get(result.profile, result.profile)}",
                f"- **Compatibilidade:** {result.score.overall_score}% ({result.score.level})",
                f"- **Privacidade:** {result.privacy.total_removed} identificador(es) removido(s) por {result.privacy.method}",
                "",
                "## Resumo",
                "",
                f"Correspondidos: **{result.score.matched}** · Parcialmente atendidos: **{result.score.partial}** · Desejáveis ausentes: **{result.score.desired_missing}** · Obrigatórios ausentes: **{result.score.required_missing}**",
                "",
                "## Evidências por requisito",
                "",
            ]
            for match in result.matches:
                lines.extend([
                    f"### {match.requirement.text}",
                    f"- Prioridade: **{PRIORITY_LABELS.get(match.requirement.priority, match.requirement.priority)}**",
                    f"- Status: **{STATUS_LABELS.get(match.status, match.status)}**",
                    f"- Pontuação final: **{match.final_score:.2f}**",
                    f"- Evidência: {match.evidence or 'Não localizada'}",
                    "",
                ])
            lines.extend(["## Recomendações", ""])
            for item in result.recommendations:
                lines.append(f"- **{item.priority.title()} — {item.category}:** {item.action}")
            lines.extend([
                "",
                "## Limitação",
                "",
                "O sistema apoia análise humana e não deve tomar decisões de contratação automaticamente.",
            ])
            return "\n".join(lines)

        return run_agent(
            self.name,
            action,
            lambda _: "Relatórios Markdown, JSON e CSV preparados.",
            lambda _: 0.98,
        )
