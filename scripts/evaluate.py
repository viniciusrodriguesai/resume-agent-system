from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from resume_ai.evaluation import classification_metrics  # noqa: E402
from resume_ai.infrastructure.embeddings import EmbeddingEngine  # noqa: E402
from resume_ai.settings import Settings  # noqa: E402


def classify(score: float) -> str:
    if score >= 0.57:
        return "matched"
    if score >= 0.32:
        return "partial"
    return "missing"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "labels",
        type=Path,
        nargs="?",
        default=Path("examples/evaluation_labels.csv"),
    )
    parser.add_argument(
        "--full-ai",
        action="store_true",
        help="Load local embedding and reranker models.",
    )
    args = parser.parse_args()

    settings = Settings.for_profile("demo").model_copy(
        update={"embedding_enabled": args.full_ai, "reranker_enabled": args.full_ai}
    )
    engine = EmbeddingEngine(settings)

    expected = []
    predicted = []
    with args.labels.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            ranked = engine.retrieve(row["requirement"], [row["evidence"]], top_k=1)
            score = float(ranked[0]["final_score"]) if ranked else 0.0
            expected.append(row["expected"])
            predicted.append(classify(score))

    print(json.dumps(classification_metrics(expected, predicted), indent=2))


if __name__ == "__main__":
    main()
