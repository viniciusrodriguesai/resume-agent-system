from __future__ import annotations

from resume_ai.domain.models import AgentTrace, EvidenceCandidate, EvidenceMatch, JobProfile, CandidateProfile
from resume_ai.infrastructure.embeddings import EmbeddingEngine

from .base import run_agent


class EvidenceAgent:
    name = "Agente de Evidências"

    def __init__(self, engine: EmbeddingEngine) -> None:
        self.engine = engine

    def run(self, candidate: CandidateProfile, job: JobProfile, top_k: int) -> tuple[list[EvidenceMatch], AgentTrace]:
        def action() -> list[EvidenceMatch]:
            output: list[EvidenceMatch] = []
            for requirement in job.requirements:
                query = " | ".join([requirement.text, *requirement.aliases])
                candidates = self.engine.retrieve(query, candidate.chunks, top_k=top_k)
                candidates = self.engine.rerank(query, candidates)
                best = candidates[0] if candidates else None
                final = float(best["final_score"]) if best else 0.0
                explanation = (
                    "A evidência foi escolhida pela combinação entre correspondência lexical, fuzzy e semântica."
                    if best else "Nenhum trecho do currículo apresentou evidência suficiente."
                )
                output.append(EvidenceMatch(
                    requirement=requirement,
                    evidence=best["text"] if best else None,
                    lexical_score=float(best["lexical_score"]) if best else 0.0,
                    fuzzy_score=float(best["fuzzy_score"]) if best else 0.0,
                    semantic_score=float(best["semantic_score"]) if best else 0.0,
                    reranker_score=float(best["reranker_score"]) if best else 0.0,
                    final_score=final,
                    explanation=explanation,
                    top_candidates=[EvidenceCandidate(**item) for item in candidates],
                ))
            return output

        return run_agent(
            self.name,
            action,
            lambda result: f"Evidências recuperadas para {len(result)} requisitos.",
            lambda result: sum(item.final_score for item in result) / len(result) if result else 0.0,
        )
