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

from evaluation.benchmarks.pipeline import run_pipeline_benchmark  # noqa: E402
from evaluation.schema import AnalysisCase  # noqa: E402
from resume_ai.application.analyze_resume import ResumeAnalysisService  # noqa: E402
from resume_ai.settings import Settings  # noqa: E402

DEFAULT_DATASET = ROOT / "evaluation" / "datasets" / "synthetic_pipeline_v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the complete analysis pipeline.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--profile", choices=["demo", "balanced", "complete"], default="demo")
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Attempt to load the selected profile's embedding and reranker models.",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_bytes = args.dataset.read_bytes()
    cases = TypeAdapter(list[AnalysisCase]).validate_json(dataset_bytes)
    settings = Settings.for_profile(args.profile).model_copy(
        update={
            "embedding_enabled": args.include_models,
            "reranker_enabled": args.include_models,
            "history_enabled": False,
            "cache_enabled": False,
        }
    )
    result = run_pipeline_benchmark(
        cases,
        ResumeAnalysisService(settings),
        runs=args.runs,
    )
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
        "parameters": {
            "runs": args.runs,
            "profile": args.profile,
            "include_models": args.include_models,
        },
        "result": result.to_dict(),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
