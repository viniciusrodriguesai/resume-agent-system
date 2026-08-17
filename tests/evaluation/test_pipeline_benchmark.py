import pytest

from evaluation.benchmarks.pipeline import run_pipeline_benchmark
from evaluation.schema import AnalysisCase
from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.settings import Settings


def service_for_benchmark(tmp_path, *, cache_enabled: bool = False) -> ResumeAnalysisService:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=False,
        history_enabled=False,
        cache_enabled=cache_enabled,
    )
    return ResumeAnalysisService(settings)


def pipeline_case() -> AnalysisCase:
    return AnalysisCase(
        case_id="python",
        resume_text="PERFIL TÉCNICO\nDesenvolvi serviços em Python.",
        job_text="Analista\nREQUISITOS OBRIGATÓRIOS\n- Python",
        expected_status_by_requirement={"Python": "matched"},
    )


def test_pipeline_runner_measures_complete_agent_flow(tmp_path) -> None:
    result = run_pipeline_benchmark(
        [pipeline_case()],
        service_for_benchmark(tmp_path),
        runs=1,
    )

    assert result.metrics["accuracy"] == 1.0
    assert result.performance.runs == 1
    assert len(result.mean_agent_duration_ms) == 8
    assert result.backend_status["embedding_loaded"] is False


def test_pipeline_runner_rejects_cache_enabled_service(tmp_path) -> None:
    with pytest.raises(ValueError, match="cache_enabled=false"):
        run_pipeline_benchmark(
            [pipeline_case()],
            service_for_benchmark(tmp_path, cache_enabled=True),
        )
