from __future__ import annotations

from typing import Any

from resume_ai.domain.concepts import ConceptGroup
from resume_ai.domain.models import (
    AgentTrace,
    CandidateProfile,
    EvidenceCandidate,
    EvidenceMatch,
    JobProfile,
    Requirement,
)
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.utils.text import best_snippet, remove_privacy_placeholders

from .base import run_agent
from .catalog import concept_group_for


def _explain_evidence(
    requirement: Requirement,
    group: ConceptGroup,
    candidate: dict[str, Any] | None,
) -> str:
    if candidate is None:
        return "Nenhum trecho do currículo apresentou evidência suficiente."

    labels = " e ".join(concept.canonical for concept in group.concepts)
    details: list[str] = []
    if candidate["explicitly_negated"]:
        details.append(f"{labels or requirement.text} foi explicitamente negado nesta evidência.")
    elif candidate.get("semantic_rule_match", False) and candidate.get("quantified_scale", False):
        details.append("Há evidência quantificada de escala operacional neste trecho.")
    elif candidate["concept_coverage"] == 0.0:
        details.append("Nenhum conceito exigido foi comprovado neste trecho.")
    elif (
        group.operator == "AND"
        and 0.0 < candidate["concept_coverage"] < 1.0
    ):
        covered = round(candidate["concept_coverage"] * len(group.concepts))
        details.append(
            f"Apenas {covered} de {len(group.concepts)} conceitos obrigatórios foi encontrado."
        )
    elif (
        group.operator == "OR"
        and candidate["concept_coverage"] == 1.0
        and not candidate["weak_experience"]
    ):
        details.append("Uma alternativa válida do requisito OR foi comprovada.")
    elif candidate["superficially_mentioned"]:
        details.append(
            f"{labels or requirement.text} foi apenas mencionado em contexto superficial."
        )
    elif candidate["weak_experience"]:
        details.append(
            f"{labels or requirement.text} aparece apenas como conhecimento básico ou teórico."
        )
    elif candidate["operational_experience"]:
        details.append(f"A evidência demonstra uso operacional de {labels or requirement.text}.")
    else:
        details.append(f"A evidência cita explicitamente {labels or requirement.text}.")

    if group.uses_literal_fallback:
        details.append("Correspondência baseada em conceito literal fora do catálogo.")
    return " ".join(details)


class EvidenceAgent:
    name = "Agente de Evidências"

    def __init__(self, engine: EmbeddingEngine) -> None:
        self.engine = engine

    def run(self, candidate: CandidateProfile, job: JobProfile, top_k: int) -> tuple[list[EvidenceMatch], AgentTrace]:
        def action() -> list[EvidenceMatch]:
            queries = [" | ".join([requirement.text, *requirement.aliases]) for requirement in job.requirements]
            concept_groups = [concept_group_for(requirement.text) for requirement in job.requirements]
            retrieved = self.engine.retrieve_many(
                queries,
                candidate.chunks,
                top_k=self.engine.retrieval_pool_size(top_k),
                concept_groups=[group.alias_groups for group in concept_groups],
            )

            output: list[EvidenceMatch] = []
            for requirement, query, group, candidates in zip(
                job.requirements,
                queries,
                concept_groups,
                retrieved,
                strict=True,
            ):
                candidates = self.engine.rerank(query, candidates)
                candidates = candidates[:top_k]
                for item in candidates:
                    item["text"] = best_snippet(item["text"], requirement.text)
                    item["literal_concept_fallback"] = group.uses_literal_fallback
                best = candidates[0] if candidates else None
                final = float(best["final_score"]) if best else 0.0
                explanation = _explain_evidence(requirement, group, best)
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
            warnings=lambda result: [
                *(
                    ["embedding-fallback"]
                    if self.engine.settings.embedding_enabled
                    and not self.engine.status["embedding_loaded"]
                    else []
                ),
                *(
                    ["reranker-fallback"]
                    if self.engine.settings.reranker_enabled
                    and not self.engine.status["reranker_loaded"]
                    else []
                ),
                *(["no-evidence-results"] if not result else []),
            ],
            evidence=lambda result: [
                f"requirement-id:{match.requirement.id}"
                for match in result
                if match.evidence is not None
            ],
            metadata=lambda result: {
                "requirement_count": len(result),
                "candidate_count": sum(len(match.top_candidates) for match in result),
                "literal_fallback_count": sum(
                    concept_group_for(match.requirement.text).uses_literal_fallback
                    for match in result
                ),
                "embedding_loaded": bool(self.engine.status["embedding_loaded"]),
                "reranker_loaded": bool(self.engine.status["reranker_loaded"]),
            },
        )
