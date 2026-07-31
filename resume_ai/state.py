from __future__ import annotations
import operator
from typing import Annotated, Any, Dict, List, TypedDict

class AnalysisState(TypedDict, total=False):
    analysis_id: str
    resume_text: str
    job_text: str
    anonymized_resume_text: str
    anonymized_job_text: str
    privacy_report: Dict[str, Any]
    resume_profile: Dict[str, Any]
    job_profile: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    scoring: Dict[str, Any]
    review: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    report_markdown: str
    report_json: str
    strictness: str
    revision_count: int
    max_revisions: int
    engine_status: Dict[str, Any]
    trace: Annotated[List[Dict[str, Any]], operator.add]
