"""Resume Match AI V6 — análise local, explicável e orientada à privacidade."""

__version__ = "6.0.4"

from .application.analyze_resume import ResumeAnalysisService
from .settings import Settings

__all__ = ["ResumeAnalysisService", "Settings"]
