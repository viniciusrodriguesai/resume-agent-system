from __future__ import annotations
import time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent
from services.semantic_service import SemanticService

class ExperienceAgent(BaseAgent):
    name = "Experience Agent"

    def __init__(self, semantic_service: SemanticService | None = None) -> None:
        self.semantic_service = semantic_service or SemanticService()

    def run(self, resume_result: AgentResult, job_result: AgentResult) -> AgentResult:
        started = time.perf_counter()
        resume_units: List[str] = resume_result.data.get("content_units", [])
        requirements: List[Dict[str, object]] = job_result.data.get("requirements", [])
        evidence_map = {}

        for requirement in requirements:
            evidence_map[str(requirement["id"])] = self.semantic_service.best_evidence(
                str(requirement["label"]),
                resume_units,
                aliases=list(requirement.get("aliases", [])),
            )

        strong = sum(1 for item in evidence_map.values() if float(item.get("similarity", 0)) >= .56)
        confidence = strong / len(evidence_map) if evidence_map else 0.0
        return AgentResult(
            agent_name=self.name,
            summary=f"Collected evidence for {len(evidence_map)} requirements; {strong} have strong support.",
            data={"evidence_map": evidence_map, "strong_evidence_count": strong},
            confidence=round(confidence, 2),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
