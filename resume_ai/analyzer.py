from __future__ import annotations

import copy
import uuid
from typing import Dict, Literal

from .catalog import SkillCatalog
from .config import Settings
from .privacy import anonymize_resume
from .profiles import job_profile, resume_profile
from .reporting import build_recommendations, build_reports
from .scoring import score_evidence
from .semantic import SemanticEngine
from .state import AnalysisState
from .storage import HistoryStore
from .text import phrase_present


class MultiAgentAnalyzer:
    """Orchestrates the agents through LangGraph when available."""

    def __init__(
        self,
        settings: Settings | None = None,
        full_ai: bool = True,
        persist_history: bool = True,
    ) -> None:
        self.settings = settings or Settings()
        self.settings.ensure()
        self.catalog = SkillCatalog(self.settings)
        self.semantic = SemanticEngine(self.settings)
        self.history = HistoryStore(self.settings)
        self.full_ai = full_ai
        self.persist_history = persist_history
        self._graph = self._build_graph()

    def engine_status(self) -> Dict[str, object]:
        semantic = self.semantic.diagnostics()
        try:
            import langgraph  # noqa: F401
            langgraph_available = True
        except ImportError:
            langgraph_available = False
        return {
            **semantic,
            "langgraph_available": langgraph_available,
            "catalog_size": self.catalog.size,
            "full_ai_requested": self.full_ai,
        }

    def run(
        self,
        resume_text: str,
        job_text: str,
        strictness: str = "Balanced",
    ) -> Dict[str, object]:
        if not resume_text.strip() or not job_text.strip():
            raise ValueError("Resume and job description are required.")

        initial: AnalysisState = {
            "analysis_id": str(uuid.uuid4()),
            "resume_text": resume_text,
            "job_text": job_text,
            "strictness": strictness,
            "revision_count": 0,
            "max_revisions": self.settings.max_revisions,
            "trace": [],
            "engine_status": {},
        }

        if self._graph is not None:
            result = dict(self._graph.invoke(initial))
        else:
            result = self._run_sequential(initial)

        if self.persist_history:
            self.history.save(result)
        return result

    def _build_graph(self):
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError:
            return None

        builder = StateGraph(AnalysisState)
        builder.add_node("privacy_agent", self._privacy_node)
        builder.add_node("resume_agent", self._resume_node)
        builder.add_node("job_agent", self._job_node)
        builder.add_node("retrieval_agent", self._retrieval_node)
        builder.add_node("scoring_agent", self._scoring_node)
        builder.add_node("review_agent", self._review_node)
        builder.add_node("recommendation_agent", self._recommendation_node)
        builder.add_node("report_agent", self._report_node)

        builder.add_edge(START, "privacy_agent")
        builder.add_edge("privacy_agent", "resume_agent")
        builder.add_edge("resume_agent", "job_agent")
        builder.add_edge("job_agent", "retrieval_agent")
        builder.add_edge("retrieval_agent", "scoring_agent")
        builder.add_edge("scoring_agent", "review_agent")
        builder.add_conditional_edges(
            "review_agent",
            self._review_route,
            {
                "revise": "retrieval_agent",
                "approve": "recommendation_agent",
            },
        )
        builder.add_edge("recommendation_agent", "report_agent")
        builder.add_edge("report_agent", END)
        return builder.compile()

    def _run_sequential(self, state: AnalysisState) -> Dict[str, object]:
        current: Dict[str, object] = dict(state)
        for node in [
            self._privacy_node,
            self._resume_node,
            self._job_node,
        ]:
            self._merge(current, node(current))

        while True:
            self._merge(current, self._retrieval_node(current))
            self._merge(current, self._scoring_node(current))
            self._merge(current, self._review_node(current))
            if self._review_route(current) == "approve":
                break

        self._merge(current, self._recommendation_node(current))
        self._merge(current, self._report_node(current))
        return current

    @staticmethod
    def _merge(state: Dict[str, object], updates: Dict[str, object]) -> None:
        for key, value in updates.items():
            if key == "trace":
                state.setdefault("trace", [])
                state["trace"].extend(value)
            else:
                state[key] = value

    @staticmethod
    def _trace(
        agent: str,
        summary: str,
        warnings=None,
        **details,
    ) -> Dict[str, object]:
        return {
            "agent": agent,
            "summary": summary,
            "warnings": warnings or [],
            **details,
        }

    def _privacy_node(self, state: AnalysisState) -> Dict[str, object]:
        anonymized, report = anonymize_resume(state["resume_text"])
        return {
            "anonymized_resume_text": anonymized,
            "anonymized_job_text": state["job_text"],
            "privacy_report": report,
            "trace": [
                self._trace(
                    "Privacy and Fairness Agent",
                    "Removed direct identifiers and selected sensitive lines before matching.",
                    removed=sum(
                        int(value)
                        for value in report.values()
                        if isinstance(value, (int, bool))
                    ),
                )
            ],
        }

    def _resume_node(self, state: AnalysisState) -> Dict[str, object]:
        profile = resume_profile(
            state["anonymized_resume_text"],
            self.catalog,
        )
        return {
            "resume_profile": profile,
            "trace": [
                self._trace(
                    "Resume Structurer Agent",
                    f"Extracted {len(profile['skill_labels'])} skills and {profile['unit_count']} evidence units.",
                )
            ],
        }

    def _job_node(self, state: AnalysisState) -> Dict[str, object]:
        profile = job_profile(
            state["anonymized_job_text"],
            self.catalog,
        )
        warnings = []
        if not profile["requirements"]:
            warnings.append("No structured requirements were detected.")
        return {
            "job_profile": profile,
            "trace": [
                self._trace(
                    "Job Structurer Agent",
                    f"Structured {profile['requirement_count']} requirements.",
                    warnings=warnings,
                )
            ],
        }

    def _retrieval_node(self, state: AnalysisState) -> Dict[str, object]:
        if self.full_ai:
            self.semantic.load()

        resume_units = state["resume_profile"].get("units", [])
        requirements = state["job_profile"].get("requirements", [])
        revision = int(state.get("revision_count", 0))
        top_k = self.settings.top_k + revision * 3
        evidence = []

        for requirement in requirements:
            ranked = self.semantic.retrieve(
                str(requirement["query"]),
                resume_units,
                top_k=top_k,
            )

            aliases = requirement.get("aliases", []) or []
            for candidate in ranked:
                if aliases and any(
                    phrase_present(candidate["text"], alias)
                    for alias in aliases
                ):
                    candidate["final_score"] = max(
                        float(candidate["final_score"]),
                        0.985,
                    )
                    candidate["exact_alias_match"] = True
                else:
                    candidate["exact_alias_match"] = False

            ranked = sorted(
                ranked,
                key=lambda item: float(item["final_score"]),
                reverse=True,
            )
            best = ranked[0] if ranked else {
                "text": "",
                "final_score": 0.0,
                "engine": "none",
            }
            evidence.append(
                {
                    **requirement,
                    "best_evidence": best.get("text", ""),
                    "final_score": round(
                        float(best.get("final_score", 0.0)),
                        4,
                    ),
                    "engine": best.get("engine", "none"),
                    "retrieval_score": best.get("retrieval_score"),
                    "reranker_score": best.get("reranker_score"),
                    "top_candidates": ranked,
                }
            )

        status = self.engine_status()
        return {
            "evidence": evidence,
            "engine_status": status,
            "trace": [
                self._trace(
                    "Semantic Retriever and Reranker Agent",
                    f"Retrieved evidence for {len(evidence)} requirements using top-{top_k}.",
                    revision=revision,
                    embedding=status["embedding_available"],
                    reranker=status["reranker_available"],
                )
            ],
        }

    def _scoring_node(self, state: AnalysisState) -> Dict[str, object]:
        scoring = score_evidence(
            state.get("evidence", []),
            strictness=state.get("strictness", "Balanced"),
        )
        return {
            "scoring": scoring,
            "trace": [
                self._trace(
                    "Explainable Scoring Agent",
                    (
                        f"Calculated {scoring['overall_score']}% compatibility: "
                        f"{scoring['matched_count']} matched, "
                        f"{scoring['partial_count']} partial, "
                        f"{scoring['missing_count']} missing."
                    ),
                )
            ],
        }

    def _review_node(self, state: AnalysisState) -> Dict[str, object]:
        scoring = state["scoring"]
        revision_count = int(state.get("revision_count", 0))
        max_revisions = int(state.get("max_revisions", 1))
        partial_threshold = float(scoring["partial_threshold"])

        borderline = [
            item
            for item in scoring.get("evidence", [])
            if item.get("priority") == "required"
            and item.get("status") == "missing"
            and float(item.get("final_score", 0.0))
            >= max(0.0, partial_threshold - 0.10)
        ]

        needs_revision = bool(
            borderline and revision_count < max_revisions
        )
        decision = "revision_requested" if needs_revision else "approved"
        next_revision = revision_count + 1 if needs_revision else revision_count

        summary = (
            "Requested a broader second retrieval pass for borderline required evidence."
            if needs_revision
            else (
                f"Approved the evidence-based result at "
                f"{scoring['overall_score']}%. "
                "Human evaluation remains required."
            )
        )

        return {
            "revision_count": next_revision,
            "review": {
                "decision": decision,
                "needs_revision": needs_revision,
                "borderline_requirement_ids": [
                    item.get("id") for item in borderline
                ],
                "summary": summary,
            },
            "trace": [
                self._trace(
                    "Review Agent",
                    summary,
                    decision=decision,
                    revision_count=next_revision,
                )
            ],
        }

    @staticmethod
    def _review_route(
        state: AnalysisState,
    ) -> Literal["revise", "approve"]:
        return (
            "revise"
            if state.get("review", {}).get("needs_revision")
            else "approve"
        )

    def _recommendation_node(
        self,
        state: AnalysisState,
    ) -> Dict[str, object]:
        recommendations = build_recommendations(
            state["scoring"],
            state["resume_profile"],
        )
        return {
            "recommendations": recommendations,
            "trace": [
                self._trace(
                    "Recommendation Agent",
                    f"Generated {len(recommendations)} truthful, prioritized actions.",
                )
            ],
        }

    def _report_node(self, state: AnalysisState) -> Dict[str, object]:
        snapshot = copy.deepcopy(dict(state))
        reports = build_reports(snapshot)
        return {
            "report_markdown": reports["markdown"],
            "report_json": reports["json"],
            "trace": [
                self._trace(
                    "Report Agent",
                    "Generated Markdown and JSON reports.",
                )
            ],
        }
