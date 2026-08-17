from resume_ai.infrastructure.log_sanitizer import sanitize_log_event, sanitize_log_fields


def test_sanitizer_drops_sensitive_and_unknown_fields() -> None:
    sanitized = sanitize_log_fields(
        {
            "analysis_id": "analysis-123",
            "resume_text": "private resume",
            "job_text": "private vacancy",
            "candidate_name": "Private Candidate",
            "email": "private@example.invalid",
            "phone": "+55 11 99999-9999",
            "address": "Private street",
            "metadata": {"evidence": "private evidence"},
        }
    )

    assert sanitized == {"analysis_id": "analysis-123"}


def test_sanitizer_redacts_contact_values_in_allowed_fields() -> None:
    sanitized = sanitize_log_fields(
        {
            "stage": "private@example.invalid",
            "agent": "+55 (11) 99999-9999",
        }
    )

    assert sanitized == {"stage": "[REDACTED]", "agent": "[REDACTED]"}


def test_sanitizer_bounds_values_and_prevents_log_injection() -> None:
    sanitized = sanitize_log_fields(
        {
            "profile": "demo\nforged=true",
            "error_type": "x" * 129,
            "backend": {"name": "unsafe"},
            "cache_hit": True,
            "duration_ms": 12.5,
        }
    )

    assert sanitized == {
        "profile": "demo forged=true",
        "error_type": "[REDACTED]",
        "backend": "[REDACTED]",
        "cache_hit": True,
        "duration_ms": 12.5,
    }


def test_event_sanitizer_accepts_only_technical_identifiers() -> None:
    assert sanitize_log_event("analysis.completed") == "analysis.completed"
    assert sanitize_log_event("cache_miss") == "cache_miss"
    assert sanitize_log_event("Private Candidate") == "invalid_event"
    assert sanitize_log_event("analysis_completed\nforged=true") == "invalid_event"
    assert sanitize_log_event("x" * 65) == "invalid_event"
