from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProfileName = Literal["demo", "balanced", "complete"]


class Settings(BaseSettings):
    """Configuração central. Todas as opções podem ser definidas por variáveis RESUME_* ."""

    model_config = SettingsConfigDict(
        env_prefix="RESUME_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    profile: ProfileName = "demo"
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1])
    data_dir: Path = Path("data")
    cache_dir: Path = Path(".cache/resume-ai")

    embedding_enabled: bool = True
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_backend: Literal["onnx", "torch", "openvino"] = "onnx"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 8
    normalize_embeddings: bool = True

    reranker_enabled: bool = False
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    reranker_top_n: int = 3

    docling_enabled: bool = False
    presidio_enabled: bool = False
    full_ner_enabled: bool = False

    top_k: int = 3
    max_requirements: int = 30
    max_chunk_chars: int = 900
    max_document_chars: int = 30_000
    max_revisions: int = 1

    cache_enabled: bool = True
    cache_ttl_seconds: int = 86_400
    store_raw_documents: bool = False
    store_anonymized_documents: bool = False

    max_upload_mb: int = 10
    allowed_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt")
    log_pii: bool = False
    log_level: str = "INFO"
    api_key: str | None = None
    require_login: bool = False
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    history_enabled: bool = True
    vector_store: Literal["memory", "lancedb"] = "memory"

    def model_post_init(self, __context: object) -> None:
        root = self.project_root
        if not self.data_dir.is_absolute():
            self.data_dir = root / self.data_dir
        if not self.cache_dir.is_absolute():
            self.cache_dir = root / self.cache_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def history_db(self) -> Path:
        return self.data_dir / "history.sqlite3"

    @classmethod
    def for_profile(cls, profile: ProfileName) -> "Settings":
        base = cls(profile=profile)
        if profile == "demo":
            return base.model_copy(update={
                "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "embedding_backend": "onnx",
                "embedding_enabled": True,
                "reranker_enabled": False,
                "docling_enabled": False,
                "presidio_enabled": False,
                "top_k": 3,
                "max_revisions": 0,
            })
        if profile == "balanced":
            return base.model_copy(update={
                "embedding_model": "intfloat/multilingual-e5-small",
                "embedding_backend": "onnx",
                "embedding_enabled": True,
                "reranker_enabled": True,
                "reranker_top_n": 3,
                "docling_enabled": False,
                "presidio_enabled": False,
                "top_k": 4,
                "max_revisions": 1,
            })
        return base.model_copy(update={
            "embedding_model": "BAAI/bge-m3",
            "embedding_backend": "torch",
            "embedding_enabled": True,
            "reranker_enabled": True,
            "reranker_model": "BAAI/bge-reranker-v2-m3",
            "reranker_top_n": 5,
            "docling_enabled": True,
            "presidio_enabled": True,
            "top_k": 5,
            "max_revisions": 1,
        })
