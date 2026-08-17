import pytest

from evaluation.metrics.ranking import mean_reciprocal_rank, precision_at_k, recall_at_k, reciprocal_rank


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


def test_recall_at_k_measures_relevant_item_coverage() -> None:
    assert recall_at_k(["first", "noise", "second"], {"first", "second"}, 2) == 0.5


def test_recall_at_k_is_zero_without_relevance_judgments() -> None:
    assert recall_at_k(["candidate"], set(), 1) == 0.0


def test_reciprocal_rank_uses_first_relevant_position() -> None:
    assert reciprocal_rank(["noise", "relevant", "later"], {"relevant", "later"}) == 0.5


def test_reciprocal_rank_is_zero_without_hit() -> None:
    assert reciprocal_rank(["noise"], {"missing"}) == 0.0


def test_mean_reciprocal_rank_averages_cases() -> None:
    assert mean_reciprocal_rank([["noise", "hit"], ["hit"]], [{"hit"}, {"hit"}]) == 0.75


def test_mean_reciprocal_rank_rejects_mismatched_case_counts() -> None:
    with pytest.raises(ValueError, match="same length"):
        mean_reciprocal_rank([["candidate"]], [])
