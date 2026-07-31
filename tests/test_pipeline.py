from pathlib import Path

from resume_ai.analyzer import MultiAgentAnalyzer

def test_pipeline_runs_without_heavy_ai():
    root = Path(__file__).resolve().parents[1]
    resume = (root / "examples" / "sample_resume.txt").read_text(encoding="utf-8")
    job = (root / "examples" / "sample_job.txt").read_text(encoding="utf-8")

    analyzer = MultiAgentAnalyzer(
        full_ai=False,
        persist_history=False,
    )
    result = analyzer.run(resume, job)

    assert 0 <= result["scoring"]["overall_score"] <= 100
    assert result["review"]["decision"] == "approved"
    assert result["report_markdown"]
    assert result["privacy_report"]["email_removed"] == 1
