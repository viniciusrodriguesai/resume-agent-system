from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from resume_ai.agents.catalog import concept_group_for
from resume_ai.domain.scoring import classify
from resume_ai.infrastructure.embeddings import EmbeddingEngine
from resume_ai.infrastructure.privacy import PrivacyService
from resume_ai.settings import Settings

FIRST_NAMES = ("Bruno", "João", "Maria", "Carla", "Rafael", "Helena", "Marcos", "Luciana")
LAST_NAMES = ("Santos", "Silva", "Oliveira", "Souza", "Costa", "Pereira", "Almeida", "Ferreira")
TECHNOLOGIES = (
    "Python",
    "Kafka",
    "Prometheus",
    "PostgreSQL",
    "FastAPI",
    "AlphaDB",
    "OmegaMQ",
    "NovaCache",
)


class FakeReranker:
    def __init__(self, score: float) -> None:
        self.score = score

    def predict(self, pairs, **_kwargs):
        return [self.score] * len(pairs)


def privacy_service(tmp_path) -> PrivacyService:
    return PrivacyService(
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            presidio_enabled=False,
            history_enabled=False,
            cache_enabled=False,
        )
    )


@st.composite
def person_technology_evidence(draw: st.DrawFn) -> tuple[str, tuple[str, str], tuple[str, ...]]:
    first = draw(st.sampled_from(FIRST_NAMES))
    last = draw(st.sampled_from(LAST_NAMES))
    technology = draw(st.sampled_from(TECHNOLOGIES))
    second_technology = draw(st.sampled_from(TECHNOLOGIES))
    pattern = draw(st.integers(min_value=0, max_value=4))
    person = f"{first} {last}"
    if pattern == 0:
        text = f"{person} {technology}"
        technologies = (technology,)
    elif pattern == 1:
        text = f"{technology} {person}"
        technologies = (technology,)
    elif pattern == 2:
        text = f"{person} {technology} {second_technology}"
        technologies = (technology, second_technology)
    elif pattern == 3:
        text = f"Trabalhei com {person} usando {technology}."
        technologies = (technology,)
    else:
        text = f"{first} {technology} {last} utilizou {second_technology}."
        technologies = (technology, second_technology)
    return text, (first, last), technologies


@settings(
    max_examples=500,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(case=person_technology_evidence())
def test_detectable_person_is_removed_and_technology_is_preserved(tmp_path, case) -> None:
    text, person_tokens, technologies = case

    anonymized, report = privacy_service(tmp_path).anonymize(text)

    assert all(person_token not in anonymized for person_token in person_tokens)
    assert all(technology in anonymized for technology in technologies)
    assert report.total_removed >= 1


def evaluate_requirement(
    tmp_path,
    requirement: str,
    evidence: str,
    reranker_score: float,
):
    engine = EmbeddingEngine(
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            embedding_enabled=False,
            reranker_enabled=True,
            history_enabled=False,
            cache_enabled=False,
        )
    )
    engine._reranker = FakeReranker(reranker_score)
    group = concept_group_for(requirement)
    candidates = engine.retrieve(requirement, [evidence], concept_groups=group.alias_groups)
    return engine.rerank(requirement, candidates)[0]


@settings(
    max_examples=150,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    pair=st.sampled_from(
        (("Terraform", "Pulumi"), ("RabbitMQ", "Kafka"), ("Grafana", "Prometheus"))
    ),
    boundary=st.sampled_from((". ", "! ", "? ", "; ", "\n")),
    negative=st.sampled_from(
        ("Nunca utilizei {left}", "Não tenho experiência com {left}", "Sem experiência com {left}")
    ),
    positive=st.sampled_from(
        ("Utilizo {right} profissionalmente.", "Uso {right} em produção.", "Trabalho com {right} na empresa.")
    ),
    reranker_score=st.sampled_from((0.0, 1.0)),
)
def test_negation_does_not_cross_semantic_boundaries(
    tmp_path,
    pair: tuple[str, str],
    boundary: str,
    negative: str,
    positive: str,
    reranker_score: float,
) -> None:
    left, right = pair
    evidence = negative.format(left=left) + boundary + positive.format(right=right)

    or_result = evaluate_requirement(
        tmp_path,
        f"Experiência com {left} ou {right}",
        evidence,
        reranker_score,
    )
    and_result = evaluate_requirement(
        tmp_path,
        f"Experiência com {left} e {right}",
        evidence,
        reranker_score,
    )

    assert or_result["concept_coverage"] == 1.0
    assert or_result["explicitly_negated"] is False
    assert classify(or_result["final_score"], "conservador") == "matched"
    assert and_result["concept_coverage"] < 1.0
    assert classify(and_result["final_score"], "flexível") != "matched"
