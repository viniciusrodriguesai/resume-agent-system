from __future__ import annotations

import math
from typing import Any

import numpy as np
from rapidfuzz.fuzz import WRatio

from resume_ai.domain.scoring import THRESHOLDS
from resume_ai.settings import Settings
from resume_ai.utils.text import (
    content_hash,
    exact_phrase,
    high_volume_request_requirement,
    negated_phrase,
    normalize,
    operational_experience_phrase,
    production_experience_phrase,
    quantified_request_volume,
    requirement_demands_experience,
    requirement_intent,
    superficial_phrase,
    tfidf_similarity,
    weak_experience_phrase,
)

INCOMPLETE_CUMULATIVE_FLOOR = THRESHOLDS["equilibrado"]["partial"]
INCOMPLETE_CUMULATIVE_CEILING = THRESHOLDS["flexível"]["matched"] - 0.01
SUPERFICIAL_EVIDENCE_CEILING = THRESHOLDS["flexível"]["matched"] - 0.01
WEAK_EXPERIENCE_CEILING = THRESHOLDS["flexível"]["matched"] - 0.01
QUANTIFIED_SCALE_FLOOR = THRESHOLDS["conservador"]["partial"]
OPERATIONAL_EXPERIENCE_BONUS = 0.06
OPERATIONAL_EXPERIENCE_FLOOR = THRESHOLDS["conservador"]["matched"]
ZERO_CONCEPT_COVERAGE_CEILING = THRESHOLDS["flexível"]["partial"]
MIN_RERANK_POOL = 12
EXPERIENCE_LISTING_FLOOR = THRESHOLDS["flexível"]["matched"]
EXPERIENCE_LISTING_CEILING = THRESHOLDS["conservador"]["matched"] - 0.01
OPERATIONAL_EXPERIENCE_CEILING = 0.84
PRODUCTION_EXPERIENCE_FLOOR = 0.85
WEAK_EXPERIENCE_FLOOR = 0.16
KNOWLEDGE_EVIDENCE_FLOOR = THRESHOLDS["equilibrado"]["matched"]


def _safe_backend_error(stage: str, error: BaseException) -> str:
    return f"{stage}:{type(error).__name__}"


def _apply_final_safety_constraints(score: float, candidate: dict[str, Any]) -> float:
    """Keep model scores subordinate to deterministic evidence policy."""
    adjusted = max(0.0, min(score, 1.0))
    coverage = float(candidate.get("concept_coverage", 0.0))
    concept_count = int(candidate.get("concept_count", 0))
    alternatives = bool(candidate.get("alternative_concepts", False))
    superficial = bool(candidate.get("superficially_mentioned", False))
    evidence_strength = int(candidate.get("evidence_strength", 0))

    complete_class_evidence = concept_count <= 1 or alternatives or coverage == 1.0
    if (
        candidate.get("requirement_intent") == "knowledge"
        and complete_class_evidence
        and coverage > 0.0
        and evidence_strength >= 2
    ):
        adjusted = max(adjusted, KNOWLEDGE_EVIDENCE_FLOOR)
    elif candidate.get("requirement_intent") != "knowledge" and complete_class_evidence:
        if evidence_strength >= 4:
            adjusted = max(adjusted, PRODUCTION_EXPERIENCE_FLOOR)
        elif evidence_strength == 3:
            adjusted = max(
                OPERATIONAL_EXPERIENCE_FLOOR,
                min(adjusted, OPERATIONAL_EXPERIENCE_CEILING),
            )
        elif evidence_strength == 2:
            adjusted = max(
                EXPERIENCE_LISTING_FLOOR,
                min(adjusted, EXPERIENCE_LISTING_CEILING),
            )
        elif evidence_strength == 1:
            adjusted = max(WEAK_EXPERIENCE_FLOOR, min(adjusted, WEAK_EXPERIENCE_CEILING))

    if (
        candidate.get("operational_experience", False)
        and coverage > 0.0
        and (concept_count <= 1 or alternatives or coverage == 1.0)
        and not candidate.get("explicitly_negated", False)
        and not candidate.get("weak_experience", False)
        and (not superficial or alternatives)
    ):
        adjusted = max(adjusted, OPERATIONAL_EXPERIENCE_FLOOR)
    if candidate.get("quantified_scale", False):
        adjusted = max(adjusted, QUANTIFIED_SCALE_FLOOR)
    if concept_count > 1 and not alternatives and 0.0 < coverage < 1.0:
        adjusted = max(
            INCOMPLETE_CUMULATIVE_FLOOR,
            min(adjusted, INCOMPLETE_CUMULATIVE_CEILING),
        )

    if candidate.get("explicitly_negated", False):
        adjusted = min(adjusted, 0.15)
    elif candidate.get("weak_experience", False):
        adjusted = min(adjusted, WEAK_EXPERIENCE_CEILING)
    elif superficial and (not alternatives or coverage == 0.0):
        adjusted = min(adjusted, SUPERFICIAL_EVIDENCE_CEILING)
    if (
        concept_count > 0
        and coverage == 0.0
        and not candidate.get("semantic_rule_match", False)
    ):
        adjusted = min(adjusted, ZERO_CONCEPT_COVERAGE_CEILING)
    return adjusted


class EmbeddingEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: Any = None
        self._reranker: Any = None
        self._load_error: str | None = None
        self._reranker_error: str | None = None
        self._chunk_embedding_cache: dict[str, np.ndarray] = {}

    @property
    def status(self) -> dict[str, Any]:
        return {
            "embedding_enabled": self.settings.embedding_enabled,
            "embedding_model": self.settings.embedding_model,
            "embedding_backend": self.settings.embedding_backend,
            "embedding_loaded": self._model is not None,
            "embedding_error": self._load_error,
            "reranker_enabled": self.settings.reranker_enabled,
            "reranker_model": self.settings.reranker_model,
            "reranker_loaded": self._reranker is not None,
            "reranker_error": self._reranker_error,
            "chunk_embedding_cache_entries": len(self._chunk_embedding_cache),
        }

    def _load_model(self) -> Any:
        if self._model is not None or not self.settings.embedding_enabled:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            kwargs: dict[str, Any] = {"device": self.settings.embedding_device}
            if self.settings.embedding_backend != "torch":
                kwargs["backend"] = self.settings.embedding_backend
            try:
                self._model = SentenceTransformer(self.settings.embedding_model, **kwargs)
            except TypeError:
                kwargs.pop("backend", None)
                self._model = SentenceTransformer(self.settings.embedding_model, **kwargs)
        except Exception as exc:
            self._load_error = _safe_backend_error("load", exc)
            self._model = None
        return self._model

    def _load_reranker(self) -> Any:
        if self._reranker is not None or not self.settings.reranker_enabled:
            return self._reranker
        try:
            from sentence_transformers import CrossEncoder

            self._reranker = CrossEncoder(self.settings.reranker_model, device=self.settings.embedding_device)
        except Exception as exc:
            self._reranker_error = _safe_backend_error("load", exc)
            self._reranker = None
        return self._reranker

    def retrieval_pool_size(self, final_top_k: int) -> int:
        if not self.settings.reranker_enabled:
            return final_top_k
        return max(final_top_k * 4, self.settings.reranker_top_n * 3, MIN_RERANK_POOL)

    def _prepare_for_model(self, texts: list[str], *, query: bool) -> list[str]:
        if "e5" not in self.settings.embedding_model.lower():
            return texts
        prefix = "query: " if query else "passage: "
        return [f"{prefix}{text}" for text in texts]

    def _encode_chunks(self, model: Any, chunks: list[str]) -> np.ndarray:
        cache_key = content_hash(self.settings.embedding_model, self.settings.embedding_backend, *chunks)
        cached = self._chunk_embedding_cache.get(cache_key)
        if cached is not None:
            return cached

        encoded = model.encode(
            self._prepare_for_model(chunks, query=False),
            normalize_embeddings=self.settings.normalize_embeddings,
            batch_size=self.settings.embedding_batch_size,
            show_progress_bar=False,
        )
        matrix = np.asarray(encoded, dtype=float)
        # O cache é pequeno por sessão e evita recalcular o mesmo currículo.
        if len(self._chunk_embedding_cache) >= 4:
            self._chunk_embedding_cache.pop(next(iter(self._chunk_embedding_cache)))
        self._chunk_embedding_cache[cache_key] = matrix
        return matrix

    @staticmethod
    def _concept_coverage(
        chunk: str,
        groups: list[list[str]],
        *,
        require_operational: bool = False,
    ) -> float:
        if not groups:
            return 0.0
        covered = 0
        for aliases in groups:
            present_aliases = [alias for alias in aliases if exact_phrase(chunk, alias)]
            if not present_aliases:
                continue
            maximum_specificity = max(
                (len(normalize(alias).split()), len(normalize(alias)))
                for alias in present_aliases
            )
            most_specific_aliases = [
                alias
                for alias in present_aliases
                if (len(normalize(alias).split()), len(normalize(alias))) == maximum_specificity
            ]
            if any(
                not superficial_phrase(chunk, alias)
                and (not require_operational or not weak_experience_phrase(chunk, alias))
                for alias in most_specific_aliases
            ):
                covered += 1
        return covered / len(groups)

    def _score_candidates(
        self,
        query: str,
        chunks: list[str],
        semantic_scores: list[float],
        semantic_method: str,
        concept_groups: list[list[str]],
        top_k: int,
        model_available: bool,
    ) -> list[dict[str, Any]]:
        requirement_text = query.split("|", 1)[0].strip()
        intent = requirement_intent(requirement_text)
        candidates: list[dict[str, Any]] = []

        for index, chunk in enumerate(chunks):
            exact_requirement = exact_phrase(chunk, requirement_text)
            negated_concept = any(
                negated_phrase(chunk, alias)
                for group in concept_groups
                for alias in group
            )
            lexical = max(0.0, min(tfidf_similarity(requirement_text, chunk), 1.0))
            fuzzy = WRatio(normalize(requirement_text), normalize(chunk)) / 100
            semantic = float(semantic_scores[index]) if index < len(semantic_scores) else 0.0
            semantic = max(0.0, min(semantic, 1.0))
            coverage = self._concept_coverage(chunk, concept_groups)
            experience_required = requirement_demands_experience(requirement_text)
            strong_coverage = self._concept_coverage(
                chunk,
                concept_groups,
                require_operational=experience_required,
            )
            explicitly_negated = negated_phrase(chunk, requirement_text) or (
                negated_concept and coverage == 0.0
            )
            superficially_mentioned = superficial_phrase(chunk, requirement_text) or any(
                superficial_phrase(chunk, alias)
                for group in concept_groups
                for alias in group
            )
            normalized_requirement = f" {normalize(requirement_text)} "
            alternatives = len(concept_groups) > 1 and (
                " ou " in normalized_requirement or " or " in normalized_requirement
            )
            if alternatives:
                coverage = 1.0 if coverage > 0 else 0.0
                strong_coverage = 1.0 if strong_coverage > 0 else 0.0

            weak_experience = experience_required and coverage > 0.0 and strong_coverage == 0.0
            operational_experience = experience_required and any(
                operational_experience_phrase(chunk, alias)
                for group in concept_groups
                for alias in group
            )
            production_experience = experience_required and any(
                production_experience_phrase(chunk, alias)
                for group in concept_groups
                for alias in group
            )
            quantified_scale = high_volume_request_requirement(
                requirement_text
            ) and quantified_request_volume(chunk)
            if explicitly_negated:
                evidence_strength = 0
            elif weak_experience or superficially_mentioned:
                evidence_strength = 1
            elif coverage > 0.0 and production_experience:
                evidence_strength = 4
            elif coverage > 0.0 and operational_experience:
                evidence_strength = 3
            elif coverage > 0.0:
                evidence_strength = 2
            else:
                evidence_strength = 0

            if model_available:
                final = 0.42 * semantic + 0.28 * lexical + 0.15 * fuzzy + 0.15 * coverage
            else:
                final = 0.48 * lexical + 0.30 * fuzzy + 0.22 * coverage

            # Boosts controlados: só uma ocorrência de Pandas não pode provar um
            # requisito que também exige NumPy e Scikit-learn.
            if exact_requirement:
                final = max(final, 0.94 + 0.04 * final)
            elif concept_groups and strong_coverage == 1.0:
                floor = 0.78 if len(concept_groups) > 1 else 0.74
                final = max(final, floor + 0.16 * final)
            elif len(concept_groups) > 1 and not alternatives and strong_coverage > 0.0:
                # Uma competência comprovada é evidência parcial, mesmo quando
                # a similaridade da frase cumulativa completa é baixa.
                final = max(
                    INCOMPLETE_CUMULATIVE_FLOOR,
                    min(final, INCOMPLETE_CUMULATIVE_CEILING),
                )
            if operational_experience:
                final = min(1.0, final + OPERATIONAL_EXPERIENCE_BONUS)
            if quantified_scale:
                final = max(final, QUANTIFIED_SCALE_FLOOR)
            if explicitly_negated:
                final = min(final, 0.15)
            elif weak_experience:
                final = min(final, WEAK_EXPERIENCE_CEILING)
            elif superficially_mentioned and (not alternatives or strong_coverage == 0.0):
                final = min(final, SUPERFICIAL_EVIDENCE_CEILING)

            method_parts = [semantic_method if model_available else "TF-IDF + RapidFuzz"]
            if concept_groups:
                method_parts.append(f"cobertura de conceitos {coverage:.0%}")
            if exact_requirement:
                method_parts.append("frase exata")
            if explicitly_negated:
                method_parts.append("menção negada")
            if superficially_mentioned:
                method_parts.append("menção superficial")
            if weak_experience:
                method_parts.append("evidência básica ou teórica")
            if quantified_scale:
                method_parts.append("carga quantificada")
            if operational_experience:
                method_parts.append("contexto operacional")

            candidate = {
                "text": chunk,
                "lexical_score": round(lexical, 4),
                "fuzzy_score": round(fuzzy, 4),
                "semantic_score": round(semantic, 4),
                "reranker_score": 0.0,
                "base_score": round(max(0.0, min(final, 1.0)), 4),
                "final_score": round(max(0.0, min(final, 1.0)), 4),
                "policy_adjusted_score": round(max(0.0, min(final, 1.0)), 4),
                "retrieval_method": " · ".join(method_parts),
                "concept_coverage": round(coverage, 4),
                "strong_coverage": round(strong_coverage, 4),
                "concept_count": len(concept_groups),
                "alternative_concepts": alternatives,
                "requirement_intent": intent.value,
                "explicitly_negated": explicitly_negated,
                "superficially_mentioned": superficially_mentioned,
                "weak_experience": weak_experience,
                "operational_experience": operational_experience,
                "production_experience": production_experience,
                "evidence_strength": evidence_strength,
                "quantified_scale": quantified_scale,
                "semantic_rule_match": quantified_scale,
                "exact_requirement": exact_requirement,
            }
            policy_adjusted = _apply_final_safety_constraints(final, candidate)
            candidate["policy_adjusted_score"] = round(policy_adjusted, 4)
            candidate["final_score"] = candidate["policy_adjusted_score"]
            candidates.append(candidate)

        candidates.sort(key=lambda item: item["final_score"], reverse=True)
        selected = candidates[:top_k]
        selected_ids = {id(item) for item in selected}
        selected.extend(
            item
            for item in candidates[top_k:]
            if id(item) not in selected_ids
            and (
                item["exact_requirement"]
                or item["strong_coverage"] > 0.0
                or item["operational_experience"]
                or item["quantified_scale"]
                or item["explicitly_negated"]
                or item["superficially_mentioned"]
            )
        )
        selected.sort(key=lambda item: item["final_score"], reverse=True)
        return selected

    def retrieve_many(
        self,
        queries: list[str],
        chunks: list[str],
        *,
        top_k: int | None = None,
        concept_groups: list[list[list[str]]] | None = None,
    ) -> list[list[dict[str, Any]]]:
        """Recupera evidências para todos os requisitos em lote.

        Na V5, o currículo era codificado novamente para cada requisito. A V5.1
        codifica os trechos uma vez e todas as consultas em um único lote.
        """
        if not queries:
            return []
        if not chunks:
            return [[] for _ in queries]

        top_k = max(1, top_k or self.settings.top_k)
        groups_per_query = concept_groups or [[] for _ in queries]
        model = self._load_model()
        semantic_method = "fallback lexical"
        semantic_matrix = np.zeros((len(queries), len(chunks)), dtype=float)

        if model is not None:
            try:
                chunk_embeddings = self._encode_chunks(model, chunks)
                query_embeddings = model.encode(
                    self._prepare_for_model(queries, query=True),
                    normalize_embeddings=self.settings.normalize_embeddings,
                    batch_size=self.settings.embedding_batch_size,
                    show_progress_bar=False,
                )
                semantic_matrix = np.matmul(np.asarray(query_embeddings, dtype=float), chunk_embeddings.T)
                semantic_method = f"{self.settings.embedding_model} ({self.settings.embedding_backend})"
            except Exception as exc:
                self._load_error = _safe_backend_error("inference", exc)
                model = None
                semantic_matrix = np.zeros((len(queries), len(chunks)), dtype=float)

        results: list[list[dict[str, Any]]] = []
        for index, query in enumerate(queries):
            groups = groups_per_query[index] if index < len(groups_per_query) else []
            results.append(self._score_candidates(
                query=query,
                chunks=chunks,
                semantic_scores=semantic_matrix[index].astype(float).tolist(),
                semantic_method=semantic_method,
                concept_groups=groups,
                top_k=top_k,
                model_available=model is not None,
            ))
        return results

    def retrieve(
        self,
        query: str,
        chunks: list[str],
        top_k: int | None = None,
        concept_groups: list[list[str]] | None = None,
    ) -> list[dict[str, Any]]:
        return self.retrieve_many(
            [query],
            chunks,
            top_k=top_k,
            concept_groups=[concept_groups or []],
        )[0]

    def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not candidates or not self.settings.reranker_enabled:
            return candidates
        reranker = self._load_reranker()
        if reranker is None:
            return candidates
        original_indexes = {id(item): index for index, item in enumerate(candidates)}
        top = candidates[: self.settings.reranker_top_n]
        try:
            scores = reranker.predict([[query, item["text"]] for item in top], show_progress_bar=False)
            for item, raw in zip(top, scores, strict=True):
                value = float(raw)
                normalized = value if 0 <= value <= 1 else 1 / (1 + math.exp(-value))
                item["reranker_score"] = round(normalized, 4)
                reranked = 0.35 * item["final_score"] + 0.65 * normalized
                item["final_score"] = round(reranked, 4)
                item["retrieval_method"] += " · CrossEncoder"
            for item in candidates:
                policy_adjusted = _apply_final_safety_constraints(item["final_score"], item)
                item["policy_adjusted_score"] = round(policy_adjusted, 4)
                item["final_score"] = item["policy_adjusted_score"]
            return sorted(
                candidates,
                key=lambda item: (
                    -float(item.get("final_score", 0.0)),
                    -float(item.get("concept_coverage", 0.0)),
                    -int(bool(item.get("operational_experience", False))),
                    -float(item.get("lexical_score", 0.0)),
                    original_indexes[id(item)],
                ),
            )
        except Exception as exc:
            self._reranker_error = _safe_backend_error("inference", exc)
            return candidates
