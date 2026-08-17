import pytest

from evaluation.metrics.classification import precision


def test_precision_measures_predicted_positive_quality() -> None:
    assert precision([True, False, True], [True, True, False]) == 0.5


def test_precision_is_zero_without_positive_predictions() -> None:
    assert precision([True, False], [False, False]) == 0.0


def test_precision_rejects_mismatched_sequences() -> None:
    with pytest.raises(ValueError, match="same length"):
        precision([True], [True, False])
