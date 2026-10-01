"""End-to-end evidence regressions, including privacy preprocessing."""
from pathlib import Path

import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings


@pytest.mark.parametrize(("resume", "requirement", "expected"), [
    ("Data Science and Artificial Intelligence student at Example University.",
     "Estar cursando Ciência de Dados ou Ciência da Computação.", "matched"),
    ("Cursando Ciência da Computação na Universidade Exemplo.",
     "Estar cursando Ciência de Dados ou Ciência da Computação.", "matched"),
    ("Completed a degree in Computer Science in 2020.",
     "Estar cursando Ciência da Computação.", "not_matched"),
    ("History student at Example University.",
     "Estar cursando Ciência da Computação.", "not_matched"),
    ("Built predictive machine learning models.",
     "Implantação de modelos de machine learning.", "not_matched"),
    ("Deployed machine learning models behind an inference API.",
     "Implantação de modelos de machine learning.", "matched"),
    ("No experience with deployment of machine learning models.",
     "Implantação de modelos de machine learning.", "not_matched"),
])
def test_evidence_grounding(tmp_path, resume, requirement, expected):
    settings = Settings(project_root=tmp_path, data_dir=tmp_path / "data",
                        cache_dir=tmp_path / "cache", embedding_enabled=False,
                        reranker_enabled=False, history_enabled=False)
    result = ResumeAnalysisService(settings).analyze(AnalysisRequest(
        resume_text=resume,
        job_text=f"Data internship\nREQUISITOS OBRIGATÓRIOS\n- {requirement}",
    ))
    assert len(result.matches) == 1
    if expected == "not_matched":
        assert result.matches[0].status != "matched"
    else:
        assert result.matches[0].status == expected


def test_existing_demo_preserves_education_and_requires_deployment(tmp_path):
    root = Path(__file__).resolve().parents[2]
    settings = Settings(project_root=tmp_path, data_dir=tmp_path / "data",
                        cache_dir=tmp_path / "cache", embedding_enabled=False,
                        reranker_enabled=False, history_enabled=False)
    result = ResumeAnalysisService(settings).analyze(AnalysisRequest(
        resume_text=(root / "examples/sample_resume.txt").read_text(),
        job_text=(root / "examples/vaga_exemplo.txt").read_text(),
    ))
    enrollment = next(m for m in result.matches if "Estar cursando" in m.requirement.text)
    deployment = next(m for m in result.matches if "Implantação" in m.requirement.text)
    assert enrollment.status == "matched"
    assert deployment.status != "matched"
