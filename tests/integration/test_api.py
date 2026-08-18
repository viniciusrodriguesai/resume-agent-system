import re

from fastapi.testclient import TestClient

from api import main as api_main
from api.main import app, settings


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_preserves_valid_request_id() -> None:
    response = TestClient(app).get(
        "/health",
        headers={"X-Request-ID": "request-123"},
    )

    assert response.headers["X-Request-ID"] == "request-123"


def test_api_replaces_unsafe_request_id() -> None:
    response = TestClient(app).get(
        "/health",
        headers={"X-Request-ID": "private@example.invalid"},
    )

    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])


def test_guard_rejection_includes_request_id() -> None:
    response = TestClient(app).post(
        "/v1/analyze",
        headers={
            "Content-Length": str(settings.api_max_body_mb * 1024 * 1024 + 1),
            "X-Request-ID": "oversized-request",
        },
    )

    assert response.status_code == 413
    assert response.headers["X-Request-ID"] == "oversized-request"
    assert response.json() == {
        "error": {
            "code": "payload_too_large",
            "message": "Payload acima do limite permitido.",
            "request_id": "oversized-request",
        }
    }


def test_validation_error_does_not_echo_submitted_personal_data() -> None:
    personal_value = "candidate.private@example.invalid"
    response = TestClient(app).post(
        "/v1/analyze",
        json={
            "resume_text": personal_value,
            "job_text": "short",
        },
        headers={"X-Request-ID": "invalid-payload"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Payload inválido ou fora dos limites permitidos.",
            "request_id": "invalid-payload",
        }
    }
    assert personal_value not in response.text


def test_http_exception_does_not_echo_service_failure_detail(monkeypatch) -> None:
    personal_value = "candidate.private@example.invalid"

    class FailingService:
        def analyze(self, _request: object) -> None:
            raise ValueError(personal_value)

    monkeypatch.setattr(api_main, "service_for", lambda _profile: FailingService())
    response = TestClient(app).post(
        "/v1/analyze",
        json={
            "resume_text": "Python engineer with production experience",
            "job_text": "Hiring a Python engineer for production systems",
        },
        headers={"X-Request-ID": "service-failure"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "unprocessable_request",
            "message": "Não foi possível processar o payload.",
            "request_id": "service-failure",
        }
    }
    assert personal_value not in response.text


def test_cors_exposes_request_id_to_allowed_origin() -> None:
    allowed_origin = settings.cors_origins.split(",")[0]

    response = TestClient(app).get(
        "/health",
        headers={"Origin": allowed_origin},
    )

    exposed_headers = response.headers["Access-Control-Expose-Headers"]
    assert "X-Request-ID" in exposed_headers
    assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
