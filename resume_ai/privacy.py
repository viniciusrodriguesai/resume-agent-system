from __future__ import annotations

import re
from typing import Dict, Tuple

SENSITIVE_LINE_MARKERS = [
    "date of birth", "birth date", "birthday", "data de nascimento",
    "marital status", "estado civil", "nationality", "nacionalidade",
    "gender", "sexo", "religion", "religiao",
]

def anonymize_resume(text: str) -> Tuple[str, Dict[str, object]]:
    value = text or ""
    report = {
        "email_removed": 0,
        "phone_removed": 0,
        "url_removed": 0,
        "sensitive_lines_removed": 0,
        "name_line_removed": False,
    }

    value, report["email_removed"] = re.subn(
        r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
        "[EMAIL REMOVED]",
        value,
    )
    value, report["phone_removed"] = re.subn(
        r"(?:\+?\d{1,3}\s*)?(?:\(?\d{2,3}\)?\s*)?\d{4,5}[-\s]?\d{4}",
        "[PHONE REMOVED]",
        value,
    )
    value, report["url_removed"] = re.subn(
        r"https?://\S+|www\.\S+",
        "[URL REMOVED]",
        value,
        flags=re.IGNORECASE,
    )

    filtered = []
    nonempty_seen = 0
    for line in value.splitlines():
        stripped = line.strip()
        lower = stripped.lower()

        if stripped:
            nonempty_seen += 1

        if any(marker in lower for marker in SENSITIVE_LINE_MARKERS):
            report["sensitive_lines_removed"] += 1
            continue

        if (
            nonempty_seen == 1
            and stripped
            and len(stripped.split()) <= 6
            and not re.search(r"\d|@|:|\b(summary|resume|curriculum|cv)\b", lower)
        ):
            filtered.append("[NAME REMOVED]")
            report["name_line_removed"] = True
            continue

        filtered.append(line)

    return "\n".join(filtered), report
