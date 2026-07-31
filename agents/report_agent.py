from __future__ import annotations
import json, time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent

class ReportAgent(BaseAgent):
    name = "Report Agent"

    def run(self, resume_result: AgentResult, job_result: AgentResult,
            matching_result: AgentResult, recommendation_result: AgentResult,
            review_result: AgentResult) -> AgentResult:
        started = time.perf_counter()
        score = matching_result.data.get("overall_score", 0)
        matches: List[Dict[str, object]] = matching_result.data.get("matches", [])
        lines = [
            "# Multi-Agent Resume Analysis Report", "",
            f"**Candidate:** {resume_result.data.get('name', 'not identified')}",
            f"**Target role:** {job_result.data.get('job_title', 'not identified')}",
            f"**Overall compatibility:** {score}%",
            f"**Review decision:** {review_result.data.get('decision', 'unknown')}", "",
            "## Category scores", "",
        ]
        for category, value in matching_result.data.get("category_scores", {}).items():
            lines.append(f"- **{category}:** {value}%")
        lines.extend(["", "## Requirement evidence", ""])
        for item in matches:
            lines.extend([
                f"### {item.get('label')}",
                f"- Priority: {item.get('priority')}",
                f"- Status: {item.get('status')}",
                f"- Similarity: {float(item.get('similarity', 0)):.2f}",
                f"- Evidence: {item.get('evidence') or 'No evidence identified.'}", "",
            ])
        lines.extend(["## Recommendations", ""])
        for item in recommendation_result.data.get("recommendations", []):
            lines.append(f"- **{item.get('priority')} — {item.get('type')}:** {item.get('action')}")
        lines.extend(["", "## Final review", "", str(review_result.data.get("final_answer", "")), "",
                      "> This system supports human evaluation and must not be used as the sole basis for employment decisions."])

        raw_json = json.dumps({
            "resume": resume_result.to_dict(),
            "job": job_result.to_dict(),
            "matching": matching_result.to_dict(),
            "recommendations": recommendation_result.to_dict(),
            "review": review_result.to_dict(),
        }, indent=2, ensure_ascii=False)

        return AgentResult(
            agent_name=self.name,
            summary="Generated Markdown and JSON reports.",
            data={"markdown_report": "\n".join(lines), "json_report": raw_json},
            confidence=1.0,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
