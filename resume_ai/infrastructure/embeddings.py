from __future__ import annotations

import math
from typing import Any

import numpy as np
from rapidfuzz.fuzz import WRatio

from resume_ai.domain.scoring import THRESHOLDS
from resume_ai.settings import Settings
from resume_ai.utils.text import content_hash, exact_phrase, negated_phrase, normalize, tfidf_similarity

INCOMPLETE_CUMULATIVE_FLOOR = THRESHOLDS["equilibrado"]["partial"]


def _safe_backend_error(stage: str, error: BaseException) -> str:
    return f"{stage}:{type(error).__name__}"


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
    def _concept_coverage(chunk: str, groups: list[list[str]]) -> float:
        if not groups:
            return 0.0
        covered = 0
        for aliases in groups:
            if any(exact_phrase(chunk, alias) for alias in aliases):
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
        candidates: list[dict[str, Any]] = []

        for index, chunk in enumerate(chunks):
            exact_requirement = exact_phrase(chunk, requirement_text)
            explicitly_negated = len(concept_groups) <= 1 and (
                negated_phrase(chunk, requirement_text)
                or any(
                    negated_phrase(chunk, alias)
                    for group in concept_groups
                    for alias in group
                )
            )
            lexical = max(0.0, min(tfidf_similarity(requirement_text, chunk), 1.0))
            fuzzy = WRatio(normalize(requirement_text), normalize(chunk)) / 100
            semantic = float(semantic_scores[index]) if index < len(semantic_scores) else 0.0
            semantic = max(0.0, min(semantic, 1.0))
            coverage = self._concept_coverage(chunk, concept_groups)
            normalized_requirement = f" {normalize(requirement_text)} "
            alternatives = len(concept_groups) > 1 and (
                " ou " in normalized_requirement or " or " in normalized_requirement
            )
            if alternatives:
                coverage = 1.0 if coverage > 0 else 0.0

            if model_available:
                final = 0.42 * semantic + 0.28 * lexical + 0.15 * fuzzy + 0.15 * coverage
            else:
                final = 0.48 * lexical + 0.30 * fuzzy + 0.22 * coverage

            # Boosts controlados: só uma ocorrência de Pandas não pode provar um
            # requisito que também exige NumPy e Scikit-learn.
            if exact_requirement:
                final = max(final, 0.94 + 0.04 * final)
            elif concept_groups and coverage == 1.0:
                floor = 0.78 if len(concept_groups) > 1 else 0.74
                final = max(final, floor + 0.16 * final)
            elif len(concept_groups) > 1 and not alternatives and coverage > 0.0:
                # Uma competência comprovada é evidência parcial, mesmo quando
                # a similaridade da frase cumulativa completa é baixa.
                final = max(final, INCOMPLETE_CUMULATIVE_FLOOR)
            if explicitly_negated:
                final = min(final, 0.15)

            method_parts = [semantic_method if model_available else "TF-IDF + RapidFuzz"]
            if concept_groups:
                method_parts.append(f"cobertura de conceitos {coverage:.0%}")
            if exact_requirement:
                method_parts.append("frase exata")
            if explicitly_negated:
                method_parts.append("menção negada")

            candidates.append({
                "text": chunk,
                "lexical_score": round(lexical, 4),
                "fuzzy_score": round(fuzzy, 4),
                "semantic_score": round(semantic, 4),
                "reranker_score": 0.0,
                "final_score": round(max(0.0, min(final, 1.0)), 4),
                "retrieval_method": " · ".join(method_parts),
                "concept_coverage": round(coverage, 4),
                "concept_count": len(concept_groups),
                "alternative_concepts": alternatives,
            })

        candidates.sort(key=lambda item: item["final_score"], reverse=True)
        return candidates[:top_k]

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
        top = candidates[: self.settings.reranker_top_n]
        try:
            scores = reranker.predict([[query, item["text"]] for item in top], show_progress_bar=False)
            for item, raw in zip(top, scores, strict=True):
                value = float(raw)
                normalized = value if 0 <= value <= 1 else 1 / (1 + math.exp(-value))
                item["reranker_score"] = round(normalized, 4)
                reranked = 0.35 * item["final_score"] + 0.65 * normalized
                # Em requisitos cumulativos, o reranker não pode transformar uma
                # evidência de apenas uma competência em correspondência completa.
                if (
                    item.get("concept_count", 0) > 1
                    and not item.get("alternative_concepts", False)
                    and item.get("concept_coverage", 0.0) < 1.0
                ):
                    reranked = max(
                        INCOMPLETE_CUMULATIVE_FLOOR,
                        min(reranked, 0.59),
                    )
                item["final_score"] = round(reranked, 4)
                item["retrieval_method"] += " · CrossEncoder"
            top.sort(key=lambda item: item["final_score"], reverse=True)
            return top + candidates[len(top):]
        except Exception as exc:
            self._reranker_error = _safe_backend_error("inference", exc)
            return candidates
