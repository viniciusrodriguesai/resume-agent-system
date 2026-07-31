from __future__ import annotations
import time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent
from agents.skill_ontology import DESIRABLE_MARKERS, REQUIRED_MARKERS, RESPONSIBILITY_MARKERS
from utils.text_utils import detect_skills, extract_job_title, normalize_text, split_content_units

class JobAgent(BaseAgent):
    name = "Job Agent"

    @staticmethod
    def _priority(unit: str) -> str:
        normalized = normalize_text(unit)
        if any(marker in normalized for marker in DESIRABLE_MARKERS):
            return "desirable"
        if any(marker in normalized for marker in REQUIRED_MARKERS):
            return "required"
        return "neutral"

    def run(self, job_text: str) -> AgentResult:
        started = time.perf_counter()
        units = split_content_units(job_text)
        detected = detect_skills(job_text)
        requirements: List[Dict[str, object]] = []

        for canonical, details in detected.items():
            evidence_lines = list(details.get("evidence", []))
            source = evidence_lines[0] if evidence_lines else canonical
            requirements.append({
                "id": f"skill:{canonical}",
                "label": canonical,
                "type": "skill",
                "category": details.get("category", "general"),
                "priority": self._priority(source),
                "source_line": source,
                "aliases": details.get("aliases", []),
            })

        responsibilities = []
        for unit in units:
            normalized = normalize_text(unit)
            if any(marker in normalized for marker in RESPONSIBILITY_MARKERS):
                responsibilities.append(unit)

        for index, responsibility in enumerate(responsibilities[:6], 1):
            requirements.append({
                "id": f"responsibility:{index}",
                "label": responsibility,
                "type": "responsibility",
                "category": "experience",
                "priority": self._priority(responsibility),
                "source_line": responsibility,
                "aliases": [],
            })

        education_lines = [
            unit for unit in units
            if any(marker in normalize_text(unit) for marker in ["degree", "bachelor", "university", "student", "graduation"])
        ]
        for index, line in enumerate(education_lines[:3], 1):
            requirements.append({
                "id": f"education:{index}",
                "label": line,
                "type": "education",
                "category": "education",
                "priority": self._priority(line),
                "source_line": line,
                "aliases": [],
            })

        warnings = []
        if not requirements:
            warnings.append("No structured requirements were identified.")
        if requirements and not any(item["priority"] == "required" for item in requirements):
            warnings.append("No explicit mandatory marker was found; requirements were treated as neutral.")

        confidence = min(.98, .50 + min(len(requirements), 15) * .03)
        return AgentResult(
            agent_name=self.name,
            summary=f"Structured {len(requirements)} requirements for '{extract_job_title(job_text)}'.",
            data={
                "job_title": extract_job_title(job_text),
                "requirements": requirements,
                "responsibilities": responsibilities[:8],
                "content_units": units,
            },
            warnings=warnings,
            confidence=round(confidence, 2),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
