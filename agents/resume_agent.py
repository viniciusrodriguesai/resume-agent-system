from agents.base_agent import AgentResult, BaseAgent
from agents.text_tools import extract_contact, extract_relevant_lines, find_skills, unique_sorted


class ResumeAgent(BaseAgent):
    """Read a resume and extract its main information."""

    name = "Resume Agent"

    def run(self, resume_text: str) -> AgentResult:
        skills = unique_sorted(find_skills(resume_text))
        contact = extract_contact(resume_text)
        education = extract_relevant_lines(
            resume_text,
            [
                "degree",
                "bachelor",
                "master",
                "university",
                "college",
                "education",
                "graduation",
                "course",
            ],
            max_items=4,
        )
        experiences = extract_relevant_lines(
            resume_text,
            [
                "experience",
                "internship",
                "project",
                "research",
                "assistant",
                "developed",
                "implemented",
                "built",
            ],
            max_items=6,
        )

        warnings = []
        if contact["email"] == "not identified":
            warnings.append("No email address was identified in the resume.")
        if len(skills) < 3:
            warnings.append("Only a small number of technical skills were identified.")

        return AgentResult(
            agent_name=self.name,
            summary=f"The Resume Agent identified {len(skills)} skills.",
            data={
                "skills": skills,
                "contact": contact,
                "education": education,
                "experiences": experiences,
                "raw_text_length": len(resume_text or ""),
            },
            warnings=warnings,
        )
