from __future__ import annotations
import time
from agents.base_agent import AgentResult, BaseAgent
from agents.skill_ontology import SECTION_ALIASES
from utils.text_utils import detect_skills, extract_contact, extract_name, select_relevant_units, split_content_units

class ResumeAgent(BaseAgent):
    name = "Resume Agent"

    def run(self, resume_text: str) -> AgentResult:
        started = time.perf_counter()
        units = split_content_units(resume_text)
        skills = detect_skills(resume_text)
        contact = extract_contact(resume_text)
        education = select_relevant_units(resume_text, SECTION_ALIASES["education"], 6)
        experience = select_relevant_units(resume_text, SECTION_ALIASES["experience"], 10)
        projects = select_relevant_units(resume_text, SECTION_ALIASES["projects"], 10)

        warnings = []
        if contact["email"] == "not identified":
            warnings.append("No email address was identified.")
        if len(skills) < 3:
            warnings.append("Only a small number of recognized skills were found.")
        if not experience and not projects:
            warnings.append("No clear experience or project evidence was identified.")

        confidence = min(.98, .45 + min(len(skills), 10) * .035 + min(len(units), 20) * .01)
        return AgentResult(
            agent_name=self.name,
            summary=f"Identified {len(skills)} skills, {len(experience)} experience statements, and {len(projects)} project statements.",
            data={
                "name": extract_name(resume_text),
                "contact": contact,
                "skills": skills,
                "education": education,
                "experience": experience,
                "projects": projects,
                "content_units": units,
                "raw_text_length": len(resume_text or ""),
            },
            warnings=warnings,
            confidence=round(confidence, 2),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
