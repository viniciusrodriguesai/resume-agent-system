from agents.base_agent import AgentResult, BaseAgent


class ReviewAgent(BaseAgent):
    """Check consistency and prepare the final response."""

    name = "Review Agent"

    def run(self, *agent_results: AgentResult) -> AgentResult:
        warnings = []
        for result in agent_results:
            warnings.extend(result.warnings)

        matching = next(
            (result for result in agent_results if result.agent_name == "Matching Agent"),
            None,
        )
        recommendations = next(
            (
                result
                for result in agent_results
                if result.agent_name == "Recommendation Agent"
            ),
            None,
        )

        score = matching.data.get("score", 0) if matching else 0
        items = (
            recommendations.data.get("recommendations", [])
            if recommendations
            else []
        )

        final_text = [
            f"Final compatibility: {score}%.",
            "Main recommendations:",
        ]
        final_text.extend(f"- {item}" for item in items)

        if warnings:
            final_text.append("System warnings:")
            final_text.extend(f"- {warning}" for warning in warnings)

        return AgentResult(
            agent_name=self.name,
            summary="The final result was reviewed and consolidated.",
            data={
                "final_answer": "\n".join(final_text),
                "warnings": warnings,
            },
            warnings=warnings,
        )
