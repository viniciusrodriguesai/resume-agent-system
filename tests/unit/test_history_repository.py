import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

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


def test_history_non_positive_limit_returns_no_rows(tmp_path) -> None:
    repository = HistoryRepository(history_settings(tmp_path))
    repository.save(analysis_result('analysis-1', datetime(2026, 1, 1, tzinfo=UTC)))

    assert repository.list_recent(limit=0) == []
    assert repository.list_recent(limit=-1) == []


def test_history_excessive_limit_is_bounded_by_configuration(tmp_path) -> None:
    repository = HistoryRepository(history_settings(tmp_path, history_query_limit=2))
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    for index in range(4):
        repository.save(analysis_result(f'analysis-{index}', base_time + timedelta(minutes=index)))

    rows = repository.list_recent(limit=10_000)

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


def test_history_configures_wal_and_busy_timeout(tmp_path) -> None:
    repository = HistoryRepository(
        history_settings(tmp_path, history_busy_timeout_ms=7000)
    )

    with repository._connect() as connection:
        journal_mode = connection.execute('PRAGMA journal_mode').fetchone()[0]
        busy_timeout = connection.execute('PRAGMA busy_timeout').fetchone()[0]

    assert journal_mode == 'wal'
    assert busy_timeout == 7000


def test_history_supports_basic_concurrent_writes(tmp_path) -> None:
    repository = HistoryRepository(
        history_settings(tmp_path, history_busy_timeout_ms=10_000)
    )
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    results = [
        analysis_result(f'analysis-{index}', base_time + timedelta(seconds=index))
        for index in range(12)
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(repository.save, results))

    assert len(repository.list_recent(limit=20)) == 12


def test_history_retention_keeps_only_configured_recent_entries(tmp_path) -> None:
    settings = history_settings(tmp_path, history_max_entries=3)
    repository = HistoryRepository(settings)
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    for index in range(5):
        repository.save(
            analysis_result(f'analysis-{index}', base_time + timedelta(minutes=index))
        )

    rows = HistoryRepository(settings).list_recent(limit=10)

    assert [row['id'] for row in rows] == [
        'analysis-4',
        'analysis-3',
        'analysis-2',
    ]


def test_history_does_not_store_or_return_job_title(tmp_path) -> None:
    settings = history_settings(tmp_path)
    repository = HistoryRepository(settings)
    sensitive_sentinel = 'SENSITIVE_JOB_TITLE_SENTINEL'

    repository.save(
        analysis_result(
            'analysis-private',
            datetime(2026, 1, 1, tzinfo=UTC),
            job_title=sensitive_sentinel,
        )
    )

    with sqlite3.connect(settings.history_db) as connection:
        stored_title = connection.execute(
            'SELECT job_title FROM analyses WHERE id = ?',
            ('analysis-private',),
        ).fetchone()[0]
    assert stored_title == ''
    assert 'job_title' not in repository.list_recent()[0]
    assert sensitive_sentinel.encode() not in settings.history_db.read_bytes()


def test_history_allowlists_engine_status_fields(tmp_path) -> None:
    settings = history_settings(tmp_path)
    repository = HistoryRepository(settings)
    sensitive_sentinel = "candidate@example.invalid at C:\\private\\model"
    result = analysis_result(
        "analysis-engine-status",
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    result.engine_status = {
        "embedding_enabled": True,
        "embedding_backend": "torch",
        "embedding_loaded": False,
        "embedding_model": sensitive_sentinel,
        "embedding_error": sensitive_sentinel,
        "reranker_enabled": True,
        "reranker_loaded": False,
        "reranker_error": sensitive_sentinel,
        "cache_hit": False,
        "unexpected": sensitive_sentinel,
    }

    repository.save(result)

    with sqlite3.connect(settings.history_db) as connection:
        stored_summary = connection.execute(
            "SELECT summary_json FROM analyses WHERE id = ?",
            (result.analysis_id,),
        ).fetchone()[0]
    assert json.loads(stored_summary)["engine_status"] == {
        "embedding_enabled": True,
        "embedding_backend": "torch",
        "embedding_loaded": False,
        "reranker_enabled": True,
        "reranker_loaded": False,
        "cache_hit": False,
    }
    database_files = settings.history_db.parent.glob(f"{settings.history_db.name}*")
    assert all(sensitive_sentinel.encode() not in path.read_bytes() for path in database_files)


def test_history_migration_scrubs_legacy_job_titles(tmp_path) -> None:
    settings = history_settings(tmp_path)
    sensitive_sentinel = 'LEGACY_SENSITIVE_TITLE_SENTINEL'
    with sqlite3.connect(settings.history_db) as connection:
        connection.execute(
            """
            CREATE TABLE analyses (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                job_title TEXT NOT NULL,
                profile TEXT NOT NULL,
                score INTEGER NOT NULL,
                level TEXT NOT NULL,
                summary_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            'INSERT INTO analyses VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                'legacy-analysis',
                datetime(2025, 1, 1, tzinfo=UTC).isoformat(),
                sensitive_sentinel,
                'demo',
                70,
                'boa',
                '{}',
            ),
        )

    repository = HistoryRepository(settings)

    with sqlite3.connect(settings.history_db) as connection:
        stored_title = connection.execute(
            'SELECT job_title FROM analyses WHERE id = ?',
            ('legacy-analysis',),
        ).fetchone()[0]
        schema_version = connection.execute('PRAGMA user_version').fetchone()[0]
    assert stored_title == ''
    assert schema_version == 1
    assert 'job_title' not in repository.list_recent()[0]
    database_files = settings.history_db.parent.glob(f'{settings.history_db.name}*')
    assert all(sensitive_sentinel.encode() not in path.read_bytes() for path in database_files)


def test_history_rejects_newer_unknown_schema(tmp_path) -> None:
    settings = history_settings(tmp_path)
    with sqlite3.connect(settings.history_db) as connection:
        connection.execute('PRAGMA user_version = 999')

    with pytest.raises(RuntimeError, match='schema is newer'):
        HistoryRepository(settings)
