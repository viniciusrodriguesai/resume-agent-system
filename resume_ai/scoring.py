from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

PRIORITY_WEIGHTS = {
    "required": 1.0,
    "desirable": 0.45,
    "neutral": 0.25,
}
STATUS_VALUES = {
    "matched": 1.0,
    "partial": 0.55,
    "missing": 0.0,
}

THRESHOLDS = {
    "Flexible": (0.48, 0.26),
    "Balanced": (0.57, 0.32),
    "Conservative": (0.66, 0.40),
}

def score_evidence(
    evidence: List[Dict[str, object]],
    strictness: str = "Balanced",
) -> Dict[str, object]:
    matched_threshold, partial_threshold = THRESHOLDS.get(
        strictness,
        THRESHOLDS["Balanced"],
    )

    scored = []
    total_weight = 0.0
    earned_weight = 0.0
    by_type_total = defaultdict(float)
    by_type_earned = defaultdict(float)
    missing_required = 0
    required_count = 0

    for item in evidence:
        value = float(item.get("final_score", 0.0))
        status = (
            "matched"
            if value >= matched_threshold
            else "partial"
            if value >= partial_threshold
            else "missing"
        )
        priority = str(item.get("priority", "neutral"))
        requirement_type = str(item.get("type", "general"))
        weight = PRIORITY_WEIGHTS.get(priority, 0.25)
        status_value = STATUS_VALUES[status]

        if priority == "required":
            required_count += 1
            if status == "missing":
                missing_required += 1

        total_weight += weight
        earned_weight += weight * status_value
        by_type_total[requirement_type] += weight
        by_type_earned[requirement_type] += weight * status_value

        scored.append({**item, "status": status})

    overall = round(
        100 * earned_weight / total_weight
    ) if total_weight else 0

    if required_count:
        missing_ratio = missing_required / required_count
        if missing_ratio >= 0.50:
            overall = min(overall, 55)
        elif missing_ratio >= 0.25:
            overall = min(overall, 72)

    category_scores = {
        key.title(): round(
            100 * by_type_earned[key] / total
        )
        for key, total in by_type_total.items()
        if total
    }

    level = (
        "high"
        if overall >= 82
        else "medium"
        if overall >= 62
        else "low"
    )

    return {
        "overall_score": max(0, min(overall, 100)),
        "level": level,
        "matched_threshold": matched_threshold,
        "partial_threshold": partial_threshold,
        "required_count": required_count,
        "missing_required_count": missing_required,
        "category_scores": category_scores,
        "evidence": scored,
        "matched_count": sum(i["status"] == "matched" for i in scored),
        "partial_count": sum(i["status"] == "partial" for i in scored),
        "missing_count": sum(i["status"] == "missing" for i in scored),
    }
