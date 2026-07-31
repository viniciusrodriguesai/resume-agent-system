from __future__ import annotations

import re

from resume_ai.domain.models import AgentTrace, CandidateProfile
from resume_ai.settings import Settings
from resume_ai.utils.text import normalize, split_chunks

from .base import run_agent
from .catalog import detect_skills

EDUCATION_MARKERS = ("universidade", "faculdade", "bacharel", "graduação", "graduacao", "degree", "university", "student")
EXPERIENCE_MARKERS = ("experiência", "experiencia", "estágio", "estagio", "trabalhei", "atuei", "desenvolvi", "implementei", "criei", "research", "experience", "developed", "implemented")
PROJECT_MARKERS = ("projeto", "project", "desenvolvi", "developed", "construí", "construi", "built", "implementei", "implemented")


class CandidateAgent:
    name = "Agente de Currículo"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, original: str, anonymized: str) -> tuple[CandidateProfile, AgentTrace]:
        def action() -> CandidateProfile:
            chunks = split_chunks(anonymized, self.settings.max_chunk_chars)
            skills = detect_skills(anonymized)
            education = [chunk for chunk in chunks if any(marker in normalize(chunk) for marker in EDUCATION_MARKERS)][:8]
            experience = [chunk for chunk in chunks if any(marker in normalize(chunk) for marker in EXPERIENCE_MARKERS)][:15]
            projects = [chunk for chunk in chunks if any(marker in normalize(chunk) for marker in PROJECT_MARKERS)][:12]
            years = [
                int(match.group(1))
                for match in re.finditer(r"\b(\d{1,2})\s*(?:anos?|years?)\b", normalize(anonymized))
            ]
            return CandidateProfile(
                skills=skills,
                education=education,
                experience=experience,
                projects=projects,
                chunks=chunks,
                years_mentioned=years,
            )

        return run_agent(
            self.name,
            action,
            lambda result: f"{len(result.skills)} competências e {len(result.chunks)} trechos estruturados.",
            lambda result: min(0.98, 0.45 + 0.03 * min(len(result.skills), 10) + 0.01 * min(len(result.chunks), 20)),
        )
