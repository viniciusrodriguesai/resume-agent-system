from __future__ import annotations

import pytest

from resume_ai.agents.candidate_agent import CandidateAgent
from resume_ai.settings import Settings


def make_agent(tmp_path) -> CandidateAgent:
    return CandidateAgent(
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
            history_enabled=False,
        )
    )


@pytest.mark.parametrize(
    "heading",
    [
        "EXPERIÊNCIA",
        "EXPERIÊNCIA PROFISSIONAL",
        "WORK EXPERIENCE",
        "EMPLOYMENT",
    ],
)
def test_resume_experience_section_does_not_duplicate_into_projects(
    tmp_path,
    heading: str,
):
    text = f"""CANDIDATO SINTÉTICO

{heading}
- Desenvolvi aplicações backend em Python.
- Implementei cache distribuído utilizando Redis em produção.
"""

    profile, _ = make_agent(tmp_path).run(text, text)

    assert "Desenvolvi aplicações backend em Python." in profile.experience
    assert "Implementei cache distribuído utilizando Redis em produção." in profile.experience
    assert profile.projects == []


@pytest.mark.parametrize(
    "heading",
    [
        "PROJETOS",
        "PROJECTS",
        "PERSONAL PROJECTS",
    ],
)
def test_project_section_is_still_detected(tmp_path, heading: str):
    text = f"""CANDIDATO SINTÉTICO

{heading}
- Desenvolvi uma API pública com FastAPI.
- Implementei um pipeline de eventos.
"""

    profile, _ = make_agent(tmp_path).run(text, text)

    assert "Desenvolvi uma API pública com FastAPI." in profile.projects
    assert "Implementei um pipeline de eventos." in profile.projects
    assert profile.experience == []
