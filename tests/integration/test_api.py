import re

from fastapi.testclient import TestClient

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
