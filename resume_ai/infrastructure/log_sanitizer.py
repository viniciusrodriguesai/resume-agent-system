from __future__ import annotations

import re
from collections.abc import Mapping

SAFE_LOG_FIELDS = frozenset(
    {
        "agent",
        "analysis_id",
        "backend",
        "cache_hit",
        "confidence",
        "correlation_id",
        "duration_ms",
        "error_type",
        "evidence_count",
        "memory_mb",
        "profile",
        "request_id",
        "score",
        "stage",
        "status",
        "warning_count",
    }
)

_EMAIL_PATTERN = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)")
_EVENT_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_MAX_LOG_STRING_LENGTH = 128
_REDACTED = "[REDACTED]"


def _sanitize_scalar(value: object) -> str | int | float | bool | None:
    if value is None or isinstance(value, bool | int | float):
        return value
    if not isinstance(value, str):
        return _REDACTED
    if len(value) > _MAX_LOG_STRING_LENGTH:
        return _REDACTED
    if _EMAIL_PATTERN.search(value) or _PHONE_PATTERN.search(value):
        return _REDACTED
    return value.replace("\r", " ").replace("\n", " ")


def sanitize_log_fields(fields: Mapping[str, object]) -> dict[str, str | int | float | bool | None]:
    """Return only bounded operational fields that are safe to serialize in logs."""

    return {
        key: _sanitize_scalar(value)
        for key, value in fields.items()
        if key in SAFE_LOG_FIELDS
    }


def sanitize_log_event(event: str) -> str:
    """Accept only bounded technical event names, never user-controlled messages."""

    return event if _EVENT_PATTERN.fullmatch(event) else "invalid_event"
