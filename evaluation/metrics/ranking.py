from __future__ import annotations

import math
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


def reciprocal_rank(
    ranked_ids: Sequence[str],
    relevant_ids: Collection[str],
) -> float:
    """Return the inverse rank of the first relevant item."""
    _validate_ranking(ranked_ids, 1)
    relevant = set(relevant_ids)
    for rank, candidate_id in enumerate(ranked_ids, start=1):
        if candidate_id in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    rankings: Sequence[Sequence[str]],
    relevance_sets: Sequence[Collection[str]],
) -> float:
    """Average reciprocal rank across retrieval cases."""
    if len(rankings) != len(relevance_sets):
        raise ValueError("rankings and relevance_sets must have the same length")
    if not rankings:
        return 0.0
    values = [
        reciprocal_rank(ranking, relevant_ids)
        for ranking, relevant_ids in zip(rankings, relevance_sets, strict=True)
    ]
    return sum(values) / len(values)


def ndcg_at_k(
    ranked_ids: Sequence[str],
    relevant_ids: Collection[str],
    k: int,
) -> float:
    """Measure position-discounted binary relevance normalized by the ideal order."""
    _validate_ranking(ranked_ids, k)
    relevant = set(relevant_ids)
    ideal_hits = min(len(relevant), k)
    if ideal_hits == 0:
        return 0.0

    discounted_gain = sum(
        1.0 / math.log2(rank + 1)
        for rank, candidate_id in enumerate(ranked_ids[:k], start=1)
        if candidate_id in relevant
    )
    ideal_gain = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return discounted_gain / ideal_gain
