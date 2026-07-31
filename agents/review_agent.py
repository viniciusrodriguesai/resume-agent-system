from __future__ import annotations
import time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent

class ReviewAgent(BaseAgent):
    name = "Review Agent"

    def run(self, matching_result: AgentResult, final_pass: bool = False) -> AgentResult:
        started = time.perf_counter()
        matches: List[Dict[str, object]] = matching_result.data.get("matches", [])
        issues, borderline = [], []

        for item in matches:
            similarity = float(item.get("similarity", 0))
            if item.get("priority") == "required" and item.get("status") == "missing" and similarity >= .24:
                borderline.append(str(item.get("id")))

        if borderline and not final_pass:
            issues.append("Some required items have borderline evidence and should be rechecked.")
        if not matches:
            issues.append("No requirements were available for review.")

        score = int(matching_result.data.get("overall_score", 0))
        missing_required = int(matching_result.data.get("missing_required_count", 0))
        if missing_required and score > 72:
            issues.append("The score is too high for the number of missing required items.")

        needs_revision = bool(issues and not final_pass)
        decision = "revision_requested" if needs_revision else "approved"
        if needs_revision:
            final_answer = "The review agent requested a second matching pass because borderline evidence or score consistency issues were found."
        else:
            level = str(matching_result.data.get("level", "low")).title()
            final_answer = (
                f"Final decision: {level} compatibility ({score}%). "
                f"The analysis is evidence-based and should support, not replace, human evaluation. "
                f"Missing required items: {missing_required}."
            )

        return AgentResult(
            agent_name=self.name,
            summary=f"Review decision: {decision}.",
            data={
                "decision": decision,
                "needs_revision": needs_revision,
                "issues": issues,
                "borderline_requirement_ids": borderline,
                "final_answer": final_answer,
            },
            warnings=issues,
            confidence=.95 if not needs_revision else .78,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
