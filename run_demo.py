from pathlib import Path

from resume_ai.analyzer import MultiAgentAnalyzer

root = Path(__file__).resolve().parent
resume = (root / "examples" / "sample_resume.txt").read_text(encoding="utf-8")
job = (root / "examples" / "sample_job.txt").read_text(encoding="utf-8")

analyzer = MultiAgentAnalyzer(full_ai=False, persist_history=False)
result = analyzer.run(resume, job)

print(result["review"]["summary"])
print(result["report_markdown"])
