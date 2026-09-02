from __future__ import annotations

from dataclasses import dataclass

import pytest

from resume_ai.infrastructure.privacy import PrivacyService, _filter_presidio_results
from resume_ai.settings import Settings


@dataclass
class FakeResult:
    entity_type: str
    start: int
    end: int


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


@pytest.mark.parametrize(
    ("text", "person_tokens", "technology"),
    [
        ("Bruno Santos", ("Bruno", "Santos"), None),
        ("Bruno Santos Python", ("Bruno", "Santos"), "Python"),
        ("Python Bruno Santos", ("Bruno", "Santos"), "Python"),
        (
            "Trabalhei com Bruno Santos usando Python",
            ("Bruno", "Santos"),
            "Python",
        ),
        ("Bruno Santos utilizou FastAPI", ("Bruno", "Santos"), "FastAPI"),
        ("Bruno Kafka Santos", ("Bruno", "Santos"), "Kafka"),
        (
            "Bruno Prometheus Santos",
            ("Bruno", "Santos"),
            "Prometheus",
        ),
        (
            "PostgreSQL foi configurado em produção por Bruno Santos.",
            ("Bruno", "Santos"),
            "PostgreSQL",
        ),
        ("Bruno Santos Python Python", ("Bruno", "Santos"), "Python"),
        ("Bruno Santos Python Kafka", ("Bruno", "Santos"), "Kafka"),
        ("Bruno Santos NovaCache", ("Bruno", "Santos"), "NovaCache"),
    ],
)
def test_regex_privacy_removes_inline_people_without_removing_technology(
    tmp_path,
    text: str,
    person_tokens: tuple[str, ...],
    technology: str | None,
) -> None:
    anonymized, report = privacy_service(tmp_path).anonymize(text)

    assert all(token not in anonymized for token in person_tokens)
    if technology:
        assert technology in anonymized
    assert report.total_removed >= 1


def test_broad_person_span_is_split_around_trailing_technology() -> None:
    text = "Bruno Santos Python"
    result = FakeResult(entity_type="PERSON", start=0, end=len(text))

    filtered = _filter_presidio_results(text, [result])
    fragments = [text[item.start:item.end].strip() for item in filtered]

    assert fragments == ["Bruno Santos"]
    assert all("Python" not in fragment for fragment in fragments)


def test_broad_person_span_is_split_around_embedded_technology() -> None:
    text = "Bruno Kafka Santos"
    result = FakeResult(entity_type="PERSON", start=0, end=len(text))

    filtered = _filter_presidio_results(text, [result])
    fragments = [text[item.start:item.end].strip() for item in filtered]

    assert fragments == ["Bruno", "Santos"]
    assert all("Kafka" not in fragment for fragment in fragments)


def test_presidio_person_false_positive_does_not_remove_operational_verb() -> None:
    text = "Trabalhei com PostgreSQL na Empresa X."
    start = text.index("Trabalhei")
    result = FakeResult(entity_type="PERSON", start=start, end=start + len("Trabalhei"))

    filtered = _filter_presidio_results(text, [result])

    assert filtered == []


def test_presidio_keeps_real_person_while_dropping_operational_verb() -> None:
    text = "Trabalhei com João Silva usando PostgreSQL."
    verb_start = text.index("Trabalhei")
    name_start = text.index("João Silva")
    results = [
        FakeResult(
            entity_type="PERSON",
            start=verb_start,
            end=verb_start + len("Trabalhei"),
        ),
        FakeResult(
            entity_type="PERSON",
            start=name_start,
            end=name_start + len("João Silva"),
        ),
    ]

    filtered = _filter_presidio_results(text, results)
    fragments = [text[item.start:item.end] for item in filtered]

    assert fragments == ["João Silva"]
