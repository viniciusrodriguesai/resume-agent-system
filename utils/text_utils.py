from __future__ import annotations
import math, re, unicodedata
from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple
from agents.skill_ontology import SKILL_ONTOLOGY

STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","has","have","in","is",
    "it","of","on","or","our","that","the","their","this","to","using","we","with",
    "will","you","your",
}

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def split_content_units(text: str) -> List[str]:
    units = []
    for raw_line in (text or "").splitlines():
        line = re.sub(r"^[\s•*\-–—\d.)]+", "", raw_line).strip()
        if not line:
            continue
        units.extend(p.strip() for p in re.split(r"(?<=[.!?;])\s+", line) if p.strip())
    return units

def tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9+#]+", normalize_text(text)) if len(t) > 1 and t not in STOPWORDS]

def cosine_similarity(text_a: str, text_b: str) -> float:
    docs = [tokenize(text_a), tokenize(text_b)]
    df = Counter()
    for tokens in docs:
        df.update(set(tokens))
    idf = {t: math.log(3 / (1 + f)) + 1 for t, f in df.items()}
    vectors = []
    for tokens in docs:
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        vectors.append({t: (c / total) * idf[t] for t, c in counts.items()})
    a, b = vectors
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(t, 0.0) for t, v in a.items())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

def phrase_present(text: str, phrase: str) -> bool:
    return f" {normalize_text(phrase)} " in f" {normalize_text(text)} "

def detect_skills(text: str) -> Dict[str, Dict[str, object]]:
    units = split_content_units(text)
    found = {}
    for category, skills in SKILL_ONTOLOGY.items():
        for canonical, aliases in skills.items():
            evidence = [u for u in units if any(phrase_present(u, a) for a in aliases)]
            if evidence:
                found[canonical] = {"category": category, "aliases": aliases, "evidence": evidence[:4]}
    return found

def extract_contact(text: str) -> Dict[str, str]:
    email = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text or "")
    phone = re.search(r"(?:\+?\d{1,3}\s*)?(?:\(?\d{2,3}\)?\s*)?\d{4,5}[-\s]?\d{4}", text or "")
    return {"email": email.group(0) if email else "not identified", "phone": phone.group(0) if phone else "not identified"}

def extract_name(text: str) -> str:
    for line in (text or "").splitlines():
        c = line.strip()
        if c and len(c.split()) <= 6 and not re.search(r"[@\d]", c):
            return c
    return "not identified"

def extract_job_title(text: str) -> str:
    for pattern in [r"(?:position|role|job title)\s*[:\-]\s*(.+)", r"looking for (?:an?\s+)?(.+?)(?:\.|,|$)", r"hiring (?:an?\s+)?(.+?)(?:\.|,|$)"]:
        match = re.search(pattern, text or "", flags=re.I)
        if match:
            return match.group(1).strip()
    for line in (text or "").splitlines():
        c = line.strip()
        if c and len(c.split()) <= 10:
            return c
    return "not identified"

def select_relevant_units(text: str, keywords: Iterable[str], max_items: int = 8) -> List[str]:
    keys = [normalize_text(k) for k in keywords]
    selected = []
    for unit in split_content_units(text):
        normalized = normalize_text(unit)
        if any(k in normalized for k in keys):
            selected.append(unit)
        if len(selected) >= max_items:
            break
    return selected
