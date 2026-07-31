from __future__ import annotations
import time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent

class RecommendationAgent(BaseAgent):
    name = "Recommendation Agent"

    def run(self, resume_result: AgentResult, matching_result: AgentResult) -> AgentResult:
        started = time.perf_counter()
        matches: List[Dict[str, object]] = matching_result.data.get("matches", [])
        recommendations = []

        required_missing = [i for i in matches if i.get("priority") == "required" and i.get("status") == "missing"]
        required_partial = [i for i in matches if i.get("priority") == "required" and i.get("status") == "partial"]
        desirable_missing = [i for i in matches if i.get("priority") == "desirable" and i.get("status") == "missing"]

        for item in required_missing[:5]:
            recommendations.append({
                "priority": "High",
                "type": "Skill gap",
                "action": f"Build real evidence for the required item '{item['label']}'. Add it only after gaining the skill or completing a relevant project.",
            })
        for item in required_partial[:5]:
            recommendations.append({
                "priority": "High",
                "type": "Resume evidence",
                "action": f"Strengthen the resume evidence for '{item['label']}'. Use a concrete action, technology, and measurable result.",
            })
        for item in desirable_missing[:4]:
            recommendations.append({
                "priority": "Medium",
                "type": "Development",
                "action": f"Consider studying or practicing '{item['label']}' because it appears as a desirable qualification.",
            })
        if resume_result.data.get("contact", {}).get("email") == "not identified":
            recommendations.append({"priority": "High", "type": "Resume format", "action": "Add a professional email address to the resume."})
        if not resume_result.data.get("projects"):
            recommendations.append({"priority": "Medium", "type": "Projects", "action": "Add a projects section with the problem, technologies, your contribution, and the result."})
        if not recommendations:
            recommendations.append({"priority": "Low", "type": "Tailoring", "action": "Tailor the summary and project bullets to the job while preserving only truthful information."})

        return AgentResult(
            agent_name=self.name,
            summary=f"Generated {len(recommendations)} prioritized recommendations.",
            data={"recommendations": recommendations},
            confidence=.92,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
