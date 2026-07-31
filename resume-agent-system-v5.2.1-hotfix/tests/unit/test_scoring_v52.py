from resume_ai.domain.models import EvidenceMatch, Requirement
from resume_ai.domain.scoring import calculate_score


def build_matches(matched: int, partial: int, missing: int):
    values = [0.90] * matched + [0.50] * partial + [0.10] * missing
    return [
        EvidenceMatch(
            requirement=Requirement(id=str(index), text=f"Requisito {index}", priority="desired"),
            final_score=value,
        )
        for index, value in enumerate(values)
    ]


def test_v52_uses_five_compatibility_levels():
    cases = [
        (build_matches(0, 4, 6), "baixa"),
        (build_matches(3, 3, 4), "moderada"),
        (build_matches(5, 3, 2), "boa"),
        (build_matches(7, 2, 1), "alta"),
        (build_matches(9, 1, 0), "excelente"),
    ]
    for matches, expected in cases:
        assert calculate_score(matches, "equilibrado").level == expected


def test_v52_separates_required_and_desired_missing():
    result = calculate_score([
        EvidenceMatch(
            requirement=Requirement(id="1", text="Python", priority="required"),
            final_score=0.90,
        ),
        EvidenceMatch(
            requirement=Requirement(id="2", text="Docker", priority="desired"),
            final_score=0.10,
        ),
    ], "equilibrado")
    assert result.required_missing == 0
    assert result.desired_missing == 1
