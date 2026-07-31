from __future__ import annotations
from collections import defaultdict
from typing import Dict, List

class ScoringService:
    PRIORITY_WEIGHTS = {"required": 1.0, "desirable": 0.45, "neutral": 0.20}
    STATUS_VALUES = {"matched": 1.0, "partial": 0.55, "missing": 0.0}
    CATEGORY_DISPLAY = {
        "programming":"Programming","data_and_ai":"Data and AI",
        "backend_and_databases":"Backend and Databases",
        "cloud_and_devops":"Cloud and DevOps","soft_skills":"Soft Skills",
        "languages":"Languages","experience":"Experience",
        "education":"Education","general":"General",
    }

    def calculate(self, matches: List[Dict[str, object]]) -> Dict[str, object]:
        total = earned = 0.0
        ct, ce = defaultdict(float), defaultdict(float)
        required_count = missing_required = 0
        for item in matches:
            priority = str(item.get("priority", "neutral"))
            status = str(item.get("status", "missing"))
            category = str(item.get("category", "general"))
            weight = self.PRIORITY_WEIGHTS.get(priority, 0.2)
            value = self.STATUS_VALUES.get(status, 0.0)
            total += weight
            earned += weight * value
            ct[category] += weight
            ce[category] += weight * value
            if priority == "required":
                required_count += 1
                missing_required += status == "missing"
        overall = round((earned / total) * 100) if total else 0
        if required_count and missing_required:
            ratio = missing_required / required_count
            if ratio >= .5:
                overall = min(overall, 55)
            elif ratio >= .25:
                overall = min(overall, 72)
        categories = {self.CATEGORY_DISPLAY.get(c, c.title()): round(ce[c] / t * 100) for c, t in ct.items() if t}
        level = "high" if overall >= 82 else "medium" if overall >= 62 else "low"
        return {
            "overall_score": max(0, min(overall, 100)),
            "level": level,
            "category_scores": categories,
            "required_count": required_count,
            "missing_required_count": int(missing_required),
        }
