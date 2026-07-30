from agents.base_agent import AgentResult, BaseAgent


class RecommendationAgent(BaseAgent):
    """Transform the comparison into practical recommendations."""

    name = "Recommendation Agent"

    def run(
        self,
        resume_result: AgentResult,
        job_result: AgentResult,
        matching_result: AgentResult,
    ) -> AgentResult:
        del resume_result, job_result

        missing_required = matching_result.data.get("missing_required", [])
        missing_desirable = matching_result.data.get("missing_desirable", [])
        matched_required = matching_result.data.get("matched_required", [])
        score = matching_result.data.get("score", 0)

        recommendations = []

        if matched_required:
            recommendations.append(
                "Highlight the skills that already match the position: "
                + ", ".join(matched_required[:6])
                + "."
            )

        if missing_required:
            recommendations.append(
                "Study or provide stronger evidence for the missing required skills: "
                + ", ".join(missing_required[:6])
                + "."
            )

        if missing_desirable:
            recommendations.append(
                "As an additional improvement, gain experience with: "
                + ", ".join(missing_desirable[:6])
                + "."
            )

        if score < 60:
            recommendations.append(
                "Apply only after adapting the resume and reviewing the main requirements."
            )
        elif score < 80:
            recommendations.append(
                "The application is reasonable, but the resume should be tailored more closely to the job description."
            )
        else:
            recommendations.append(
                "The position is a strong match; emphasize concrete projects, actions, and measurable results."
            )

        return AgentResult(
            agent_name=self.name,
            summary=f"The agent generated {len(recommendations)} recommendations.",
            data={"recommendations": recommendations},
        )
