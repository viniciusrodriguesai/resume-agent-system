import re

import pytest

from resume_ai.infrastructure.correlation import (
    correlation_scope,
    current_correlation_id,
    normalize_correlation_id,
)


def test_correlation_scope_preserves_bounded_caller_id() -> None:
    assert current_correlation_id() is None

    with correlation_scope("request-123") as correlation_id:
        assert correlation_id == "request-123"
        assert current_correlation_id() == "request-123"

    assert current_correlation_id() is None


@pytest.mark.parametrize(
    "candidate",
    [
        "candidate@example.invalid",
        "request\nforged=true",
        "x" * 65,
        "contains spaces",
        "",
        None,
    ],
)
def test_invalid_correlation_id_is_replaced(candidate: str | None) -> None:
    generated = normalize_correlation_id(candidate)

    assert re.fullmatch(r"[0-9a-f]{32}", generated)
    assert generated != candidate


def test_nested_scope_restores_previous_identifier() -> None:
    with correlation_scope("outer"):
        with correlation_scope("inner"):
            assert current_correlation_id() == "inner"
        assert current_correlation_id() == "outer"

    assert current_correlation_id() is None


def test_scope_resets_identifier_after_exception() -> None:
    with pytest.raises(RuntimeError, match="expected"), correlation_scope("request-123"):
        raise RuntimeError("expected")

    assert current_correlation_id() is None
