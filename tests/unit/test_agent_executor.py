import pytest

from resume_ai.agents.base import AgentExecutionError, run_agent


def test_executor_collects_warning_evidence_and_metadata() -> None:
    value, result = run_agent(
        "Agente de Teste",
        lambda: ["item"],
        lambda output: f"{len(output)} item processado.",
        warnings=lambda _: ["fallback-used"],
        evidence=lambda _: ["requirement:test"],
        metadata=lambda output: {"item_count": len(output)},
    )

    assert value == ["item"]
    assert result.status == "warning"
    assert result.warnings == ["fallback-used"]
    assert result.evidence == ["requirement:test"]
    assert result.metadata == {"item_count": 1}


def test_executor_failure_result_does_not_copy_exception_message() -> None:
    def fail() -> None:
        raise ValueError("candidate-email@example.invalid")

    with pytest.raises(AgentExecutionError) as captured:
        run_agent("Agente de Teste", fail, lambda _: "unreachable")

    assert captured.value.result.status == "error"
    assert captured.value.result.metadata == {"exception_type": "ValueError"}
    assert "candidate-email" not in captured.value.result.model_dump_json()
    assert isinstance(captured.value.__cause__, ValueError)
