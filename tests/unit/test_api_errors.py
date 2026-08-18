import json
import re

import pytest
from pydantic import ValidationError

from api.errors import ApiErrorDetail, api_error_response
from resume_ai.infrastructure.correlation import correlation_scope


def test_error_response_uses_active_request_id() -> None:
    with correlation_scope("request-123"):
        response = api_error_response(422, "invalid_request", "Payload inválido.")

    assert response.status_code == 422
    assert json.loads(response.body) == {
        "error": {
            "code": "invalid_request",
            "message": "Payload inválido.",
            "request_id": "request-123",
        }
    }


def test_error_response_generates_request_id_outside_context() -> None:
    response = api_error_response(500, "internal_error", "Erro interno.")
    payload = json.loads(response.body)

    assert re.fullmatch(r"[0-9a-f]{32}", payload["error"]["request_id"])


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("Invalid Code", "Mensagem."),
        ("invalid-code", "Mensagem."),
        ("valid_code", ""),
        ("valid_code", "x" * 201),
    ],
)
def test_error_detail_rejects_values_outside_contract(code: str, message: str) -> None:
    with pytest.raises(ValidationError):
        ApiErrorDetail(code=code, message=message, request_id="request-123")
