from __future__ import annotations

import json
import sqlite3
from typing import Any

from resume_ai.domain.models import AnalysisResult
from resume_ai.settings import Settings

_SCHEMA_VERSION = 1
_BOOLEAN_ENGINE_STATUS_FIELDS = (
    "embedding_enabled",
    "embedding_loaded",
    "reranker_enabled",
    "reranker_loaded",
    "cache_hit",
)
_ALLOWED_EMBEDDING_BACKENDS = frozenset({"onnx", "openvino", "torch"})


def _safe_engine_status(status: dict[str, Any]) -> dict[str, bool | str]:
    safe: dict[str, bool | str] = {
        field: value
        for field in _BOOLEAN_ENGINE_STATUS_FIELDS
        if isinstance((value := status.get(field)), bool)
    }
    backend = status.get("embedding_backend")
    if isinstance(backend, str) and backend in _ALLOWED_EMBEDDING_BACKENDS:
        safe["embedding_backend"] = backend
    return safe


class SQLiteHistoryRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.path = settings.history_db
        if settings.history_enabled:
            self._initialize()

    def _connect(self) -> sqlite3.Connection:
        timeout_seconds = self.settings.history_busy_timeout_ms / 1000
        connection = sqlite3.connect(self.path, timeout=timeout_seconds)
        connection.execute(f"PRAGMA busy_timeout = {self.settings.history_busy_timeout_ms}")
        connection.execute("PRAGMA secure_delete=ON")
        return connection

    def _initialize(self) -> None:
        migration_performed = False
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
            if schema_version > _SCHEMA_VERSION:
                raise RuntimeError("history database schema is newer than this application")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    summary_json TEXT NOT NULL
                )
            """)
            if schema_version < 1:
                connection.execute("UPDATE analyses SET job_title = '' WHERE job_title <> ''")
                connection.execute("PRAGMA user_version = 1")
                migration_performed = True
        if migration_performed:
            with self._connect() as connection:
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def save(self, result: AnalysisResult) -> None:
        if not self.settings.history_enabled:
            return
        summary: dict[str, Any] = {
            "score": result.score.model_dump(),
            "engine_status": _safe_engine_status(result.engine_status),
            "timings_ms": result.timings_ms,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analyses (
                    id, created_at, job_title, profile, score, level, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.analysis_id,
                    result.created_at.isoformat(),
                    "",
                    result.profile,
                    result.score.overall_score,
                    result.score.level,
                    json.dumps(summary, ensure_ascii=False),
                ),
            )
            connection.execute(
                """
                DELETE FROM analyses
                WHERE id NOT IN (
                    SELECT id FROM analyses
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                )
                """,
                (self.settings.history_max_entries,),
            )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.settings.history_enabled or limit <= 0:
            return []
        effective_limit = min(limit, self.settings.history_query_limit)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, created_at, profile, score, level
                FROM analyses
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (effective_limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "created_at": row[1],
                "profile": row[2],
                "score": row[3],
                "level": row[4],
            }
            for row in rows
        ]

    def clear(self) -> None:
        if not self.settings.history_enabled:
            return
        with self._connect() as connection:
            connection.execute("DELETE FROM analyses")


HistoryRepository = SQLiteHistoryRepository
