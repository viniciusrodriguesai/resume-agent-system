from __future__ import annotations

import secrets
from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from resume_ai import __version__
from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult, HealthResponse
from resume_ai.infrastructure.observability import METRICS
from resume_ai.settings import Settings


@lru_cache(maxsize=3)
def service_for(profile: str) -> ResumeAnalysisService:
    return ResumeAnalysisService(Settings.for_profile(profile))  # type: ignore[arg-type]


settings = Settings()
app = FastAPI(
    title="Resume Match AI API",
    description="API local e explicável para análise de currículos e vagas.",
    version=__version__,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key and (not x_api_key or not secrets.compare_digest(x_api_key, settings.api_key)):
        raise HTTPException(status_code=401, detail="API key inválida")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    service = service_for(settings.profile)
    return HealthResponse(
        profile=settings.profile,
        model_loaded=bool(service.engine.status["embedding_loaded"]),
        memory_mb=service.telemetry.process_memory_mb(),
    )


@app.get("/v1/profiles")
def profiles() -> dict[str, object]:
    return {
        "profiles": {
            "demo": "MiniLM ONNX, sem reranker e sem Docling",
            "balanced": "E5-small ONNX e reranker apenas no top 3",
            "complete": "BGE-M3, reranker BGE, Docling e Presidio quando instalados",
        }
    }


@app.post("/v1/analyze", response_model=AnalysisResult, dependencies=[Depends(verify_api_key)])
def analyze(request: AnalysisRequest) -> AnalysisResult:
    service = service_for(request.profile)
    return service.analyze(request)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str | bytes:
    generated = METRICS.render()
    if generated is not None:
        return generated
    service = service_for(settings.profile)
    memory = service.telemetry.process_memory_mb()
    return (
        "# HELP resume_ai_process_memory_mb Memória RSS do processo em MB\n"
        "# TYPE resume_ai_process_memory_mb gauge\n"
        f"resume_ai_process_memory_mb {memory}\n"
    )
