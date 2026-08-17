from __future__ import annotations

import secrets
import time
from collections import deque
from functools import lru_cache
from threading import Lock

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from starlette.middleware.base import RequestResponseEndpoint

from resume_ai import __version__
from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult, HealthResponse
from resume_ai.infrastructure.correlation import correlation_scope
from resume_ai.infrastructure.observability import METRICS
from resume_ai.settings import Settings


@lru_cache(maxsize=3)
def service_for(profile: str) -> ResumeAnalysisService:
    return ResumeAnalysisService(Settings.for_profile(profile))  # type: ignore[arg-type]


settings = Settings()
_rate_lock = Lock()
_request_times: dict[str, deque[float]] = {}
app = FastAPI(
    title="Resume Match AI API",
    description="API local e explicável para análise de currículos e vagas.",
    version=__version__,
)


@app.middleware("http")
async def guard_analysis_requests(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    if request.url.path != "/v1/analyze":
        return await call_next(request)

    max_bytes = settings.api_max_body_mb * 1024 * 1024
    raw_length = request.headers.get("content-length")
    if raw_length:
        try:
            content_length = int(raw_length)
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Content-Length invalido"})
        if content_length > max_bytes:
            return JSONResponse(status_code=413, content={"detail": "Corpo da requisicao muito grande"})

    limit = settings.api_rate_limit_per_minute
    if limit > 0:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with _rate_lock:
            recent = _request_times.setdefault(client, deque())
            while recent and now - recent[0] >= 60:
                recent.popleft()
            if len(recent) >= limit:
                return JSONResponse(status_code=429, content={"detail": "Limite de requisicoes excedido"})
            recent.append(now)
    return await call_next(request)


@app.middleware("http")
async def attach_request_id(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    with correlation_scope(request.headers.get("X-Request-ID")) as request_id:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
    expose_headers=["X-Request-ID"],
)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.environment == "production" and not settings.api_key:
        raise HTTPException(status_code=503, detail="API key obrigatoria em producao")
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
    descriptions = {
        "demo": "MiniLM ONNX, sem reranker e sem Docling",
        "balanced": "E5-small ONNX e reranker apenas no top 3",
        "complete": "BGE-M3, reranker BGE, Docling e Presidio quando instalados",
    }
    return {
        "profiles": {profile: descriptions[profile] for profile in settings.allowed_profiles}
    }


@app.post("/v1/analyze", response_model=AnalysisResult, dependencies=[Depends(verify_api_key)])
def analyze(request: AnalysisRequest) -> AnalysisResult:
    if request.profile not in settings.allowed_profiles:
        raise HTTPException(status_code=403, detail="Perfil nao permitido neste deployment")
    try:
        service = service_for(request.profile)
        return service.analyze(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
