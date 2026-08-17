from __future__ import annotations

from collections.abc import Collection, Sequence


def _validate_ranking(ranked_ids: Sequence[str], k: int) -> None:
    if k <= 0:
        raise ValueError("k must be greater than zero")
    if len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError("ranked_ids must not contain duplicates")


def precision_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Collection[str],
    k: int,
) -> float:
    """Measure the fraction of the first k retrieval slots that are relevant."""
    _validate_ranking(ranked_ids, k)
    relevant = set(relevant_ids)
    hits = sum(candidate_id in relevant for candidate_id in ranked_ids[:k])
    return hits / k


def recall_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Collection[str],
    k: int,
) -> float:
    """Measure the fraction of all relevant items retrieved in the first k slots."""
    _validate_ranking(ranked_ids, k)
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    hits = sum(candidate_id in relevant for candidate_id in ranked_ids[:k])
    return hits / len(relevant)
