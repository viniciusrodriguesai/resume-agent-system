from __future__ import annotations

import json
from typing import Dict, List

def build_recommendations(
    scoring: Dict[str, object],
    resume_profile: Dict[str, object],
) -> List[Dict[str, str]]:
    recommendations: List[Dict[str, str]] = []
    evidence = scoring.get("evidence", []) or []

    for item in evidence:
        if item.get("priority") == "required" and item.get("status") == "missing":
            recommendations.append(
                {
                    "priority": "High",
                    "type": "Required gap",
                    "action": (
                        f"Develop truthful evidence for '{item.get('label')}'. "
                        "Do not add it to the resume before gaining the skill or experience."
                    ),
                }
            )
        elif item.get("priority") == "required" and item.get("status") == "partial":
            recommendations.append(
                {
                    "priority": "High",
                    "type": "Evidence quality",
                    "action": (
                        f"Strengthen the resume bullet related to '{item.get('label')}' "
                        "with an action, technology, scope, and measurable result."
                    ),
                }
            )
        elif item.get("priority") == "desirable" and item.get("status") == "missing":
            recommendations.append(
                {
                    "priority": "Medium",
                    "type": "Development",
                    "action": f"Consider studying or practicing '{item.get('label')}'.",
                }
            )

    if not resume_profile.get("quantified_evidence"):
        recommendations.append(
            {
                "priority": "Medium",
                "type": "Impact",
                "action": (
                    "Add measurable outcomes where truthful, such as time saved, "
                    "records processed, accuracy, or users supported."
                ),
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "priority": "Low",
                "type": "Tailoring",
                "action": (
                    "Tailor the professional summary and project bullets to the role "
                    "without inventing experience."
                ),
            }
        )

    unique = []
    seen = set()
    for item in recommendations:
        key = item["action"]
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:12]


def build_reports(state: Dict[str, object]) -> Dict[str, str]:
    scoring = state.get("scoring", {}) or {}
    job = state.get("job_profile", {}) or {}
    review = state.get("review", {}) or {}
    recommendations = state.get("recommendations", []) or []

    lines = [
        "# Explainable Multi-Agent Resume Analysis",
        "",
        f"**Analysis ID:** {state.get('analysis_id', '')}",
        f"**Target role:** {job.get('title', 'Unknown')}",
        f"**Overall score:** {scoring.get('overall_score', 0)}%",
        f"**Level:** {str(scoring.get('level', 'low')).title()}",
        f"**Review decision:** {review.get('decision', 'unknown')}",
        "",
        "## Category scores",
        "",
    ]

    for category, score in (scoring.get("category_scores", {}) or {}).items():
        lines.append(f"- **{category}:** {score}%")

    lines.extend(["", "## Requirement evidence", ""])
    for item in scoring.get("evidence", []) or []:
        lines.extend(
            [
                f"### {item.get('label')}",
                f"- Priority: {item.get('priority')}",
                f"- Status: {item.get('status')}",
                f"- Final score: {float(item.get('final_score', 0)):.3f}",
                f"- Evidence: {item.get('best_evidence') or 'No evidence identified.'}",
                f"- Engine: {item.get('engine', 'unknown')}",
                "",
            ]
        )

    lines.extend(["## Recommendations", ""])
    for item in recommendations:
        lines.append(
            f"- **{item.get('priority')} — {item.get('type')}:** {item.get('action')}"
        )

    lines.extend(
        [
            "",
            "## Review",
            "",
            str(review.get("summary", "")),
            "",
            "> This system supports human evaluation. It must not be the sole basis "
            "for hiring or rejection decisions.",
        ]
    )

    return {
        "markdown": "\n".join(lines),
        "json": json.dumps(state, ensure_ascii=False, indent=2),
    }
