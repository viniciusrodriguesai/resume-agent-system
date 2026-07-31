from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("RESUME_AI_DATA_DIR", PROJECT_ROOT / "data"))
    embedding_model: str = os.getenv(
        "RESUME_AI_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    reranker_model: str = os.getenv(
        "RESUME_AI_RERANKER_MODEL",
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    )
    enable_embeddings: bool = os.getenv("RESUME_AI_ENABLE_EMBEDDINGS", "1").lower() not in {"0", "false", "no"}
    enable_reranker: bool = os.getenv("RESUME_AI_ENABLE_RERANKER", "1").lower() not in {"0", "false", "no"}
    enable_docling: bool = os.getenv("RESUME_AI_ENABLE_DOCLING", "1").lower() not in {"0", "false", "no"}
    top_k: int = int(os.getenv("RESUME_AI_TOP_K", "5"))
    max_revisions: int = int(os.getenv("RESUME_AI_MAX_REVISIONS", "1"))

    @property
    def history_db(self) -> Path:
        return self.data_dir / "history.sqlite"

    @property
    def esco_db(self) -> Path:
        return self.data_dir / "esco.sqlite"

    def ensure(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
