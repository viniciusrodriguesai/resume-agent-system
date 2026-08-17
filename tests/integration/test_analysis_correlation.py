import json
import logging
import re

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.infrastructure.correlation import current_correlation_id
from resume_ai.infrastructure.telemetry import JsonLogFormatter
from resume_ai.settings import Settings


def test_direct_analysis_generates_and_cleans_correlation_context(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
    )
    service = ResumeAnalysisService(settings)
    records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = CaptureHandler()
    service.telemetry.logger.addHandler(handler)
    try:
        service.analyze(
            AnalysisRequest(
                resume_text="Candidate with Python and SQL project experience.",
                job_text="Data role requiring Python and SQL experience.",
            )
        )
    finally:
        service.telemetry.logger.removeHandler(handler)

    completed = next(record for record in records if record.getMessage() == "analysis_completed")
    payload = json.loads(JsonLogFormatter().format(completed))

    assert re.fullmatch(r"[0-9a-f]{32}", payload["correlation_id"])
    assert current_correlation_id() is None
