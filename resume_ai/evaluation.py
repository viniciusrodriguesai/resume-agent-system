from __future__ import annotations

from collections.abc import Iterable

LABELS = ["matched", "partial", "missing"]

def classification_metrics(
    expected: Iterable[str],
    predicted: Iterable[str],
) -> dict[str, object]:
    expected_values = list(expected)
    predicted_values = list(predicted)
    if len(expected_values) != len(predicted_values):
        raise ValueError("Expected and predicted lists must have the same length.")

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
