import pytest
from pydantic import ValidationError

from evaluation.schema import AnalysisCase, RetrievalCase


def valid_case() -> dict[str, object]:
    return {
        "case_id": "python-ranking",
        "query": "Experiência com Python",
        "candidates": [
            {"candidate_id": "relevant", "text": "Criei APIs em Python."},
            {"candidate_id": "distractor", "text": "Desenhei interfaces no Figma."},
        ],
        "relevant_candidate_ids": ["relevant"],
        "data_origin": "synthetic",
    }


def test_accepts_consistent_synthetic_retrieval_case() -> None:
    case = RetrievalCase.model_validate(valid_case())

    assert case.data_origin == "synthetic"
    assert case.relevant_candidate_ids == ["relevant"]


def test_rejects_unknown_relevance_reference() -> None:
    payload = valid_case()
    payload["relevant_candidate_ids"] = ["not-present"]

    with pytest.raises(ValidationError, match="unknown candidates"):
        RetrievalCase.model_validate(payload)


def test_rejects_duplicate_candidate_identifiers() -> None:
    payload = valid_case()
    payload["candidates"] = [
        {"candidate_id": "duplicate", "text": "Primeiro trecho."},
        {"candidate_id": "duplicate", "text": "Segundo trecho."},
    ]
    payload["relevant_candidate_ids"] = ["duplicate"]

    with pytest.raises(ValidationError, match="must be unique"):
        RetrievalCase.model_validate(payload)


def test_rejects_unexpected_fields() -> None:
    payload = valid_case()
    payload["candidate_email"] = "should-not-be-part-of-the-contract@example.invalid"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RetrievalCase.model_validate(payload)


def test_accepts_synthetic_full_pipeline_case() -> None:
    case = AnalysisCase(
        case_id="pipeline-python",
        resume_text="Python usado em projetos de APIs.",
        job_text="REQUISITOS OBRIGATÓRIOS\n- Python",
        expected_status_by_requirement={"Python": "matched"},
    )

    assert case.strictness == "equilibrado"
    assert case.data_origin == "synthetic"


def test_rejects_unknown_pipeline_status_label() -> None:
    with pytest.raises(ValidationError):
        AnalysisCase(
            case_id="invalid-label",
            resume_text="Python usado em projetos de APIs.",
            job_text="REQUISITOS OBRIGATÓRIOS\n- Python",
            expected_status_by_requirement={"Python": "excellent"},  # type: ignore[dict-item]
        )
