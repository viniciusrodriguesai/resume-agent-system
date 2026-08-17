import pytest

from evaluation.metrics.ranking import precision_at_k


def test_precision_at_k_counts_relevant_slots() -> None:
    assert precision_at_k(["relevant", "noise", "also-relevant"], {"relevant", "also-relevant"}, 2) == 0.5


def test_precision_at_k_penalizes_missing_slots() -> None:
    assert precision_at_k(["relevant"], {"relevant"}, 2) == 0.5


@pytest.mark.parametrize("k", [0, -1])
def test_precision_at_k_rejects_non_positive_cutoff(k: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        precision_at_k(["candidate"], {"candidate"}, k)


def test_precision_at_k_rejects_duplicate_ranking_ids() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        precision_at_k(["same", "same"], {"same"}, 2)
