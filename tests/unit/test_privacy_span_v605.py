from __future__ import annotations

from dataclasses import dataclass

import pytest

from resume_ai.infrastructure.privacy import _filter_presidio_results


@dataclass
class FakeResult:
    entity_type: str
    start: int
    end: int


def person_result(text: str, person: str) -> FakeResult:
    start = text.index(person)
    return FakeResult(entity_type="PERSON", start=start, end=start + len(person))


@pytest.mark.parametrize(
    ("text", "technology"),
    [
        ("Monitorei aplicações com Prometheus.", "Prometheus"),
        ("Apache Kafka foi usado em produção.", "Apache Kafka"),
        ("Utilizei AlphaDB em produção.", "AlphaDB"),
    ],
)
def test_exact_technical_person_false_positive_is_suppressed(
    text: str,
    technology: str,
) -> None:
    result = person_result(text, technology)

    assert _filter_presidio_results(text, [result]) == []


@pytest.mark.parametrize(
    ("text", "person", "technology"),
    [
        ("João Prometheus Silva", "João Prometheus Silva", "Prometheus"),
        (
            "Trabalhei com João Silva utilizando Python.",
            "João Silva",
            "Python",
        ),
        (
            "Maria Kafka desenvolveu uma API em FastAPI.",
            "Maria Kafka",
            "FastAPI",
        ),
        (
            "Conversei com Kafka Oliveira sobre PostgreSQL.",
            "Kafka Oliveira",
            "PostgreSQL",
        ),
        ("João Silva utilizou AlphaDB.", "João Silva", "AlphaDB"),
    ],
)
def test_real_person_fragments_are_retained_without_overlapping_technology(
    text: str,
    person: str,
    technology: str,
) -> None:
    result = person_result(text, person)

    filtered = _filter_presidio_results(text, [result])
    fragments = [text[item.start:item.end] for item in filtered]
    assert technology in text
    assert fragments
    assert all(technology not in fragment for fragment in fragments)
    assert any(
        token in fragment
        for token in person.split()
        for fragment in fragments
    )


def test_non_person_results_are_untouched() -> None:
    text = "joao@example.invalid utiliza Python."
    result = FakeResult(entity_type="EMAIL_ADDRESS", start=0, end=20)

    assert _filter_presidio_results(text, [result]) == [result]


def test_technology_inside_name_is_carved_from_broad_person_span() -> None:
    text = "Maria Kafka desenvolveu uma API em FastAPI."
    result = FakeResult(entity_type="PERSON", start=0, end=text.index(" em FastAPI"))

    filtered = _filter_presidio_results(text, [result])
    fragments = [text[item.start:item.end].strip() for item in filtered]

    assert fragments == ["Maria"]
    assert all("Kafka" not in fragment for fragment in fragments)


def test_broad_person_span_anonymizes_name_but_excludes_unrelated_technology() -> None:
    text = "Conversei com Kafka Oliveira sobre PostgreSQL."
    result = person_result(text, "Kafka Oliveira sobre PostgreSQL")

    filtered = _filter_presidio_results(text, [result])

    assert filtered
    fragments = [text[item.start:item.end] for item in filtered]

    assert any("Oliveira" in fragment for fragment in fragments)
    assert all("Kafka" not in fragment for fragment in fragments)
    assert all("PostgreSQL" not in fragment for fragment in fragments)


def test_broad_false_positive_is_split_away_from_technical_term() -> None:
    text = "Li artigos sobre RabbitMQ."
    result = FakeResult(entity_type="PERSON", start=0, end=text.index("."))

    filtered = _filter_presidio_results(text, [result])

    assert all("RabbitMQ" not in text[item.start:item.end] for item in filtered)


def test_sentence_initial_technical_verb_does_not_turn_technology_into_person() -> None:
    text = "Testei Kubernetes em um cluster local."
    result = person_result(text, "Testei Kubernetes")

    filtered = _filter_presidio_results(text, [result])

    assert all("Kubernetes" not in text[item.start:item.end] for item in filtered)
