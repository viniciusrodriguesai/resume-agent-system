from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings


def test_report_trace_contains_only_technical_evidence(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
    )
    service = ResumeAnalysisService(settings)

    result = service.analyze(
        AnalysisRequest(
            resume_text="Private Candidate private@example.invalid uses Python and SQL.",
            job_text="Confidential Data Role requires Python, SQL, and Docker.",
        )
    )

    trace = result.traces[-1]
    serialized_trace = trace.model_dump_json()

    assert trace.agent_name == "Agente de Relatório"
    assert trace.status == "success"
    assert trace.metadata == {
        "match_count": len(result.matches),
        "recommendation_count": len(result.recommendations),
        "output_format_count": 3,
    }
    assert all(item.startswith("requirement-id:") for item in trace.evidence)
    assert result.job.title not in serialized_trace
    assert "private@example.invalid" not in serialized_trace
    assert "Confidential Data Role" not in serialized_trace
