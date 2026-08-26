import pytest

from resume_ai.domain.models import EvidenceMatch, Requirement
from resume_ai.domain.scoring import calculate_score


def test_required_missing_caps_score():
    matches = [
        EvidenceMatch(requirement=Requirement(id="1", text="Python", priority="required"), final_score=0.9),
        EvidenceMatch(requirement=Requirement(id="2", text="Docker", priority="required"), final_score=0.1),
    ]
    score = calculate_score(matches, "equilibrado")
    assert score.required_missing == 1
    assert score.overall_score <= 55


def make_match(
    identifier: str,
    final_score: float,
    *,
    priority: str = "neutral",
    category: str = "other",
) -> EvidenceMatch:
    return EvidenceMatch(
        requirement=Requirement(
            id=identifier,
            text=f"Requirement {identifier}",
            priority=priority,
            category=category,
        ),
        final_score=final_score,
    )


@pytest.mark.parametrize("strictness", ["flexível", "equilibrado", "conservador"])
@pytest.mark.parametrize(
    "matches",
    [
        [],
        [make_match("missing", 0.0, priority="required")],
        [make_match("partial", 0.5, priority="desired")],
        [make_match("matched", 1.0, priority="neutral")],
        [
            make_match("required", 0.9, priority="required", category="backend"),
            make_match("desired", 0.4, priority="desired", category="backend"),
            make_match("neutral", 0.1, category="tooling"),
        ],
    ],
)
def test_score_summary_invariants(
    strictness: str,
    matches: list[EvidenceMatch],
) -> None:
    result = calculate_score(matches, strictness)

    assert 0 <= result.overall_score <= 100
    assert result.matched + result.partial + result.missing == len(matches)
    assert all(0 <= category.score <= 100 for category in result.categories)
    assert all(
        category.matched + category.partial + category.missing > 0
        for category in result.categories
    )


def test_stricter_modes_cannot_increase_score() -> None:
    evidence_scores = [0.72, 0.65, 0.50, 0.40, 0.30, 0.10]

    scores = [
        calculate_score(
            [make_match(str(index), value) for index, value in enumerate(evidence_scores)],
            strictness,
        ).overall_score
        for strictness in ("flexível", "equilibrado", "conservador")
    ]

    assert scores == sorted(scores, reverse=True)


def test_weaker_evidence_cannot_produce_a_higher_score() -> None:
    evidence_scores = [0.2, 0.4, 0.6, 0.8]
    scores = [
        calculate_score([make_match(str(index), value)], "equilibrado").overall_score
        for index, value in enumerate(evidence_scores)
    ]

    assert scores == sorted(scores)


def test_missing_required_evidence_cannot_improve_an_existing_score() -> None:
    desired_matches = [
        make_match("desired-1", 0.9, priority="desired"),
        make_match("desired-2", 0.9, priority="desired"),
    ]
    baseline = calculate_score(desired_matches, "equilibrado")
    with_required_gap = calculate_score(
        [
            make_match("desired-1", 0.9, priority="desired"),
            make_match("desired-2", 0.9, priority="desired"),
            make_match("required-gap", 0.0, priority="required"),
        ],
        "equilibrado",
    )

    assert with_required_gap.overall_score <= baseline.overall_score
    assert with_required_gap.required_missing == 1


def test_zero_requirements_has_consistent_empty_summary() -> None:
    result = calculate_score([], "equilibrado")

    assert result.overall_score == 0
    assert result.matched == result.partial == result.missing == 0
    assert result.required_missing == 0
    assert result.categories == []


def test_all_missing_and_all_matched_keep_exact_boundary_scores() -> None:
    missing = calculate_score(
        [make_match(str(index), 0.0, priority="required") for index in range(3)],
        "equilibrado",
    )
    matched = calculate_score(
        [make_match(str(index), 1.0, priority="required") for index in range(3)],
        "equilibrado",
    )

    assert missing.overall_score == 0
    assert missing.missing == missing.required_missing == 3
    assert matched.overall_score == 100
    assert matched.matched == 3
    assert matched.required_missing == 0


def test_repeating_the_same_requirement_does_not_change_its_score() -> None:
    original = [make_match("python", 0.5, priority="required", category="backend")]
    repeated = [
        make_match("python-1", 0.5, priority="required", category="backend"),
        make_match("python-2", 0.5, priority="required", category="backend"),
    ]

    original_score = calculate_score(original, "equilibrado")
    repeated_score = calculate_score(repeated, "equilibrado")

    assert repeated_score.overall_score == original_score.overall_score
    assert repeated_score.categories[0].score == original_score.categories[0].score
