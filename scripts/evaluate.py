from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from resume_ai.evaluation import evaluate_evidence_rows  # noqa: E402
from resume_ai.infrastructure.embeddings import EmbeddingEngine  # noqa: E402
from resume_ai.settings import Settings  # noqa: E402


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
    parser.add_argument("--min-accuracy", type=float, default=0.75)
    parser.add_argument("--min-macro-f1", type=float, default=0.70)
    args = parser.parse_args()

    settings = Settings.for_profile("demo").model_copy(
        update={"embedding_enabled": args.full_ai, "reranker_enabled": args.full_ai}
    )
    engine = EmbeddingEngine(settings)

    with args.labels.open("r", encoding="utf-8-sig", newline="") as handle:
        result = evaluate_evidence_rows(csv.DictReader(handle), engine)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["accuracy"] < args.min_accuracy or result["macro_f1"] < args.min_macro_f1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
