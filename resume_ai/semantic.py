from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence

from .config import Settings
from .text import lexical_similarity


def _sigmoid(value: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-value))
    except OverflowError:
        return 0.0 if value < 0 else 1.0


@dataclass
class SemanticStatus:
    embedding_available: bool
    reranker_available: bool
    embedding_model: str
    reranker_model: str
    fallback: str = "local TF-IDF cosine similarity"


class SemanticEngine:
    """
    Two-stage local retrieval:
    1. SentenceTransformer bi-encoder when installed, otherwise lexical TF-IDF.
    2. CrossEncoder reranking when installed, otherwise first-stage score.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._embedder = None
        self._reranker = None
        self._embedding_error = ""
        self._reranker_error = ""

    def load(self) -> SemanticStatus:
        if self.settings.enable_embeddings and self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(
                    self.settings.embedding_model
                )
            except Exception as exc:
                self._embedding_error = str(exc)

        if self.settings.enable_reranker and self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(
                    self.settings.reranker_model
                )
            except Exception as exc:
                self._reranker_error = str(exc)

        return self.status()

    def status(self) -> SemanticStatus:
        return SemanticStatus(
            embedding_available=self._embedder is not None,
            reranker_available=self._reranker is not None,
            embedding_model=self.settings.embedding_model,
            reranker_model=self.settings.reranker_model,
        )

    def diagnostics(self) -> Dict[str, object]:
        state = self.status()
        return {
            **state.__dict__,
            "embedding_error": self._embedding_error,
            "reranker_error": self._reranker_error,
        }

    def retrieve(
        self,
        query: str,
        candidates: Sequence[str],
        top_k: int | None = None,
    ) -> List[Dict[str, object]]:
        if not candidates:
            return []

        k = min(top_k or self.settings.top_k, len(candidates))
        scores = self._first_stage(query, candidates)
        ranked_indices = sorted(
            range(len(candidates)),
            key=lambda index: scores[index],
            reverse=True,
        )[:k]

        first_stage = [
            {
                "text": candidates[index],
                "retrieval_score": round(float(scores[index]), 4),
            }
            for index in ranked_indices
        ]

        if self._reranker is None:
            return [
                {
                    **item,
                    "reranker_score": None,
                    "final_score": item["retrieval_score"],
                    "engine": (
                        "sentence-transformer"
                        if self._embedder is not None
                        else "lexical-fallback"
                    ),
                }
                for item in first_stage
            ]

        pairs = [[query, item["text"]] for item in first_stage]
        raw_scores = self._reranker.predict(pairs)
        reranked = []
        for item, raw in zip(first_stage, raw_scores):
            normalized = _sigmoid(float(raw))
            final_score = (
                0.35 * float(item["retrieval_score"])
                + 0.65 * normalized
            )
            reranked.append(
                {
                    **item,
                    "reranker_score": round(normalized, 4),
                    "final_score": round(final_score, 4),
                    "engine": "bi-encoder+cross-encoder",
                }
            )
        return sorted(
            reranked,
            key=lambda item: float(item["final_score"]),
            reverse=True,
        )

    def _first_stage(
        self,
        query: str,
        candidates: Sequence[str],
    ) -> List[float]:
        if self._embedder is None:
            return [
                lexical_similarity(query, candidate)
                for candidate in candidates
            ]

        embeddings = self._embedder.encode(
            [query, *candidates],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        query_embedding = embeddings[0]
        return [
            float(query_embedding @ candidate_embedding)
            for candidate_embedding in embeddings[1:]
        ]
