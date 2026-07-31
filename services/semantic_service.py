from __future__ import annotations
from typing import Dict, List, Optional
from utils.text_utils import cosine_similarity, normalize_text, phrase_present

class SemanticService:
    def similarity(self, requirement_text: str, candidate_text: str, aliases: Optional[List[str]] = None) -> float:
        aliases = aliases or []
        if any(phrase_present(candidate_text, alias) for alias in aliases):
            return 1.0
        base = cosine_similarity(requirement_text, candidate_text)
        req = set(normalize_text(requirement_text).split())
        cand = set(normalize_text(candidate_text).split())
        overlap = len(req & cand) / len(req) if req else 0.0
        return min(1.0, base * 0.72 + overlap * 0.28)

    def best_evidence(self, requirement_text: str, candidate_units: List[str], aliases: Optional[List[str]] = None) -> Dict[str, object]:
        best_line, best_score = "", 0.0
        for unit in candidate_units:
            score = self.similarity(requirement_text, unit, aliases)
            if score > best_score:
                best_line, best_score = unit, score
        return {"evidence": best_line, "similarity": round(best_score, 3)}
