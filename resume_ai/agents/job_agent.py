from __future__ import annotations

import uuid
from dataclasses import dataclass

from resume_ai.domain.models import AgentTrace, JobProfile, Priority, Requirement
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
ALTERNATIVE_MARKERS = ("requisitos alternativos", "alternative requirements")
INFRASTRUCTURE_MARKERS = ("requisitos de infraestrutura", "infrastructure requirements", "infraestrutura")
TECHNICAL_MARKERS = ("requisitos tecnicos", "technical requirements")
TITLE_MARKERS = (
    "estagio", "intern", "analista", "cientista", "engenheiro", "engineer", "developer", "desenvolvedor",
    "arquiteto", "architect", "especialista", "specialist",
)
BULLET_PREFIXES = ("-", "•", "*", "–", "—")
GENERIC_QUALIFICATION_HEADINGS = {"qualifications", "qualification"}


@dataclass(frozen=True)
class SectionContext:
    section: str = "preamble"
    priority: Priority = "neutral"
    subsection: str | None = None


def _context_for_section(section: str) -> SectionContext:
    priority: Priority = (
        "desired"
        if section == "desired"
        else "required"
        if section in {"required", "infrastructure", "technical"}
        else "neutral"
    )
    return SectionContext(section=section, priority=priority)


def _looks_like_generic_subheading(
    line: str,
    *,
    is_bullet: bool,
    next_is_bullet: bool,
    context: SectionContext,
) -> bool:
    """Recognize a structural label without maintaining a vocabulary of labels."""
    if (
        is_bullet
        or not next_is_bullet
        or context.section in {"preamble", "responsibilities"}
        or len(line) > 80
        or len(line.split()) > 7
        or line.endswith((".", "!", "?", ";"))
    ):
        return False

    stripped = line.rstrip(":").strip()
    letters = [character for character in stripped if character.isalpha()]
    if not letters:
        return False
    uppercase_ratio = sum(character.isupper() for character in letters) / len(letters)
    significant_words = [
        word
        for word in stripped.replace("/", " ").replace("&", " ").split()
        if normalize(word) not in {"de", "da", "do", "das", "dos", "e", "and", "of"}
    ]
    title_case = bool(significant_words) and all(word[0].isupper() for word in significant_words)
    return line.endswith(":") or uppercase_ratio >= 0.72 or title_case


def _heading_section(line: str, *, is_bullet: bool) -> str | None:
    if is_bullet or len(line.split()) > 8:
        return None
    normalized = normalize(line)
    if any(marker in normalized for marker in RESPONSIBILITY_MARKERS):
        return "responsibilities"
    if any(marker in normalized for marker in DESIRED_MARKERS):
        return "desired"
    if any(marker in normalized for marker in ALTERNATIVE_MARKERS):
        return "alternative"
    if any(marker in normalized for marker in INFRASTRUCTURE_MARKERS):
        return "infrastructure"
    if any(marker in normalized for marker in TECHNICAL_MARKERS):
        return "technical"
    if any(marker in normalized for marker in REQUIRED_MARKERS):
        return "required"
    first_word = normalized.split(maxsplit=1)[0] if normalized else ""
    if first_word in {"requisito", "requisitos", "requirement", "requirements"}:
        return "required"
    if normalized in GENERIC_QUALIFICATION_HEADINGS:
        return "neutral"
    return None


def _is_job_title(raw_line: str, line: str) -> bool:
    is_bullet = raw_line.lstrip().startswith(BULLET_PREFIXES)
    if is_bullet or len(line) > 120 or len(line.split()) > 10:
        return False
    if line.endswith((".", "!", "?")) or _heading_section(line, is_bullet=False) is not None:
        return False
    normalized = normalize(line)
    return any(marker in normalized for marker in TITLE_MARKERS)


class JobAgent:
    name = "Agente de Vaga"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, text: str) -> tuple[JobProfile, AgentTrace]:
        def action() -> JobProfile:
            raw_lines = [line.rstrip() for line in text.splitlines() if line.strip()]
            clean_lines = [line.strip(" •-*–—\t") for line in raw_lines]
            title = next(
                (
                    line
                    for raw_line, line in zip(raw_lines[:8], clean_lines[:8], strict=True)
                    if _is_job_title(raw_line, line)
                ),
                "Vaga não identificada",
            )

            context = SectionContext()
            requirements: list[Requirement] = []
            responsibilities: list[str] = []
            seen: set[str] = set()

            for index, (raw_line, line) in enumerate(zip(raw_lines, clean_lines, strict=True)):
                if len(line) < 2:
                    continue
                is_bullet = raw_line.lstrip().startswith(BULLET_PREFIXES)
                heading_section = _heading_section(line, is_bullet=is_bullet)
                if heading_section is not None:
                    context = _context_for_section(heading_section)
                    continue

                next_is_bullet = (
                    index + 1 < len(raw_lines)
                    and raw_lines[index + 1].lstrip().startswith(BULLET_PREFIXES)
                )
                if _looks_like_generic_subheading(
                    line,
                    is_bullet=is_bullet,
                    next_is_bullet=next_is_bullet,
                    context=context,
                ):
                    context = SectionContext(
                        section=context.section,
                        priority=context.priority,
                        subsection=line.rstrip(":"),
                    )
                    continue

                if line == title:
                    continue

                if context.section == "responsibilities":
                    if is_bullet or len(line) <= 220:
                        responsibilities.append(line.rstrip(".;"))
                    continue

                # Textos introdutórios não são requisitos. Em vagas sem cabeçalhos,
                # bullets ainda podem ser tratados como requisitos neutros.
                if context.section == "preamble" and not is_bullet:
                    continue

                if len(line.split()) > 35:
                    continue
                key = normalize(line)
                if key in seen:
                    continue
                seen.add(key)
                requirements.append(Requirement(
                    id=str(uuid.uuid4()),
                    text=line.rstrip(".;"),
                    priority=context.priority,
                    category=category_for(line),
                    aliases=aliases_for(line),
                    source_section=context.section,
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
