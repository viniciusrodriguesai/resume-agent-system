from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

import numpy as np
from rapidfuzz.fuzz import WRatio

from resume_ai.settings import Settings
from resume_ai.utils.text import exact_phrase, normalize, tfidf_similarity


class EmbeddingEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: Any = None
        self._reranker: Any = None
        self._load_error: str | None = None
        self._reranker_error: str | None = None

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
            self._load_error = f"{type(exc).__name__}: {exc}"
            self._model = None
        return self._model

    def _load_reranker(self) -> Any:
        if self._reranker is not None or not self.settings.reranker_enabled:
            return self._reranker
        try:
            from sentence_transformers import CrossEncoder

            self._reranker = CrossEncoder(self.settings.reranker_model, device=self.settings.embedding_device)
        except Exception as exc:
            self._reranker_error = f"{type(exc).__name__}: {exc}"
            self._reranker = None
        return self._reranker

    def retrieve(self, query: str, chunks: list[str], top_k: int | None = None) -> list[dict[str, Any]]:
        if not chunks:
            return []
        top_k = max(1, top_k or self.settings.top_k)
        model = self._load_model()
        semantic_scores = [0.0] * len(chunks)
        semantic_method = "fallback lexical"
        if model is not None:
            try:
                query_text = query
                chunk_texts = chunks
                if "e5" in self.settings.embedding_model.lower():
                    query_text = f"query: {query}"
                    chunk_texts = [f"passage: {chunk}" for chunk in chunks]
                embeddings = model.encode(
                    [query_text, *chunk_texts],
                    normalize_embeddings=self.settings.normalize_embeddings,
                    batch_size=self.settings.embedding_batch_size,
                    show_progress_bar=False,
                )
                semantic_scores = np.dot(embeddings[1:], embeddings[0]).astype(float).tolist()
                semantic_method = f"{self.settings.embedding_model} ({self.settings.embedding_backend})"
            except Exception as exc:
                self._load_error = f"falha na inferência: {type(exc).__name__}: {exc}"

        aliases = [part.strip() for part in query.split("|") if part.strip()]
        candidates: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunks):
            exact = any(exact_phrase(chunk, alias) for alias in aliases)
            lexical = 1.0 if exact else tfidf_similarity(query, chunk)
            fuzzy = WRatio(normalize(query), normalize(chunk)) / 100
            semantic = float(semantic_scores[index]) if index < len(semantic_scores) else 0.0
            if model is None:
                final = 1.0 if exact else 0.65 * lexical + 0.35 * fuzzy
            else:
                final = max(semantic, 0.50 * semantic + 0.30 * lexical + 0.20 * fuzzy)
                if exact:
                    final = max(final, 0.97)
            candidates.append({
                "text": chunk,
                "lexical_score": round(lexical, 4),
                "fuzzy_score": round(fuzzy, 4),
                "semantic_score": round(semantic, 4),
                "reranker_score": 0.0,
                "final_score": round(max(0.0, min(final, 1.0)), 4),
                "retrieval_method": semantic_method if model is not None else ("alias exato" if exact else "TF-IDF + RapidFuzz"),
            })
        candidates.sort(key=lambda item: item["final_score"], reverse=True)
        return candidates[:top_k]

    def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not candidates or not self.settings.reranker_enabled:
            return candidates
        reranker = self._load_reranker()
        if reranker is None:
            return candidates
        top = candidates[: self.settings.reranker_top_n]
        try:
            scores = reranker.predict([[query, item["text"]] for item in top], show_progress_bar=False)
            for item, raw in zip(top, scores):
                value = float(raw)
                normalized = value if 0 <= value <= 1 else 1 / (1 + math.exp(-value))
                item["reranker_score"] = round(normalized, 4)
                item["final_score"] = round(0.25 * item["final_score"] + 0.75 * normalized, 4)
                item["retrieval_method"] += " + CrossEncoder"
            top.sort(key=lambda item: item["final_score"], reverse=True)
            return top + candidates[len(top):]
        except Exception as exc:
            self._reranker_error = f"falha na inferência: {type(exc).__name__}: {exc}"
            return candidates
