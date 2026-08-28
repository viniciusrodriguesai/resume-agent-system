from __future__ import annotations

import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings

ANA_RESUME = """Ana Teste

EXPERIÊNCIA

- Nunca utilizei Terraform.
- Utilizo Pulumi profissionalmente há 3 anos.
- Trabalhei com Prometheus em produção.
- Nunca utilizei Grafana.
- Li artigos sobre RabbitMQ.
- Não tenho experiência com Apache Kafka.
- Utilizo AlphaDB profissionalmente.
"""

ANA_JOB = """SOFTWARE ENGINEER

REQUISITOS OBRIGATÓRIOS

- Experiência com Terraform ou Pulumi.
- Experiência com Prometheus e Grafana.
- Experiência com RabbitMQ ou Apache Kafka.
- Experiência com AlphaDB ou BetaDB.
"""


class ZeroReranker:
    def predict(self, pairs, **_kwargs):
        return [0.0] * len(pairs)


def test_complete_profile_and_or_privacy_fixture(tmp_path) -> None:
    pytest.importorskip("presidio_analyzer")
    pytest.importorskip("presidio_anonymizer")
    settings = Settings(
        profile="complete",
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        embedding_enabled=False,
        reranker_enabled=True,
        reranker_top_n=5,
        docling_enabled=False,
        presidio_enabled=True,
        history_enabled=False,
        cache_enabled=False,
        store_raw_documents=False,
        store_anonymized_documents=False,
    )
    service = ResumeAnalysisService(settings)
    service.engine._reranker = ZeroReranker()

    result = service.analyze(
        AnalysisRequest(
            resume_text=ANA_RESUME,
            job_text=ANA_JOB,
            profile="complete",
            strictness="conservador",
        )
    )
    matches = {match.requirement.text: match for match in result.matches}

    assert matches["Experiência com Terraform ou Pulumi"].status == "matched"
    assert matches["Experiência com Prometheus e Grafana"].status != "matched"
    assert matches["Experiência com RabbitMQ ou Apache Kafka"].status == "missing"
    assert matches["Experiência com AlphaDB ou BetaDB"].status == "matched"
    candidate_text = "\n".join(result.candidate.chunks)
    for technology in (
        "Pulumi",
        "Prometheus",
        "Grafana",
        "RabbitMQ",
        "Apache Kafka",
        "AlphaDB",
    ):
        assert technology in candidate_text
    assert {"Pulumi", "Prometheus"} <= {skill.name for skill in result.candidate.skills}
    assert result.privacy.raw_document_stored is False
    assert result.privacy.anonymized_document_stored is False
    assert all(
        match.status != "matched"
        or not match.top_candidates
        or match.top_candidates[0].concept_coverage > 0.0
        or match.top_candidates[0].semantic_rule_match
        for match in result.matches
    )
