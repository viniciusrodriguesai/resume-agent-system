import csv
from pathlib import Path

from resume_ai.evaluation import evaluate_evidence_rows
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.settings import Settings


def test_lexical_quality_baseline(tmp_path):
    root = Path(__file__).resolve().parents[1]
    with (root / "examples" / "evaluation_labels.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
    )

    result = evaluate_evidence_rows(rows, EmbeddingEngine(settings))

    assert result["total"] >= 20
    assert result["accuracy"] >= 0.95
    assert result["macro_f1"] >= 0.90
