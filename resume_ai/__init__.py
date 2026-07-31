"""Resume Match AI V5 — análise local, explicável e orientada à privacidade."""

from .application.analyze_resume import ResumeAnalysisService
from .settings import Settings

__all__ = ["ResumeAnalysisService", "Settings"]
__version__ = "5.0.0"
