from __future__ import annotations

import re
from typing import Dict, List

from .catalog import SkillCatalog
from .text import contains_any, normalize, split_units

REQUIRED_MARKERS = [
    "required", "mandatory", "must", "essential", "minimum",
    "necessario", "obrigatorio", "requisito",
]
DESIRABLE_MARKERS = [
    "preferred", "desirable", "nice to have", "plus", "bonus",
    "desejavel", "diferencial",
]
EDUCATION_MARKERS = [
    "degree", "bachelor", "master", "university", "college",
    "graduation", "student", "graduacao", "universidade", "curso",
]
EXPERIENCE_MARKERS = [
    "experience", "internship", "research", "worked", "developed",
    "built", "implemented", "experiencia", "estagio", "pesquisa",
    "desenvolveu", "desenvolvido", "projeto",
]


def infer_priority(text: str) -> str:
    if contains_any(text, DESIRABLE_MARKERS):
        return "desirable"
    if contains_any(text, REQUIRED_MARKERS):
        return "required"
    return "neutral"


def resume_profile(
    text: str,
    catalog: SkillCatalog,
) -> Dict[str, object]:
    units = split_units(text)
    skills = catalog.find_in_text(text)

    education = [
        unit for unit in units
        if contains_any(unit, EDUCATION_MARKERS)
    ][:8]
    experience = [
        unit for unit in units
        if contains_any(unit, EXPERIENCE_MARKERS)
    ][:15]

    quantified = [
        unit for unit in units
        if re.search(r"\b\d+(?:[.,]\d+)?%?\b", unit)
    ][:10]

    return {
        "skills": skills,
        "skill_labels": [item["label"] for item in skills],
        "education": education,
        "experience": experience,
        "quantified_evidence": quantified,
        "units": units,
        "unit_count": len(units),
    }


def job_profile(
    text: str,
    catalog: SkillCatalog,
) -> Dict[str, object]:
    units = split_units(text)
    found_skills = catalog.find_in_text(text)
    requirements: List[Dict[str, object]] = []

    for skill in found_skills:
        evidence_lines = [
            unit for unit in units
            if any(
                normalize(alias) in normalize(unit)
                for alias in skill["aliases"]
            )
        ]
        source_line = evidence_lines[0] if evidence_lines else skill["label"]
        requirements.append(
            {
                "id": f"skill:{normalize(skill['label'])}",
                "label": skill["label"],
                "query": source_line,
                "type": "skill",
                "priority": infer_priority(source_line),
                "aliases": skill["aliases"],
                "source": skill["source"],
                "uri": skill["uri"],
            }
        )

    responsibility_markers = [
        "responsibilities", "you will", "will be responsible",
        "develop", "build", "analyze", "create", "support",
        "responsabilidades", "voce ira", "desenvolver", "analisar",
    ]
    responsibility_units = [
        unit for unit in units
        if contains_any(unit, responsibility_markers)
        and len(unit.split()) >= 4
    ]

    for index, unit in enumerate(responsibility_units[:8], start=1):
        requirements.append(
            {
                "id": f"responsibility:{index}",
                "label": unit,
                "query": unit,
                "type": "responsibility",
                "priority": infer_priority(unit),
                "aliases": [],
                "source": "job-text",
                "uri": "",
            }
        )

    education_units = [
        unit for unit in units
        if contains_any(unit, EDUCATION_MARKERS)
        and len(unit.split()) >= 4
    ]
    for index, unit in enumerate(education_units[:4], start=1):
        requirements.append(
            {
                "id": f"education:{index}",
                "label": unit,
                "query": unit,
                "type": "education",
                "priority": infer_priority(unit),
                "aliases": [],
                "source": "job-text",
                "uri": "",
            }
        )

    deduplicated: Dict[str, Dict[str, object]] = {}
    for requirement in requirements:
        deduplicated[str(requirement["id"])] = requirement

    title = "Target role"
    for unit in units[:4]:
        if len(unit.split()) <= 12:
            title = unit
            break

    return {
        "title": title,
        "requirements": list(deduplicated.values()),
        "units": units,
        "requirement_count": len(deduplicated),
    }
