from __future__ import annotations

from resume_ai.domain.models import AgentTrace, PrivacyReport
from resume_ai.infrastructure.privacy import PrivacyService

from .base import run_agent


class PrivacyAgent:
    name = "Agente de Privacidade"

    def __init__(self, service: PrivacyService) -> None:
        self.service = service

    def run(self, text: str) -> tuple[tuple[str, PrivacyReport], AgentTrace]:
        return run_agent(
            self.name,
            lambda: self.service.anonymize(text),
            lambda result: f"{result[1].total_removed} dado(s) pessoal(is) removido(s) antes dos embeddings.",
            lambda result: 0.92 if "Presidio" in result[1].method else 0.80,
        )
