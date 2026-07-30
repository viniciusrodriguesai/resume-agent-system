from agents.base_agent import AgentResult, BaseAgent


class MatchingAgent(BaseAgent):
    """Compare resume and job skills and calculate compatibility."""

    name = "Matching Agent"

    def run(
        self,
        resume_result: AgentResult,
        job_result: AgentResult,
    ) -> AgentResult:
        resume_skills = set(resume_result.data.get("skills", []))
        required = set(job_result.data.get("required_skills", []))
        desirable = set(job_result.data.get("desirable_skills", []))
        neutral = set(job_result.data.get("neutral_skills", []))

        matched_required = sorted(resume_skills & required)
        missing_required = sorted(required - resume_skills)
        matched_desirable = sorted(resume_skills & desirable)
        missing_desirable = sorted(desirable - resume_skills)
        matched_neutral = sorted(resume_skills & neutral)

        required_score = len(matched_required) / len(required) if required else 1.0
        desirable_score = (
            len(matched_desirable) / len(desirable) if desirable else 1.0
        )
        neutral_score = len(matched_neutral) / len(neutral) if neutral else 1.0

        score = round(
            (
                required_score * 0.65
                + desirable_score * 0.25
                + neutral_score * 0.10
            )
            * 100
        )
        score = max(0, min(score, 100))

        if score >= 80:
            level = "high"
        elif score >= 60:
            level = "medium"
        else:
            level = "low"

        return AgentResult(
            agent_name=self.name,
            summary=f"{level.title()} compatibility: {score}%.",
            data={
                "score": score,
                "level": level,
                "matched_required": matched_required,
                "missing_required": missing_required,
                "matched_desirable": matched_desirable,
                "missing_desirable": missing_desirable,
                "matched_neutral": matched_neutral,
            },
        )
