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
