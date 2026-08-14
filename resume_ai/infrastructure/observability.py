from __future__ import annotations

from typing import Any


class MetricsRecorder:
    """Prometheus opcional, sem tornar o pacote obrigatório no modo demo."""

    def __init__(self) -> None:
        self.enabled = False
        self._generate_latest: Any = None
        try:
            from prometheus_client import Counter, Gauge, Histogram, generate_latest

            self.analysis_total = Counter("resume_ai_analysis_total", "Número total de análises", ["profile", "status"])
            self.analysis_duration = Histogram("resume_ai_analysis_duration_seconds", "Duração total da análise", ["profile"])
            self.score_gauge = Gauge("resume_ai_last_score", "Última nota calculada", ["profile"])
            self.cache_total = Counter("resume_ai_cache_total", "Consultas ao cache de análises", ["profile", "result"])
            self._generate_latest = generate_latest
            self.enabled = True
        except Exception:
            self.analysis_total = None
            self.analysis_duration = None
            self.score_gauge = None
            self.cache_total = None

    def record_success(self, profile: str, duration_seconds: float, score: int) -> None:
        if not self.enabled:
            return
        self.analysis_total.labels(profile=profile, status="success").inc()
        self.analysis_duration.labels(profile=profile).observe(duration_seconds)
        self.score_gauge.labels(profile=profile).set(score)

    def record_failure(self, profile: str) -> None:
        if self.enabled:
            self.analysis_total.labels(profile=profile, status="failure").inc()

    def record_cache(self, profile: str, hit: bool) -> None:
        if self.enabled:
            self.cache_total.labels(profile=profile, result="hit" if hit else "miss").inc()

    def render(self) -> bytes | None:
        return self._generate_latest() if self.enabled and self._generate_latest else None


METRICS = MetricsRecorder()
