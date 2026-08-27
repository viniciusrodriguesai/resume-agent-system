from __future__ import annotations

import pytest

from resume_ai.agents.catalog import concept_group_for, detect_skills


def test_structured_catalog_contains_v603_technologies():
    names = {
        skill.name
        for skill in detect_skills(
            "Apache Kafka, Prometheus, Grafana, Memcached, Pulumi e Java"
        )
    }

    assert {
        "Apache Kafka",
        "Prometheus",
        "Grafana",
        "Memcached",
        "Pulumi",
        "Java",
    } <= names


@pytest.mark.parametrize(
    ("text", "unexpected"),
    [
        ("JavaScript", "Java"),
        ("GitHub", "Git"),
        ("C++", "C"),
    ],
)
def test_catalog_does_not_use_unsafe_substrings(text: str, unexpected: str):
    assert unexpected not in {skill.name for skill in detect_skills(text)}


def test_uncataloged_technology_still_uses_literal_matching_structure():
    group = concept_group_for("Experiência com TecnologiaÑDB")

    assert [concept.canonical for concept in group.concepts] == ["tecnologiandb"]
    assert group.uses_literal_fallback is True
