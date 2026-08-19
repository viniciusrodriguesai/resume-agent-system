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
    embedding_backend: Literal["onnx", "torch", "openvino"] = "torch"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 16
    normalize_embeddings: bool = True

    reranker_enabled: bool = False
    reranker_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    reranker_top_n: int = 3

    docling_enabled: bool = False
    presidio_enabled: bool = False
    full_ner_enabled: bool = False

    top_k: int = 3
    max_requirements: int = 30
    max_chunk_chars: int = 420
    max_document_chars: int = 30_000
    max_job_chars: int = 30_000
    max_revisions: int = 1

    cache_enabled: bool = True
    cache_backend: Literal["memory", "disk"] = "memory"
    cache_max_entries: int = 128
    cache_ttl_seconds: int = 86_400
    store_raw_documents: bool = False
    store_anonymized_documents: bool = False

    max_upload_mb: int = 10
    allowed_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt")
    log_pii: bool = False
    log_level: str = "INFO"
    api_key: str | None = None
    environment: Literal["development", "test", "production"] = "development"
    allowed_profiles: tuple[ProfileName, ...] = ("demo", "balanced", "complete")
    api_max_body_mb: int = 1
    api_rate_limit_per_minute: int = 60
    require_login: bool = False
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    history_enabled: bool = True
    history_query_limit: int = Field(default=100, ge=1, le=1000)
    vector_store: Literal["memory", "lancedb"] = "memory"

    def model_post_init(self, __context: object) -> None:
        root = self.project_root
        if not self.data_dir.is_absolute():
            self.data_dir = root / self.data_dir
        if not self.cache_dir.is_absolute():
            self.cache_dir = root / self.cache_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.cache_backend == "disk" and not self.store_anonymized_documents:
            raise ValueError(
                "RESUME_CACHE_BACKEND=disk requires RESUME_STORE_ANONYMIZED_DOCUMENTS=true"
            )
        if not self.allowed_profiles:
            raise ValueError("RESUME_ALLOWED_PROFILES must contain at least one profile")

    @property
    def history_db(self) -> Path:
        return self.data_dir / "history.sqlite3"

    @classmethod
    def for_profile(cls, profile: ProfileName) -> Settings:
        base = cls(profile=profile)
        explicit_fields = base.model_fields_set
        if profile == "demo":
            defaults = {
                "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "embedding_backend": "torch",
                "embedding_enabled": True,
                "reranker_enabled": False,
                "docling_enabled": False,
                "presidio_enabled": False,
                "top_k": 3,
                "embedding_batch_size": 32,
                "max_revisions": 0,
            }
        elif profile == "balanced":
            defaults = {
                "embedding_model": "intfloat/multilingual-e5-small",
                "embedding_backend": "torch",
                "embedding_enabled": True,
                "reranker_enabled": True,
                "reranker_top_n": 3,
                "docling_enabled": False,
                "presidio_enabled": False,
                "top_k": 4,
                "embedding_batch_size": 16,
                "max_revisions": 1,
            }
        else:
            defaults = {
                "embedding_model": "BAAI/bge-m3",
                "embedding_backend": "torch",
                "embedding_enabled": True,
                "reranker_enabled": True,
                "reranker_model": "BAAI/bge-reranker-v2-m3",
                "reranker_top_n": 5,
                "docling_enabled": True,
                "presidio_enabled": True,
                "top_k": 5,
                "embedding_batch_size": 8,
                "max_revisions": 1,
            }
        return base.model_copy(
            update={key: value for key, value in defaults.items() if key not in explicit_fields}
        )
