from __future__ import annotations

from typing import Any

from resume_ai.settings import Settings


class VectorStore:
    """Adaptador opcional. A análise de um par currículo-vaga usa memória por padrão."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._db: Any = None
        if settings.vector_store == "lancedb":
            try:
                import lancedb

                self._db = lancedb.connect(str(settings.data_dir / "lancedb"))
            except Exception:
                self._db = None

    @property
    def enabled(self) -> bool:
        return self._db is not None
