from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

ConceptOperator = Literal["SINGLE", "AND", "OR"]


class RequirementIntent(StrEnum):
    KNOWLEDGE = "knowledge"
    EXPERIENCE = "experience"
    PROFESSIONAL_EXPERIENCE = "professional_experience"
    PRODUCTION_EXPERIENCE = "production_experience"


@dataclass(frozen=True)
class EvidenceContext:
    professional_experience: bool = False
    production_experience: bool = False
    personal_project_context: bool = False
    academic_context: bool = False


@dataclass(frozen=True)
class Concept:
    canonical: str
    aliases: tuple[str, ...]
    cataloged: bool


@dataclass(frozen=True)
class ConceptGroup:
    operator: ConceptOperator
    concepts: tuple[Concept, ...]

    @property
    def alias_groups(self) -> list[list[str]]:
        return [list(concept.aliases) for concept in self.concepts]

    @property
    def uses_literal_fallback(self) -> bool:
        return any(not concept.cataloged for concept in self.concepts)
