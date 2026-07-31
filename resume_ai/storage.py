from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .config import Settings

class HistoryStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.ensure()
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.settings.history_db) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    target_role TEXT,
                    overall_score INTEGER,
                    level TEXT,
                    strictness TEXT,
                    engine_status TEXT,
                    result_json TEXT NOT NULL
                )
                """
            )

    def save(self, state: Dict[str, object]) -> None:
        scoring = state.get("scoring", {}) or {}
        job_profile = state.get("job_profile", {}) or {}
        with sqlite3.connect(self.settings.history_db) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analyses (
                    analysis_id, created_at, target_role, overall_score,
                    level, strictness, engine_status, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.get("analysis_id"),
                    datetime.now(timezone.utc).isoformat(),
                    job_profile.get("title"),
                    scoring.get("overall_score"),
                    scoring.get("level"),
                    state.get("strictness"),
                    json.dumps(state.get("engine_status", {}), ensure_ascii=False),
                    json.dumps(state, ensure_ascii=False),
                ),
            )

    def list_recent(self, limit: int = 20) -> List[Dict[str, object]]:
        with sqlite3.connect(self.settings.history_db) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT analysis_id, created_at, target_role, overall_score,
                       level, strictness
                FROM analyses
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, analysis_id: str) -> Optional[Dict[str, object]]:
        with sqlite3.connect(self.settings.history_db) as connection:
            row = connection.execute(
                "SELECT result_json FROM analyses WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None
