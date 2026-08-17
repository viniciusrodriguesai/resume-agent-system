from evaluation.benchmarks.rankers import HybridRanker, RapidFuzzRanker, TfidfRanker
from evaluation.schema import RetrievalCase
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings


def make_case() -> RetrievalCase:
    return RetrievalCase(
        case_id="python",
        query="Python API",
        candidates=[
            {"candidate_id": "relevant", "text": "Desenvolvi uma API usando Python."},
            {"candidate_id": "noise", "text": "Criei protótipos no Figma."},
        ],
        relevant_candidate_ids=["relevant"],
    )


def test_tfidf_ranker_prefers_lexical_evidence() -> None:
    assert TfidfRanker().rank(make_case())[0] == "relevant"


def test_rapidfuzz_ranker_prefers_textual_evidence() -> None:
    assert RapidFuzzRanker().rank(make_case())[0] == "relevant"


def test_hybrid_ranker_reports_lexical_fallback_when_embeddings_are_disabled(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
    )
    ranker = HybridRanker("pipeline-fallback", EmbeddingEngine(settings))

    assert ranker.rank(make_case())[0] == "relevant"
    assert ranker.status()["actual_backend"] == "tfidf+rapidfuzz-fallback"
