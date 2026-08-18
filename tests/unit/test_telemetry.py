import json
import logging

from resume_ai.infrastructure.correlation import correlation_scope
from resume_ai.infrastructure.telemetry import JsonLogFormatter, Telemetry
from resume_ai.settings import Settings


def test_json_formatter_emits_only_bounded_operational_fields() -> None:
    record = logging.LogRecord(
        name="resume_ai",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="analysis_completed",
        args=(),
        exc_info=None,
    )
    record.telemetry_fields = {
        "analysis_id": "analysis-123",
        "duration_ms": 14.5,
        "resume_text": "Private Candidate private@example.invalid",
        "job_text": "Confidential role",
    }

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["event"] == "analysis_completed"
    assert payload["analysis_id"] == "analysis-123"
    assert payload["duration_ms"] == 14.5
    assert payload["level"] == "info"
    assert payload["logger"] == "resume_ai"
    assert "timestamp" in payload
    assert "resume_text" not in payload
    assert "job_text" not in payload
    assert "private@example.invalid" not in json.dumps(payload)


def test_json_formatter_rejects_unsafe_event_name() -> None:
    record = logging.LogRecord(
        name="resume_ai",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="Private Candidate\nforged=true",
        args=(),
        exc_info=None,
    )

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["event"] == "invalid_event"
    assert "Private Candidate" not in json.dumps(payload)


def test_telemetry_installs_one_json_handler(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )

    first = Telemetry(settings)
    second = Telemetry(settings)
    json_handlers = [
        handler
        for handler in first.logger.handlers
        if isinstance(handler.formatter, JsonLogFormatter)
    ]

    assert first.logger is second.logger
    assert len(json_handlers) == 1


def test_telemetry_attaches_active_correlation_id(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    telemetry = Telemetry(settings)
    records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = CaptureHandler()
    telemetry.logger.addHandler(handler)
    try:
        with correlation_scope("request-123"):
            telemetry.info(
                "analysis_started",
                correlation_id="spoofed",
                profile="demo",
                resume_text="Private Candidate",
            )
    finally:
        telemetry.logger.removeHandler(handler)

    payload = json.loads(JsonLogFormatter().format(records[-1]))
    assert payload["correlation_id"] == "request-123"
    assert payload["profile"] == "demo"
    assert "resume_text" not in payload
    assert "Private Candidate" not in json.dumps(payload)


def test_error_telemetry_drops_uncontrolled_exception_details(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
    )
    telemetry = Telemetry(settings)
    records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = CaptureHandler()
    telemetry.logger.addHandler(handler)
    try:
        with correlation_scope("request-error"):
            telemetry.error(
                "api_unhandled_error",
                error_type="RuntimeError",
                exception_message="Private Candidate private@example.invalid",
            )
    finally:
        telemetry.logger.removeHandler(handler)

    payload = json.loads(JsonLogFormatter().format(records[-1]))
    assert payload["level"] == "error"
    assert payload["event"] == "api_unhandled_error"
    assert payload["error_type"] == "RuntimeError"
    assert payload["correlation_id"] == "request-error"
    assert "exception_message" not in payload
    assert "private@example.invalid" not in json.dumps(payload)
