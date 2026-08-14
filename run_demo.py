from pathlib import Path

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest
from resume_ai.settings import Settings


def main() -> None:
    base = Path(__file__).resolve().parent
    resume = (base / "examples" / "curriculo_exemplo.txt").read_text(encoding="utf-8")
    job = (base / "examples" / "vaga_exemplo.txt").read_text(encoding="utf-8")
    settings = Settings.for_profile("demo").model_copy(
        update={"embedding_enabled": False, "history_enabled": False}
    )
    result = ResumeAnalysisService(settings).analyze(
        AnalysisRequest(resume_text=resume, job_text=job)
    )
    print(result.review_summary)
    print(result.markdown_report)


if __name__ == "__main__":
    main()
