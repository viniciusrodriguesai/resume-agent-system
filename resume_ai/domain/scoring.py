from __future__ import annotations

from collections import defaultdict

from .models import CategoryScore, EvidenceMatch, ScoreSummary

PRIORITY_WEIGHTS = {"required": 1.0, "desired": 0.45, "neutral": 0.2}
STATUS_VALUES = {"matched": 1.0, "partial": 0.55, "missing": 0.0}
THRESHOLDS = {
    "flexível": {"matched": 0.50, "partial": 0.28},
    "equilibrado": {"matched": 0.60, "partial": 0.35},
    "conservador": {"matched": 0.70, "partial": 0.43},
}


def classify(score: float, strictness: str) -> str:
    limits = THRESHOLDS.get(strictness, THRESHOLDS["equilibrado"])
    if score >= limits["matched"]:
        return "matched"
    if score >= limits["partial"]:
        return "partial"
    return "missing"


def calculate_score(matches: list[EvidenceMatch], strictness: str) -> ScoreSummary:
    totals: dict[str, float] = defaultdict(float)
    gains: dict[str, float] = defaultdict(float)
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total = 0.0
    gain = 0.0
    required = 0
    required_missing = 0
    desired_missing = 0
    neutral_missing = 0

    for match in matches:
        match.status = classify(match.final_score, strictness)  # type: ignore[assignment]
        weight = PRIORITY_WEIGHTS[match.requirement.priority]
        value = STATUS_VALUES[match.status]
        category = match.requirement.category
        total += weight
        gain += weight * value
        totals[category] += weight
        gains[category] += weight * value
        counts[category][match.status] += 1
        if match.requirement.priority == "required":
            required += 1
            if match.status == "missing":
                required_missing += 1
        elif match.requirement.priority == "desired" and match.status == "missing":
            desired_missing += 1
        elif match.requirement.priority == "neutral" and match.status == "missing":
            neutral_missing += 1

    overall = round(100 * gain / total) if total else 0
    if required:
        ratio = required_missing / required
        if ratio >= 0.5:
            overall = min(overall, 55)
        elif ratio >= 0.25:
            overall = min(overall, 72)

    categories = []
    for category, total_weight in totals.items():
        categories.append(CategoryScore(
            category=category,
            score=round(100 * gains[category] / total_weight) if total_weight else 0,
            matched=counts[category]["matched"],
            partial=counts[category]["partial"],
            missing=counts[category]["missing"],
        ))
    categories.sort(key=lambda item: item.score, reverse=True)

    matched = sum(m.status == "matched" for m in matches)
    partial = sum(m.status == "partial" for m in matches)
    missing = sum(m.status == "missing" for m in matches)
    if overall >= 90:
        level = "excelente"
    elif overall >= 75:
        level = "alta"
    elif overall >= 60:
        level = "boa"
    elif overall >= 40:
        level = "moderada"
    else:
        level = "baixa"

    explanation = [
        "A nota usa pesos diferentes: obrigatório 1,00; desejável 0,45; neutro 0,20.",
        f"Foram encontrados {matched} requisitos atendidos, {partial} parciais e {missing} ausentes.",
    ]
    if required_missing:
        explanation.append(
            f"A nota foi limitada porque {required_missing} requisito(s) obrigatório(s) não tiveram evidência suficiente."
        )

    return ScoreSummary(
        overall_score=overall,
        level=level,  # type: ignore[arg-type]
        matched=matched,
        partial=partial,
        missing=missing,
        required_missing=required_missing,
        desired_missing=desired_missing,
        neutral_missing=neutral_missing,
        categories=categories,
        thresholds=THRESHOLDS.get(strictness, THRESHOLDS["equilibrado"]),
        explanation=explanation,
    )
