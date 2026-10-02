"""Evaluate annotated fictional resume/job pairs through the complete lexical pipeline."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resume_ai.application.analyze_resume import ResumeAnalysisService  # noqa: E402
from resume_ai.domain.models import AnalysisRequest  # noqa: E402
from resume_ai.evaluation import classification_metrics  # noqa: E402
from resume_ai.settings import Settings  # noqa: E402


def evaluate(path: Path) -> dict:
    data = json.loads(path.read_text())
    cases = data["cases"]
    if not cases or any(c.get("expected") not in {"matched", "partial", "missing"} for c in cases):
        raise ValueError("Every case needs an independently specified valid expected label")
    ids = [c['id'] for c in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("Case IDs must be unique")
    service = ResumeAnalysisService(Settings(embedding_enabled=False, reranker_enabled=False,
                                            history_enabled=False, cache_enabled=False,
                                            log_level="ERROR"))
    results = []
    for case in cases:
        result = service.analyze(AnalysisRequest(
            resume_text=case['resume'],
            job_text="Data internship\nREQUISITOS OBRIGATÓRIOS\n- " + case['requirement']))
        if len(result.matches) != 1:
            raise ValueError(f"Case {case['id']} must generate exactly one requirement")
        match = result.matches[0]
        results.append({"id": case['id'], "category": case['category'],
                        "expected": case['expected'], "predicted": match.status,
                        "correct": match.status == case['expected'],
                        "evidence": match.evidence, "score": match.final_score})
    summary = classification_metrics([c['expected'] for c in results], [c['predicted'] for c in results])
    categories = sorted({c['category'] for c in results})
    return {"dataset_name": data['name'], "annotation_origin": data['annotation_origin'],
            "total": len(results), **summary,
            "by_category": {category: classification_metrics(
                [c['expected'] for c in results if c['category'] == category],
                [c['predicted'] for c in results if c['category'] == category]) for category in categories},
            "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "source_commit": subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            "python": platform.python_version(), "cases": results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.cases)
    with args.output.open('x') as output:
        json.dump(report, output, indent=2, ensure_ascii=False, allow_nan=False)
        output.write('\n')
    print(json.dumps({k: report[k] for k in ('total', 'accuracy', 'macro_f1')}))
