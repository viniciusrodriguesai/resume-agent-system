from __future__ import annotations

import uuid

from resume_ai.domain.models import AgentTrace, JobProfile, Requirement
from resume_ai.settings import Settings
from resume_ai.utils.text import normalize

from .base import run_agent
from .catalog import aliases_for, category_for

REQUIRED_MARKERS = (
    "requisitos obrigatorios", "requisito obrigatorio", "obrigatorio", "required", "must have",
)
DESIRED_MARKERS = (
    "requisitos desejaveis", "requisito desejavel", "desejavel", "diferenciais", "diferencial",
    "desirable", "preferred", "nice to have",
)
RESPONSIBILITY_MARKERS = (
    "responsabilidades", "responsibilities", "atividades", "atribuicoes",
)
TITLE_MARKERS = (
    "estágio", "estagio", "intern", "analista", "cientista", "engenheiro", "developer", "desenvolvedor",
)
BULLET_PREFIXES = ("-", "•", "*", "–", "—")


class JobAgent:
    name = "Agente de Vaga"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, text: str) -> tuple[JobProfile, AgentTrace]:
        def action() -> JobProfile:
            raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
            clean_lines = [line.strip(" •-*–—\t") for line in raw_lines]
            title = next(
                (line for line in clean_lines[:8] if any(marker in normalize(line) for marker in TITLE_MARKERS)),
                clean_lines[0] if clean_lines else "Vaga não identificada",
            )

            section = "preamble"
            requirements: list[Requirement] = []
            responsibilities: list[str] = []
            seen: set[str] = set()

            for raw_line, line in zip(raw_lines, clean_lines, strict=True):
                normalized = normalize(line)
                if len(line) < 2:
                    continue
                is_bullet = raw_line.lstrip().startswith(BULLET_PREFIXES)
                is_short_header = len(line.split()) <= 8

                if is_short_header and any(marker in normalized for marker in RESPONSIBILITY_MARKERS):
                    section = "responsibilities"
                    continue
                if is_short_header and any(marker in normalized for marker in DESIRED_MARKERS):
                    section = "desired"
                    continue
                if is_short_header and any(marker in normalized for marker in REQUIRED_MARKERS):
                    section = "required"
                    continue

                if line == title:
                    continue

                if section == "responsibilities":
                    if is_bullet or len(line) <= 220:
                        responsibilities.append(line.rstrip(".;"))
                    continue

                # Textos introdutórios não são requisitos. Em vagas sem cabeçalhos,
                # bullets ainda podem ser tratados como requisitos neutros.
                if section == "preamble" and not is_bullet:
                    continue

                if len(line.split()) > 35:
                    continue
                priority = "desired" if section == "desired" else "required" if section == "required" else "neutral"
                key = normalize(line)
                if key in seen:
                    continue
                seen.add(key)
                requirements.append(Requirement(
                    id=str(uuid.uuid4()),
                    text=line.rstrip(".;"),
                    priority=priority,  # type: ignore[arg-type]
                    category=category_for(line),
                    aliases=aliases_for(line),
                    source_section=section,
                ))
                if len(requirements) >= self.settings.max_requirements:
                    break

            return JobProfile(
                title=title,
                requirements=requirements,
                responsibilities=responsibilities[:15],
            )

        return run_agent(
            self.name,
            action,
            lambda result: f"{len(result.requirements)} requisitos estruturados para “{result.title}”.",
            lambda result: min(0.96, 0.55 + 0.02 * min(len(result.requirements), 15)),
            warnings=lambda result: ["no-job-requirements"] if not result.requirements else [],
            evidence=lambda result: [
                f"requirement-id:{requirement.id}"
                for requirement in result.requirements
            ],
            metadata=lambda result: {
                "requirement_count": len(result.requirements),
                "required_count": sum(
                    requirement.priority == "required"
                    for requirement in result.requirements
                ),
                "desired_count": sum(
                    requirement.priority == "desired"
                    for requirement in result.requirements
                ),
                "neutral_count": sum(
                    requirement.priority == "neutral"
                    for requirement in result.requirements
                ),
                "responsibility_count": len(result.responsibilities),
            },
        )
