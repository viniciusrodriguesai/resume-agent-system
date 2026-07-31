from __future__ import annotations
from agents import CoordinatorAgent

def run_pipeline(resume_text: str, job_text: str, strictness: str = "Balanced"):
    return CoordinatorAgent().run(
        resume_text=resume_text,
        job_text=job_text,
        strictness=strictness,
    )
