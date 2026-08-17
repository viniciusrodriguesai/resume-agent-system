import pytest
from pydantic import ValidationError

from resume_ai.domain.models import AgentResult, AgentTrace


def test_agent_result_preserves_legacy_trace_fields() -> None:
    result = AgentResult(
        agent="Agente de Teste",
        summary="Etapa concluída.",
        confidence=0.8,
        evidence=["requirement:python"],
        metadata={"items": 1},
    )

    assert isinstance(result, AgentTrace)
    assert result.agent_name == "Agente de Teste"
    assert result.status == "success"
    assert result.warnings == []
    assert result.model_dump()["agent"] == "Agente de Teste"


def test_agent_result_accepts_legacy_cached_payload_without_new_fields() -> None:
    result = AgentTrace.model_validate(
        {"agent": "Agente Legado", "summary": "Resultado em cache.", "alerts": []}
    )

    assert result.status == "success"
    assert result.evidence == []


def test_agent_result_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            agent="Agente de Teste",
            summary="Inválido.",
            status="unknown",  # type: ignore[arg-type]
        )
