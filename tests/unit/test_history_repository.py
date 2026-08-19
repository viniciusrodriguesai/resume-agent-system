from datetime import UTC, datetime, timedelta

from resume_ai.domain.models import (
    AnalysisResult,
    CandidateProfile,
    JobProfile,
    PrivacyReport,
    ScoreSummary,
)
from resume_ai.infrastructure.history import HistoryRepository
from resume_ai.settings import Settings


def history_settings(tmp_path, **overrides):
    return Settings(
        project_root=tmp_path,
        data_dir=tmp_path / 'data',
        cache_dir=tmp_path / 'cache',
        history_enabled=True,
        **overrides,
    )


def analysis_result(
    analysis_id: str,
    created_at: datetime,
    *,
    score: int = 80,
    job_title: str = 'Synthetic role',
) -> AnalysisResult:
    return AnalysisResult(
        analysis_id=analysis_id,
        created_at=created_at,
        profile='demo',
        strictness='equilibrado',
        candidate=CandidateProfile(),
        job=JobProfile(title=job_title),
        privacy=PrivacyReport(method='synthetic fixture'),
        matches=[],
        score=ScoreSummary(
            overall_score=score,
            level='boa',
            matched=1,
            partial=0,
            missing=0,
            required_missing=0,
        ),
        recommendations=[],
        review_summary='Synthetic result',
        traces=[],
    )


def test_disabled_history_does_not_create_sqlite_database(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        history_enabled=False,
    )

    repository = HistoryRepository(settings)

    assert repository.list_recent() == []
    repository.clear()
    assert not settings.history_db.exists()


def test_history_saves_and_lists_result_in_temporary_database(tmp_path) -> None:
    settings = history_settings(tmp_path)
    repository = HistoryRepository(settings)
    created_at = datetime(2026, 1, 1, tzinfo=UTC)

    repository.save(analysis_result('analysis-1', created_at))

    assert settings.history_db.exists()
    assert repository.list_recent() == [
        {
            'id': 'analysis-1',
            'created_at': created_at.isoformat(),
            'job_title': 'Synthetic role',
            'profile': 'demo',
            'score': 80,
            'level': 'boa',
        }
    ]


def test_history_orders_multiple_results_and_applies_limit(tmp_path) -> None:
    repository = HistoryRepository(history_settings(tmp_path))
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    for index in range(4):
        repository.save(
            analysis_result(
                f'analysis-{index}',
                base_time + timedelta(minutes=index),
                score=70 + index,
            )
        )

    rows = repository.list_recent(limit=2)

    assert [row['id'] for row in rows] == ['analysis-3', 'analysis-2']


def test_history_persists_after_repository_reopen(tmp_path) -> None:
    settings = history_settings(tmp_path)
    HistoryRepository(settings).save(
        analysis_result('analysis-reopened', datetime(2026, 1, 1, tzinfo=UTC))
    )

    reopened = HistoryRepository(settings)

    assert [row['id'] for row in reopened.list_recent()] == ['analysis-reopened']


def test_history_clear_removes_all_results(tmp_path) -> None:
    repository = HistoryRepository(history_settings(tmp_path))
    repository.save(analysis_result('analysis-1', datetime(2026, 1, 1, tzinfo=UTC)))
    repository.save(analysis_result('analysis-2', datetime(2026, 1, 2, tzinfo=UTC)))

    repository.clear()

    assert repository.list_recent() == []
