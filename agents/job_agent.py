from agents.base_agent import AgentResult, BaseAgent
from agents.text_tools import (
    DESIRABLE_WORDS,
    HIGH_PRIORITY_WORDS,
    find_skills,
    split_lines,
    unique_sorted,
)


class JobAgent(BaseAgent):
    """Analyze a job description and classify its requested skills."""

    name = "Job Agent"

    def _classify_skills(self, job_text: str):
        required = set()
        desirable = set()
        neutral = set()
        current_section = None

        for line in split_lines(job_text):
            lower = line.lower()

            if any(
                phrase in lower
                for phrase in [
                    "required qualifications",
                    "required skills",
                    "mandatory requirements",
                    "requirements",
                    "required",
                ]
            ):
                current_section = "required"
                continue

            if any(
                phrase in lower
                for phrase in [
                    "preferred qualifications",
                    "preferred skills",
                    "desirable skills",
                    "nice to have",
                    "differentials",
                    "plus",
                ]
            ):
                current_section = "desirable"
                continue

            line_skills = find_skills(line)
            if not line_skills:
                continue

            if current_section == "desirable" or any(
                word in lower for word in DESIRABLE_WORDS
            ):
                desirable.update(line_skills)
            elif current_section == "required" or any(
                word in lower for word in HIGH_PRIORITY_WORDS
            ):
                required.update(line_skills)
            else:
                neutral.update(line_skills)

        # When the job does not explicitly separate requirements, treat general
        # skills as required so that the comparison remains meaningful.
        if not required:
            required.update(neutral)
            neutral.clear()

        return (
            unique_sorted(required),
            unique_sorted(desirable),
            unique_sorted(neutral),
        )

    def run(self, job_text: str) -> AgentResult:
        required, desirable, neutral = self._classify_skills(job_text)
        all_skills = unique_sorted(required + desirable + neutral)

        lower_text = job_text.lower()
        seniority = (
            "internship/entry level"
            if any(
                term in lower_text
                for term in ["internship", "intern", "trainee", "junior", "entry level"]
            )
            else "not identified"
        )

        warnings = []
        if not all_skills:
            warnings.append("No known skills were identified in the job description.")

        return AgentResult(
            agent_name=self.name,
            summary=(
                f"The position appears to be {seniority} and contains "
                f"{len(all_skills)} mapped skills."
            ),
            data={
                "required_skills": required,
                "desirable_skills": desirable,
                "neutral_skills": neutral,
                "all_skills": all_skills,
                "seniority": seniority,
            },
            warnings=warnings,
        )
