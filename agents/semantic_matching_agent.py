from __future__ import annotations
import time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent
from services.scoring_service import ScoringService

class SemanticMatchingAgent(BaseAgent):
    name = "Semantic Matching Agent"

    def __init__(self, scoring_service: ScoringService | None = None) -> None:
        self.scoring_service = scoring_service or ScoringService()

    def run(self, job_result: AgentResult, experience_result: AgentResult,
            matched_threshold: float = .56, partial_threshold: float = .30,
            pass_number: int = 1) -> AgentResult:
        started = time.perf_counter()
        requirements: List[Dict[str, object]] = job_result.data.get("requirements", [])
        evidence_map: Dict[str, Dict[str, object]] = experience_result.data.get("evidence_map", {})
        matches = []

        for requirement in requirements:
            evidence = evidence_map.get(str(requirement["id"]), {"evidence": "", "similarity": 0.0})
            similarity = float(evidence.get("similarity", 0.0))
            status = "matched" if similarity >= matched_threshold else "partial" if similarity >= partial_threshold else "missing"
            matches.append({
                **requirement,
                "status": status,
                "similarity": round(similarity, 3),
                "evidence": evidence.get("evidence", ""),
            })

        score_data = self.scoring_service.calculate(matches)
        matched = sum(item["status"] == "matched" for item in matches)
        partial = sum(item["status"] == "partial" for item in matches)
        missing = sum(item["status"] == "missing" for item in matches)
        average = sum(float(item["similarity"]) for item in matches) / len(matches) if matches else 0.0

        return AgentResult(
            agent_name=self.name,
            summary=f"Pass {pass_number}: {matched} matched, {partial} partial, {missing} missing. Overall compatibility: {score_data['overall_score']}%.",
            data={
                **score_data,
                "matches": matches,
                "matched_count": int(matched),
                "partial_count": int(partial),
                "missing_count": int(missing),
                "pass_number": pass_number,
                "thresholds": {"matched": matched_threshold, "partial": partial_threshold},
            },
            confidence=round(average, 2),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
