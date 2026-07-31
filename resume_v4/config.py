from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Config:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("RESUME_V4_DATA_DIR", ROOT / "data")))
    modelo_embeddings: str = os.getenv("RESUME_V4_EMBEDDINGS", "BAAI/bge-m3")
    modelo_reranker: str = os.getenv("RESUME_V4_RERANKER", "BAAI/bge-reranker-v2-m3")
    usar_embeddings: bool = os.getenv("RESUME_V4_USAR_EMBEDDINGS", "1") not in {"0", "false", "False"}
    usar_reranker: bool = os.getenv("RESUME_V4_USAR_RERANKER", "1") not in {"0", "false", "False"}
    usar_docling: bool = os.getenv("RESUME_V4_USAR_DOCLING", "1") not in {"0", "false", "False"}
    usar_presidio: bool = os.getenv("RESUME_V4_USAR_PRESIDIO", "1") not in {"0", "false", "False"}
    top_k: int = int(os.getenv("RESUME_V4_TOP_K", "5"))
    max_revisoes: int = int(os.getenv("RESUME_V4_MAX_REVISOES", "1"))

    @property
    def banco_historico(self) -> Path:
        return self.data_dir / "historico.sqlite"

    @property
    def banco_checkpoints(self) -> Path:
        return self.data_dir / "checkpoints.sqlite"

    @property
    def banco_esco(self) -> Path:
        return self.data_dir / "esco.sqlite"

    def preparar(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
