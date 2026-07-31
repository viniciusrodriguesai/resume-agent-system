from __future__ import annotations
import time
from typing import Dict, List
from agents.base_agent import AgentResult, BaseAgent
from agents.experience_agent import ExperienceAgent
from agents.job_agent import JobAgent
from agents.recommendation_agent import RecommendationAgent
from agents.report_agent import ReportAgent
from agents.resume_agent import ResumeAgent
from agents.review_agent import ReviewAgent
from agents.semantic_matching_agent import SemanticMatchingAgent

class CoordinatorAgent(BaseAgent):
    name = "Coordinator Agent"

    def __init__(self) -> None:
        self.resume_agent = ResumeAgent()
        self.job_agent = JobAgent()
        self.experience_agent = ExperienceAgent()
        self.matching_agent = SemanticMatchingAgent()
        self.recommendation_agent = RecommendationAgent()
        self.review_agent = ReviewAgent()
        self.report_agent = ReportAgent()

    def run(self, resume_text: str, job_text: str, strictness: str = "Balanced") -> Dict[str, AgentResult]:
        started = time.perf_counter()
        trace: List[Dict[str, object]] = []
        thresholds = {
            "Conservative": (.64, .36),
            "Balanced": (.56, .30),
            "Flexible": (.50, .26),
        }
        matched_threshold, partial_threshold = thresholds.get(strictness, thresholds["Balanced"])

        resume_result = self.resume_agent.run(resume_text)
        trace.append(self._trace("resume", resume_result, 1))

        job_result = self.job_agent.run(job_text)
        trace.append(self._trace("job", job_result, 1))

        experience_result = self.experience_agent.run(resume_result, job_result)
        trace.append(self._trace("experience", experience_result, 1))

        matching_result = self.matching_agent.run(
            job_result, experience_result,
            matched_threshold=matched_threshold,
            partial_threshold=partial_threshold,
            pass_number=1,
        )
        trace.append(self._trace("matching", matching_result, 1))

        review_result = self.review_agent.run(matching_result, final_pass=False)
        trace.append(self._trace("review", review_result, 1))

        revision_performed = False
        if review_result.data.get("needs_revision"):
            revision_performed = True
            matching_result = self.matching_agent.run(
                job_result, experience_result,
                matched_threshold=max(.45, matched_threshold - .04),
                partial_threshold=max(.20, partial_threshold - .03),
                pass_number=2,
            )
            trace.append(self._trace("matching", matching_result, 2))
            review_result = self.review_agent.run(matching_result, final_pass=True)
            trace.append(self._trace("review", review_result, 2))

        recommendation_result = self.recommendation_agent.run(resume_result, matching_result)
        trace.append(self._trace("recommendation", recommendation_result, 1))

        report_result = self.report_agent.run(
            resume_result, job_result, matching_result,
            recommendation_result, review_result,
        )
        trace.append(self._trace("report", report_result, 1))

        elapsed = (time.perf_counter() - started) * 1000
        coordinator_result = AgentResult(
            agent_name=self.name,
            summary=f"Completed the workflow with {'one review revision' if revision_performed else 'no revision'}.",
            data={
                "strictness": strictness,
                "revision_performed": revision_performed,
                "trace": trace,
                "total_elapsed_ms": round(elapsed, 2),
            },
            confidence=.97,
            elapsed_ms=round(elapsed, 2),
        )

        return {
            "coordinator": coordinator_result,
            "resume": resume_result,
            "job": job_result,
            "experience": experience_result,
            "matching": matching_result,
            "recommendation": recommendation_result,
            "review": review_result,
            "report": report_result,
        }

    @staticmethod
    def _trace(stage: str, result: AgentResult, pass_number: int) -> Dict[str, object]:
        return {
            "stage": stage,
            "pass": pass_number,
            "agent": result.agent_name,
            "summary": result.summary,
            "confidence": result.confidence,
            "elapsed_ms": result.elapsed_ms,
            "warnings": result.warnings,
        }
