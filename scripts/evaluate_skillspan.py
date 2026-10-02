"""External, full-split token evaluation of the unchanged skill catalog adapter."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resume_ai.agents.catalog import detect_skills  # noqa: E402
from resume_ai.utils.text import exact_phrase, normalize  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def predicted_tokens(tokens: list[str]) -> set[int]:
    """Localize sentence-level canonical detections; not a native NER model."""
    skills = detect_skills(" ".join(tokens))
    result: set[int] = set()
    for skill in skills:
        for alias in skill.aliases:
            # A bounded minimal window is an adapter, not a gold-label transformation.
            maximum = len(normalize(alias).split()) * 4 + 4
            windows = []
            for start in range(len(tokens)):
                for end in range(start + 1, min(len(tokens), start + maximum) + 1):
                    if exact_phrase(normalize(" ".join(tokens[start:end])), alias):
                        windows.append((start, end))
                        break
            for start, end in windows:
                if not any(start <= other_start and other_end <= end and (start, end) != (other_start, other_end)
                           for other_start, other_end in windows):
                    result.update(range(start, end))
    return result


def bio_spans(tags: list[str], label: str) -> list[tuple[int, int]]:
    spans = []
    start: int | None = None
    for index, original in enumerate([*tags, "O"]):
        # Official JSONL mixes plain B/I with typed BIO in each label column.
        tag = f"{original}-{label}" if original in {"B", "I"} else original
        if tag not in {"O", f"B-{label}", f"I-{label}"}:
            raise ValueError(f"Invalid {label} BIO tag: {tag}")
        if tag == f"I-{label}" and start is None:
            raise ValueError("Orphan I tag")
        if tag in {"O", f"B-{label}"} and start is not None:
            spans.append((start, index))
            start = None
        if tag == f"B-{label}":
            start = index
    return spans


def merge_overlaps(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def score(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if tp + fp else 0.
    recall = tp / (tp + fn) if tp + fn else 0.
    return {"precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.}


def run(data: Path, output: Path, revision: str) -> dict[str, Any]:
    # Exclusive output directory prevents silent overwrite of a previous test pass.
    output.mkdir(parents=True, exist_ok=False)
    raw = data.read_text()
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected a nonempty list or JSONL")
    totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    clusters: dict[tuple[str, int], np.ndarray[Any, Any]] = {}
    for row in rows:
        tokens = row["tokens"]
        if not isinstance(tokens, list) or not tokens or not all(isinstance(t, str) for t in tokens):
            raise ValueError("Invalid tokens")
        if len(row["tags_skill"]) != len(tokens) or len(row["tags_knowledge"]) != len(tokens):
            raise ValueError("Token/label length mismatch")
        source = row["source"]
        if source not in {"house", "tech"}:
            raise ValueError("Unexpected source")
        spans = merge_overlaps(bio_spans(row["tags_skill"], "Skill") + bio_spans(row["tags_knowledge"], "Knowledge"))
        gold = {i for start, end in spans for i in range(start, end)}
        predicted = predicted_tokens(tokens)
        counts = {"sentences": 1, "tokens": len(tokens), "gold_tokens": len(gold),
                  "predicted_tokens": len(predicted), "true_positive_tokens": len(gold & predicted),
                  "false_positive_tokens": len(predicted - gold), "missed_tokens": len(gold - predicted),
                  "gold_spans": len(spans),
                  "fully_covered_gold_spans": sum(set(range(a, b)) <= predicted for a, b in spans)}
        for group in ["all", source]:
            for key, value in counts.items():
                totals[group][key] += value
        cluster_key = (source, int(row["idx"]))
        if cluster_key not in clusters:
            clusters[cluster_key] = np.zeros(3, dtype=np.int64)
        clusters[cluster_key] += [counts["true_positive_tokens"], counts["false_positive_tokens"], counts["missed_tokens"]]
    if set(totals) != {"all", "house", "tech"}:
        raise ValueError("The complete test split must contain both released sources")
    groups = {group: {**counts, **score(counts["true_positive_tokens"], counts["false_positive_tokens"], counts["missed_tokens"])}
              for group, counts in totals.items()}
    values = np.stack(list(clusters.values()))
    rng = np.random.default_rng(20261002)
    bootstrap: dict[str, list[float]] = {key: [] for key in ["precision", "recall", "f1"]}
    for _ in range(500):
        sampled = values[rng.integers(0, len(values), size=len(values))].sum(axis=0)
        for key, value in score(*map(int, sampled)).items():
            bootstrap[key].append(value)
    report: dict[str, Any] = {
        "protocol": "skillspan-catalog-token-v1", "source_revision": revision,
        "dataset_sha256": sha(data), "script_sha256": sha(Path(__file__)),
        "catalog_sha256": sha(ROOT / "resume_ai/agents/catalog.py"),
        "normalizer_sha256": sha(ROOT / "resume_ai/utils/text.py"),
        "protocol_sha256": sha(ROOT / "docs/SKILLSPAN_PROTOCOL.md"),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": platform.python_version(), "versions": {p: importlib.metadata.version(p) for p in
        ["numpy", "pydantic", "rapidfuzz"]}, "posting_clusters": len(clusters),
        "groups": groups, "bootstrap_replicates": 500,
        "cluster_bootstrap_ci95": {key: np.quantile(series, [.025, .975]).tolist() for key, series in bootstrap.items()},
        "scope": "External human skill/knowledge annotations; adapter token metrics, not end-to-end matching labels",
    }
    (output / "metrics.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    result = run(args.data, args.output, args.source_revision)
    print(json.dumps(result["groups"]["all"], indent=2))
