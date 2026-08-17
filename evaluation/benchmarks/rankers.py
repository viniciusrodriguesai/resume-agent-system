from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from rapidfuzz.fuzz import WRatio

from evaluation.schema import RetrievalCase
from resume_ai.agents.catalog import concept_alias_groups
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.utils.text import normalize, tfidf_similarity


class Ranker(Protocol):
    name: str

    def rank(self, case: RetrievalCase) -> list[str]: ...

    def status(self) -> dict[str, Any]: ...


class _FunctionRanker:
    def __init__(self, name: str, scorer: Callable[[str, str], float]) -> None:
        self.name = name
        self._scorer = scorer

    def rank(self, case: RetrievalCase) -> list[str]:
        scored = [
            (candidate.candidate_id, self._scorer(case.query, candidate.text))
            for candidate in case.candidates
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [candidate_id for candidate_id, _ in scored]

    def status(self) -> dict[str, Any]:
        return {"available": True, "actual_backend": self.name}


class TfidfRanker(_FunctionRanker):
    def __init__(self) -> None:
        super().__init__("tfidf", tfidf_similarity)


class RapidFuzzRanker(_FunctionRanker):
    def __init__(self) -> None:
        super().__init__(
            "rapidfuzz",
            lambda query, text: WRatio(normalize(query), normalize(text)) / 100.0,
        )


class HybridRanker:
    def __init__(self, name: str, engine: EmbeddingEngine) -> None:
        self.name = name
        self.engine = engine

    def rank(self, case: RetrievalCase) -> list[str]:
        ids_by_text = {candidate.text: candidate.candidate_id for candidate in case.candidates}
        if len(ids_by_text) != len(case.candidates):
            raise ValueError("hybrid benchmarks require unique candidate texts within a case")
        ranked = self.engine.retrieve(
            case.query,
            list(ids_by_text),
            top_k=len(case.candidates),
            concept_groups=concept_alias_groups(case.query),
        )
        ranked = self.engine.rerank(case.query, ranked)
        return [ids_by_text[item["text"]] for item in ranked]

    def status(self) -> dict[str, Any]:
        engine_status = self.engine.status
        embedding_loaded = bool(engine_status["embedding_loaded"])
        reranker_loaded = bool(engine_status["reranker_loaded"])
        if self.engine.settings.reranker_enabled and reranker_loaded:
            actual_backend = "embeddings+reranker"
        elif embedding_loaded:
            actual_backend = "embeddings"
        else:
            actual_backend = "tfidf+rapidfuzz-fallback"
        return {
            "available": True,
            "actual_backend": actual_backend,
            "embedding_loaded": embedding_loaded,
            "reranker_loaded": reranker_loaded,
            "embedding_error": bool(engine_status["embedding_error"]),
            "reranker_error": bool(engine_status["reranker_error"]),
        }
