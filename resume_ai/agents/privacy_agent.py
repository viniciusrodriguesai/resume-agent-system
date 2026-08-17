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
            warnings=lambda result: (
                ["presidio-fallback"]
                if self.service.settings.presidio_enabled and "Presidio" not in result[1].method
                else []
            ),
            evidence=lambda result: [
                f"entity-type:{entity.entity_type}"
                for entity in result[1].entities
            ],
            metadata=lambda result: {
                "removed_count": result[1].total_removed,
                "entity_type_count": len(result[1].entities),
            },
        )
