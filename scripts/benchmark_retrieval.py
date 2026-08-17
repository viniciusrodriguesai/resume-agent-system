from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.benchmarks.rankers import (  # noqa: E402
    HybridRanker,
    Ranker,
    RapidFuzzRanker,
    TfidfRanker,
)
from evaluation.benchmarks.retrieval import run_retrieval_benchmark  # noqa: E402
from evaluation.schema import RetrievalCase  # noqa: E402
from resume_ai.infrastructure.embeddings import EmbeddingEngine  # noqa: E402
from resume_ai.settings import Settings  # noqa: E402

DEFAULT_DATASET = ROOT / "evaluation" / "datasets" / "synthetic_retrieval_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark evidence-retrieval variants.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Attempt to load configured embedding and reranker models.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def build_rankers(include_models: bool) -> list[Ranker]:
    base = Settings.for_profile("demo").model_copy(
        update={"history_enabled": False, "cache_enabled": False}
    )
    fallback = base.model_copy(update={"embedding_enabled": False, "reranker_enabled": False})
    rankers: list[Ranker] = [
        TfidfRanker(),
        RapidFuzzRanker(),
        HybridRanker("hybrid-fallback", EmbeddingEngine(fallback)),
    ]
    if include_models:
        embeddings = base.model_copy(update={"embedding_enabled": True, "reranker_enabled": False})
        reranked = base.model_copy(update={"embedding_enabled": True, "reranker_enabled": True})
        rankers.extend(
            [
                HybridRanker("embeddings", EmbeddingEngine(embeddings)),
                HybridRanker("embeddings+reranker", EmbeddingEngine(reranked)),
            ]
        )
    return rankers


def main() -> None:
    args = parse_args()
    dataset_bytes = args.dataset.read_bytes()
    cases = TypeAdapter(list[RetrievalCase]).validate_json(dataset_bytes)
    results = [
        run_retrieval_benchmark(cases, ranker, k=args.k, runs=args.runs).to_dict()
        for ranker in build_rankers(args.include_models)
    ]
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "path": args.dataset.name,
            "sha256": hashlib.sha256(dataset_bytes).hexdigest(),
            "cases": len(cases),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "parameters": {"k": args.k, "runs": args.runs, "include_models": args.include_models},
        "results": results,
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
