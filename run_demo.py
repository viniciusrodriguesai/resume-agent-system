from pathlib import Path

from pipeline import run_pipeline

BASE_DIR = Path(__file__).parent
resume_text = (BASE_DIR / "examples" / "sample_resume.txt").read_text(encoding="utf-8")
job_text = (BASE_DIR / "examples" / "sample_job.txt").read_text(encoding="utf-8")

results = run_pipeline(resume_text, job_text)

print("=== FINAL RESULT ===")
print(results["review"].data["final_answer"])
print("\n=== AGENT EXECUTION TRACE ===")
for stage, result in results.items():
    print(f"{stage}: {result.agent_name} -> {result.summary}")
