import json
import logging

import pytest

from resume_ai.agents.base import AgentExecutionError
from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.infrastructure.correlation import current_correlation_id
from resume_ai.infrastructure.observability import METRICS
from resume_ai.infrastructure.telemetry import JsonLogFormatter
from resume_ai.settings import Settings


def test_agent_failure_emits_sanitized_stage_diagnostics(tmp_path, monkeypatch) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        history_enabled=False,
    )
    service = ResumeAnalysisService(settings)
    records: list[logging.LogRecord] = []
    failed_profiles: list[str] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    def fail_with_sensitive_message(_text: str) -> None:
        raise ValueError("private@example.invalid at C:\\private\\resume.txt")

    handler = CaptureHandler()
    service.telemetry.logger.addHandler(handler)
    monkeypatch.setattr(service.privacy_agent.service, "anonymize", fail_with_sensitive_message)
    monkeypatch.setattr(METRICS, "record_failure", failed_profiles.append)
    try:
        with pytest.raises(AgentExecutionError):
            service.analyze(
                AnalysisRequest(
                    resume_text="Candidate with Python and SQL experience.",
                    job_text="Data role requiring Python and SQL.",
                )
            )
    finally:
        service.telemetry.logger.removeHandler(handler)

    failure_payloads = [
        json.loads(JsonLogFormatter().format(record))
        for record in records
        if record.getMessage() in {"agent_failed", "analysis_failed"}
    ]
    serialized_logs = json.dumps(failure_payloads)

    assert [payload["event"] for payload in failure_payloads] == [
        "agent_failed",
        "analysis_failed",
    ]
    assert all(payload["stage"] == "privacy" for payload in failure_payloads)
    assert failure_payloads[-1]["error_type"] == "ValueError"
    assert failed_profiles == ["demo"]
    assert "private@example.invalid" not in serialized_logs
    assert "resume.txt" not in serialized_logs
    assert current_correlation_id() is None
