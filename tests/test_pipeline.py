from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline import run_pipeline

def test_pipeline_returns_expected_agents():
    resume = """
    Alex Example
    alex@example.com
    Data Science student.
    Skills: Python, SQL, Pandas, Machine Learning, Git.
    Developed a Power BI dashboard and a classification model.
    """
    job = """
    Data Science Intern
    Required: Python, SQL, Pandas, Machine Learning, and Git.
    Preferred: AWS and Docker.
    The intern will analyze data and build predictive models.
    """
    results = run_pipeline(resume, job)
    expected = {
        "coordinator", "resume", "job", "experience",
        "matching", "recommendation", "review", "report",
    }
    assert expected.issubset(results.keys())
    assert 0 <= results["matching"].data["overall_score"] <= 100
    assert results["review"].data["decision"] == "approved"
    assert results["report"].data["markdown_report"]

def test_missing_required_skill_reduces_score():
    resume = "Student with communication and teamwork skills."
    job = "Required: Python, SQL, Docker, AWS, and Machine Learning."
    results = run_pipeline(resume, job)
    assert results["matching"].data["missing_required_count"] >= 1
    assert results["matching"].data["overall_score"] <= 72
