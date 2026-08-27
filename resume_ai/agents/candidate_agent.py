from __future__ import annotations

import re
from enum import StrEnum

from resume_ai.domain.models import AgentTrace, CandidateProfile
from resume_ai.settings import Settings
from resume_ai.utils.text import normalize, remove_privacy_placeholders, split_chunks

from .base import run_agent
from .catalog import detect_skills

EDUCATION_MARKERS = ("universidade", "faculdade", "bacharel", "graduação", "graduacao", "degree", "university", "student")
EXPERIENCE_MARKERS = ("experiência", "experiencia", "estágio", "estagio", "trabalhei", "atuei", "desenvolvi", "implementei", "criei", "research", "experience", "developed", "implemented")
PROJECT_MARKERS = ("projeto", "project", "desenvolvi", "developed", "construí", "construi", "built", "implementei", "implemented")


class ResumeSection(StrEnum):
    UNKNOWN = "unknown"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    OTHER = "other"


SECTION_HEADINGS: dict[ResumeSection, set[str]] = {
    ResumeSection.EXPERIENCE: {
        "experiencia",
        "experiencia profissional",
        "professional experience",
        "work experience",
        "employment",
    },
    ResumeSection.PROJECTS: {
        "projetos",
        "projetos pessoais",
        "projects",
        "personal projects",
    },
    ResumeSection.EDUCATION: {
        "educacao",
        "formacao",
        "formacao academica",
        "education",
        "academic background",
    },
    ResumeSection.OTHER: {
        "resumo",
        "summary",
        "tecnologias",
        "technology",
        "technologies",
        "competencias",
        "skills",
        "conhecimentos",
        "conhecimentos e limitacoes",
        "idiomas",
        "languages",
    },
}


def _resume_section(line: str) -> ResumeSection | None:
    normalized = normalize(line.rstrip(":"))
    for section, headings in SECTION_HEADINGS.items():
        if normalized in headings:
            return section
    return None


def _section_aware_profile_chunks(
    text: str,
    max_chunk_chars: int,
) -> tuple[list[str], list[str], list[str]]:
    education: list[str] = []
    experience: list[str] = []
    projects: list[str] = []
    section = ResumeSection.UNKNOWN

    for raw_line in text.splitlines():
        detected_section = _resume_section(raw_line.strip())
        if detected_section is not None:
            section = detected_section
            continue
        line_chunks = split_chunks(raw_line, max_chunk_chars)
        for chunk in line_chunks:
            normalized = normalize(chunk)
            if section is ResumeSection.EXPERIENCE:
                experience.append(chunk)
            elif section is ResumeSection.PROJECTS:
                projects.append(chunk)
            elif section is ResumeSection.EDUCATION:
                education.append(chunk)
            elif section is ResumeSection.UNKNOWN:
                if any(marker in normalized for marker in EDUCATION_MARKERS):
                    education.append(chunk)
                if any(marker in normalized for marker in EXPERIENCE_MARKERS):
                    experience.append(chunk)
                if any(marker in normalized for marker in PROJECT_MARKERS):
                    projects.append(chunk)

    return education[:12], experience[:30], projects[:20]


class CandidateAgent:
    name = "Agente de Currículo"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, _original: str, anonymized: str) -> tuple[CandidateProfile, AgentTrace]:
        def action() -> CandidateProfile:
            public_text = remove_privacy_placeholders(anonymized)
            chunks = split_chunks(public_text, self.settings.max_chunk_chars)
            skills = detect_skills(public_text)
            education, experience, projects = _section_aware_profile_chunks(
                public_text,
                self.settings.max_chunk_chars,
            )
            years = [
                int(match.group(1))
                for match in re.finditer(r"\b(\d{1,2})\s*(?:anos?|years?)\b", normalize(public_text))
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
            lambda result: f"{len(result.skills)} competências e {len(result.chunks)} trechos específicos estruturados.",
            lambda result: min(0.98, 0.45 + 0.03 * min(len(result.skills), 10) + 0.01 * min(len(result.chunks), 20)),
            warnings=lambda result: ["no-resume-chunks"] if not result.chunks else [],
            evidence=lambda result: [f"skill:{normalize(skill.name)}" for skill in result.skills],
            metadata=lambda result: {
                "skill_count": len(result.skills),
                "chunk_count": len(result.chunks),
                "education_count": len(result.education),
                "experience_count": len(result.experience),
                "project_count": len(result.projects),
            },
        )
