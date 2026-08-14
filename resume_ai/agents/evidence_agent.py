from __future__ import annotations

from resume_ai.domain.models import AgentTrace, CandidateProfile, EvidenceCandidate, EvidenceMatch, JobProfile
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.utils.text import best_snippet, remove_privacy_placeholders

from .base import run_agent
from .catalog import concept_alias_groups


class EvidenceAgent:
    name = "Agente de Evidências"

    def __init__(self, engine: EmbeddingEngine) -> None:
        self.engine = engine

    def run(self, candidate: CandidateProfile, job: JobProfile, top_k: int) -> tuple[list[EvidenceMatch], AgentTrace]:
        def action() -> list[EvidenceMatch]:
            queries = [" | ".join([requirement.text, *requirement.aliases]) for requirement in job.requirements]
            groups = [concept_alias_groups(requirement.text) for requirement in job.requirements]
            retrieved = self.engine.retrieve_many(
                queries,
                candidate.chunks,
                top_k=top_k,
                concept_groups=groups,
            )

            output: list[EvidenceMatch] = []
            for requirement, query, candidates in zip(job.requirements, queries, retrieved, strict=True):
                candidates = self.engine.rerank(query, candidates)
                for item in candidates:
                    item["text"] = best_snippet(item["text"], requirement.text)
                best = candidates[0] if candidates else None
                final = float(best["final_score"]) if best else 0.0
                explanation = (
                    "A evidência combina similaridade lexical, aproximada, semântica e cobertura das competências citadas."
                    if best else "Nenhum trecho do currículo apresentou evidência suficiente."
                )
                output.append(EvidenceMatch(
                    requirement=requirement,
                    evidence=remove_privacy_placeholders(best["text"]) if best else None,
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
            lambda result: f"Evidências recuperadas em lote para {len(result)} requisitos.",
            lambda result: sum(item.final_score for item in result) / len(result) if result else 0.0,
        )
