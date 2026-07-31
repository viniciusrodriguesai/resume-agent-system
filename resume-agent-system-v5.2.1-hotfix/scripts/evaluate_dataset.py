from __future__ import annotations

import argparse
import csv
from pathlib import Path

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings

parser = argparse.ArgumentParser()
parser.add_argument("dataset", type=Path)
parser.add_argument("--profile", default="demo", choices=["demo", "balanced", "complete"])
args = parser.parse_args()
service = ResumeAnalysisService(Settings.for_profile(args.profile))
rows = list(csv.DictReader(args.dataset.open(encoding="utf-8")))
correct = 0
for row in rows:
    result = service.analyze(AnalysisRequest(resume_text=row["resume"], job_text=row["job"], profile=args.profile))
    predicted = "1" if result.score.overall_score >= 60 else "0"
    correct += predicted == row["label"]
print(f"Acurácia simples: {correct / max(len(rows), 1):.3f} ({correct}/{len(rows)})")
