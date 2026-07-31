from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from resume_ai.evaluation import classification_metrics
from resume_ai.semantic import SemanticEngine


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

    engine = SemanticEngine()
    if args.full_ai:
        engine.load()

    expected = []
    predicted = []
    with args.labels.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            ranked = engine.retrieve(
                row["requirement"],
                [row["evidence"]],
                top_k=1,
            )
            score = float(ranked[0]["final_score"]) if ranked else 0.0
            expected.append(row["expected"])
            predicted.append(classify(score))

    print(json.dumps(
        classification_metrics(expected, predicted),
        indent=2,
    ))


if __name__ == "__main__":
    main()
