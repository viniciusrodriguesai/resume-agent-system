from __future__ import annotations

import re
import uuid

from resume_ai.domain.models import AgentTrace, JobProfile, Requirement
from resume_ai.settings import Settings
from resume_ai.utils.text import normalize, split_chunks

from .base import run_agent
from .catalog import aliases_for, category_for

REQUIRED_MARKERS = ("obrigatório", "obrigatorio", "requisito", "required", "must", "necessário", "necessario")
DESIRED_MARKERS = ("desejável", "desejavel", "diferencial", "desirable", "preferred", "nice to have")
RESPONSIBILITY_MARKERS = ("responsabilidades", "responsibilities", "atividades", "atribuições", "atribuicoes")
TITLE_MARKERS = ("estágio", "estagio", "intern", "analista", "cientista", "engenheiro", "developer", "desenvolvedor")


class JobAgent:
    name = "Agente de Vaga"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, text: str) -> tuple[JobProfile, AgentTrace]:
        def action() -> JobProfile:
            lines = [line.strip(" •-*	") for line in text.splitlines() if line.strip()]
            title = next((line for line in lines[:8] if any(marker in normalize(line) for marker in TITLE_MARKERS)), lines[0] if lines else "Vaga não identificada")
            section = "neutral"
            requirements: list[Requirement] = []
            responsibilities: list[str] = []
            seen: set[str] = set()
            for line in lines:
                normalized = normalize(line)
                if len(line) < 4:
                    continue
                if any(marker in normalized for marker in RESPONSIBILITY_MARKERS):
                    section = "responsibilities"
                    continue
                if any(marker in normalized for marker in DESIRED_MARKERS) and len(line.split()) < 8:
                    section = "desired"
                    continue
                if any(marker in normalized for marker in REQUIRED_MARKERS) and len(line.split()) < 8:
                    section = "required"
                    continue
                bullet_like = line.startswith(("-", "•", "*")) or len(line) <= 220
                if section == "responsibilities":
                    if bullet_like:
                        responsibilities.append(line)
                    continue
                priority = "desired" if section == "desired" else "required" if section == "required" else "neutral"
                if line == title or len(line.split()) > 35:
                    continue
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
            return JobProfile(title=title, requirements=requirements, responsibilities=responsibilities[:15])

        return run_agent(
            self.name,
            action,
            lambda result: f"{len(result.requirements)} requisitos estruturados para “{result.title}”.",
            lambda result: min(0.96, 0.55 + 0.02 * min(len(result.requirements), 15)),
        )
