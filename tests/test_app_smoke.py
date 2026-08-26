from pathlib import Path

import pytest

from resume_ai.application.analyze_resume import ResumeAnalysisService

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_streamlit_starts():
    app = AppTest.from_file(APP_PATH)
    app.run(timeout=30)
    assert not app.exception


def test_streamlit_hides_backend_failure_details(monkeypatch):
    private_detail = "candidate@example.invalid at C:\\private\\resume.txt"

    def fail_analysis(self, request):
        raise RuntimeError(private_detail)

    monkeypatch.setattr(ResumeAnalysisService, "analyze", fail_analysis)
    app = AppTest.from_file(APP_PATH)
    app.run(timeout=30)
    app.text_area[0].input("Python engineer with production API experience")
    app.text_area[1].input("Python engineer required for production APIs")
    app.checkbox[0].check()
    submit = next(button for button in app.button if "Executar análise" in button.label)
    submit.click()
    app.run(timeout=30)

    assert not app.exception
    assert any("Não foi possível concluir a análise" in error.value for error in app.error)
    assert private_detail not in str(app)
