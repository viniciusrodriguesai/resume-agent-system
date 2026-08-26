import re

from fastapi.testclient import TestClient

from api import main as api_main
from api.main import app, settings


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_reports_ready_service() -> None:
    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["profile"] == settings.profile


def test_profiles_endpoint_describes_supported_torch_backends() -> None:
    response = TestClient(app).get("/v1/profiles")

    assert response.status_code == 200
    profiles = response.json()["profiles"]
    assert "Torch" in profiles["demo"]
    assert "Torch" in profiles["balanced"]
    assert "ONNX" not in str(profiles)


def test_readiness_failure_returns_safe_service_unavailable(monkeypatch) -> None:
    internal_detail = "model path C:/private/candidate@example.invalid"

    def fail_service_initialization(_profile: str) -> None:
        raise RuntimeError(internal_detail)

    monkeypatch.setattr(api_main, "service_for", fail_service_initialization)
    response = TestClient(app).get(
        "/ready",
        headers={"X-Request-ID": "readiness-failure"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "service_unavailable",
            "message": "Serviço temporariamente indisponível.",
            "request_id": "readiness-failure",
        }
    }
    assert internal_detail not in response.text


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


def test_api_adds_defensive_response_headers() -> None:
    response = TestClient(app).get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), geolocation=(), microphone=()"
    )


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
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {
        "error": {
            "code": "payload_too_large",
            "message": "Payload acima do limite permitido.",
            "request_id": "oversized-request",
        }
    }


def test_guard_rejects_body_larger_than_declared_content_length() -> None:
    oversized_body = b"x" * (settings.api_max_body_mb * 1024 * 1024 + 1)
    response = TestClient(app).post(
        "/v1/analyze",
        content=oversized_body,
        headers={
            "Content-Length": "1",
            "Content-Type": "application/json",
            "X-Request-ID": "deceptive-length",
        },
    )

    assert response.status_code == 413
    assert response.json()["error"] == {
        "code": "payload_too_large",
        "message": "Payload acima do limite permitido.",
        "request_id": "deceptive-length",
    }


def test_guard_rejects_negative_content_length() -> None:
    response = TestClient(app).post(
        "/v1/analyze",
        content=b"{}",
        headers={
            "Content-Length": "-1",
            "Content-Type": "application/json",
            "X-Request-ID": "negative-length",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "invalid_content_length",
        "message": "Cabeçalho Content-Length inválido.",
        "request_id": "negative-length",
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


def test_unexpected_exception_returns_safe_internal_error(monkeypatch) -> None:
    internal_detail = "C:/private/resumes candidate.private@example.invalid"

    class CrashingService:
        def analyze(self, _request: object) -> None:
            raise RuntimeError(internal_detail)

    monkeypatch.setattr(api_main, "service_for", lambda _profile: CrashingService())
    response = TestClient(app, raise_server_exceptions=False).post(
        "/v1/analyze",
        json={
            "resume_text": "Python engineer with production experience",
            "job_text": "Hiring a Python engineer for production systems",
        },
        headers={"X-Request-ID": "unexpected-failure"},
    )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "unexpected-failure"
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Erro interno ao processar a requisição.",
            "request_id": "unexpected-failure",
        }
    }
    assert internal_detail not in response.text


def test_cors_exposes_request_id_to_allowed_origin() -> None:
    allowed_origin = settings.cors_origins.split(",")[0]

    response = TestClient(app).get(
        "/health",
        headers={"Origin": allowed_origin},
    )

    exposed_headers = response.headers["Access-Control-Expose-Headers"]
    assert "X-Request-ID" in exposed_headers
    assert response.headers["Access-Control-Allow-Origin"] == allowed_origin


def test_cors_preflight_allows_request_id_for_analysis() -> None:
    allowed_origin = settings.cors_origins.split(",")[0]

    response = TestClient(app).options(
        "/v1/analyze",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "Content-Type, X-API-Key, X-Request-ID"
            ),
        },
    )

    assert response.status_code == 200
    allowed_headers = response.headers["Access-Control-Allow-Headers"].lower()
    assert "x-request-id" in allowed_headers


def test_not_found_and_method_not_allowed_use_correlated_error_contract() -> None:
    client = TestClient(app)
    missing = client.get("/does-not-exist", headers={"X-Request-ID": "missing-route"})
    wrong_method = client.put("/health", headers={"X-Request-ID": "wrong-method"})

    assert missing.status_code == 404
    assert missing.json()["error"]["request_id"] == "missing-route"
    assert wrong_method.status_code == 405
    assert wrong_method.json()["error"]["request_id"] == "wrong-method"
