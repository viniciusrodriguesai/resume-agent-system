from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfusionCounts:
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int


def confusion_counts(
    expected: Iterable[bool],
    predicted: Iterable[bool],
) -> ConfusionCounts:
    expected_values = list(expected)
    predicted_values = list(predicted)
    if len(expected_values) != len(predicted_values):
        raise ValueError("expected and predicted must have the same length")

    pairs = list(zip(expected_values, predicted_values, strict=True))
    return ConfusionCounts(
        true_positive=sum(expected_value and predicted_value for expected_value, predicted_value in pairs),
        false_positive=sum(not expected_value and predicted_value for expected_value, predicted_value in pairs),
        false_negative=sum(expected_value and not predicted_value for expected_value, predicted_value in pairs),
        true_negative=sum(not expected_value and not predicted_value for expected_value, predicted_value in pairs),
    )


def precision(expected: Iterable[bool], predicted: Iterable[bool]) -> float:
    """Return positive predictive value, or zero when no positive was predicted."""
    counts = confusion_counts(expected, predicted)
    denominator = counts.true_positive + counts.false_positive
    return counts.true_positive / denominator if denominator else 0.0


def recall(expected: Iterable[bool], predicted: Iterable[bool]) -> float:
    """Return sensitivity, or zero when the sample has no relevant positives."""
    counts = confusion_counts(expected, predicted)
    denominator = counts.true_positive + counts.false_negative
    return counts.true_positive / denominator if denominator else 0.0
