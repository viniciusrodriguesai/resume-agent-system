"""Resume Match AI V5.1 — análise local, explicável e orientada à privacidade."""

__version__ = "5.1.0"

from .application.analyze_resume import ResumeAnalysisService
from .settings import Settings

__all__ = ["ResumeAnalysisService", "Settings"]
