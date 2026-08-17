from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_CORRELATION_ID = ContextVar[str | None]("resume_ai_correlation_id", default=None)
_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def normalize_correlation_id(candidate: str | None) -> str:
    """Preserve a bounded caller ID or generate an opaque local identifier."""

    if candidate and _CORRELATION_ID_PATTERN.fullmatch(candidate):
        return candidate
    return uuid.uuid4().hex


def current_correlation_id() -> str | None:
    return _CORRELATION_ID.get()


@contextmanager
def correlation_scope(candidate: str | None = None) -> Iterator[str]:
    correlation_id = normalize_correlation_id(candidate)
    token = _CORRELATION_ID.set(correlation_id)
    try:
        yield correlation_id
    finally:
        _CORRELATION_ID.reset(token)
