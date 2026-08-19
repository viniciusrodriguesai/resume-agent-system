from __future__ import annotations

import json
import sqlite3
from typing import Any

from resume_ai.domain.models import AnalysisResult
from resume_ai.settings import Settings


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
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
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

    def save(self, result: AnalysisResult) -> None:
        if not self.settings.history_enabled:
            return
        summary: dict[str, Any] = {
            "score": result.score.model_dump(),
            "engine_status": result.engine_status,
            "timings_ms": result.timings_ms,
        }
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO analyses VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    result.analysis_id,
                    result.created_at.isoformat(),
                    result.job.title,
                    result.profile,
                    result.score.overall_score,
                    result.score.level,
                    json.dumps(summary, ensure_ascii=False),
                ),
            )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.settings.history_enabled or limit <= 0:
            return []
        effective_limit = min(limit, self.settings.history_query_limit)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, created_at, job_title, profile, score, level FROM analyses ORDER BY created_at DESC LIMIT ?",
                (effective_limit,),
            ).fetchall()
        return [
            {"id": row[0], "created_at": row[1], "job_title": row[2], "profile": row[3], "score": row[4], "level": row[5]}
            for row in rows
        ]

    def clear(self) -> None:
        if not self.settings.history_enabled:
            return
        with self._connect() as connection:
            connection.execute("DELETE FROM analyses")


HistoryRepository = SQLiteHistoryRepository
