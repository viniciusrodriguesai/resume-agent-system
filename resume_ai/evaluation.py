from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol

from resume_ai.agents.catalog import concept_alias_groups

LABELS = ["matched", "partial", "missing"]


class RetrievalEngine(Protocol):
    def retrieve(
        self,
        query: str,
        chunks: list[str],
        top_k: int | None = None,
        concept_groups: list[list[str]] | None = None,
    ) -> list[dict[str, Any]]: ...


def classify_score(score: float) -> str:
    if score >= 0.57:
        return "matched"
    if score >= 0.32:
        return "partial"
    return "missing"


def classification_metrics(
    expected: Iterable[str],
    predicted: Iterable[str],
) -> dict[str, object]:
    expected_values = list(expected)
    predicted_values = list(predicted)
    if len(expected_values) != len(predicted_values):
        raise ValueError("Expected and predicted lists must have the same length.")
    unknown = (set(expected_values) | set(predicted_values)) - set(LABELS)
    if unknown:
        raise ValueError(f"Unknown labels: {', '.join(sorted(unknown))}")

    per_label = {}
    total_correct = 0
    for label in LABELS:
        true_positive = sum(
            e == label and p == label
            for e, p in zip(expected_values, predicted_values, strict=True)
        )
        false_positive = sum(
            e != label and p == label
            for e, p in zip(expected_values, predicted_values, strict=True)
        )
        false_negative = sum(
            e == label and p != label
            for e, p in zip(expected_values, predicted_values, strict=True)
        )
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(e == label for e in expected_values),
        }
        total_correct += true_positive

    macro_f1 = sum(
        item["f1"] for item in per_label.values()
    ) / len(LABELS)
    accuracy = (
        total_correct / len(expected_values)
        if expected_values
        else 0.0
    )
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_label": per_label,
    }


def evaluate_evidence_rows(
    rows: Iterable[dict[str, str]],
    engine: RetrievalEngine,
) -> dict[str, object]:
    expected: list[str] = []
    predicted: list[str] = []
    cases: list[dict[str, object]] = []

    for index, row in enumerate(rows, start=1):
        missing_columns = {"requirement", "evidence", "expected"} - set(row)
        if missing_columns:
            raise ValueError(
                f"Row {index} is missing columns: {', '.join(sorted(missing_columns))}"
            )
        ranked = engine.retrieve(
            row["requirement"],
            [row["evidence"]],
            top_k=1,
            concept_groups=concept_alias_groups(row["requirement"]),
        )
        score = float(ranked[0]["final_score"]) if ranked else 0.0
        prediction = classify_score(score)
        expected.append(row["expected"])
        predicted.append(prediction)
        cases.append(
            {
                "requirement": row["requirement"],
                "expected": row["expected"],
                "predicted": prediction,
                "score": round(score, 4),
                "correct": prediction == row["expected"],
            }
        )

    metrics = classification_metrics(expected, predicted)
    return {**metrics, "total": len(cases), "cases": cases}
