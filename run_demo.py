from pathlib import Path
from pipeline import run_pipeline

base = Path(__file__).resolve().parent
resume = (base / "examples" / "sample_resume.txt").read_text(encoding="utf-8")
job = (base / "examples" / "sample_job.txt").read_text(encoding="utf-8")
results = run_pipeline(resume, job)

print(results["coordinator"].summary)
print(results["matching"].summary)
print(results["review"].data["final_answer"])
print()
print(results["report"].data["markdown_report"])
