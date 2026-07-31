from __future__ import annotations
import math
import re
import unicodedata
from collections import Counter
from typing import Iterable, List

STOPWORDS = {
    "a","an","and","are","as","at","be","by","da","das","de","do","dos","e","em",
    "for","from","has","have","in","is","it","o","of","on","or","os","para","por",
    "que","the","this","to","um","uma","using","we","with","you","your",
}

def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z0-9+#./\-\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def split_units(text: str, min_length: int = 3) -> List[str]:
    units: List[str] = []
    for raw in (text or "").splitlines():
        line = re.sub(r"^[\s•*\-–—\d.)]+", "", raw).strip()
        if not line:
            continue
        for part in re.split(r"(?<=[.!?;])\s+", line):
            part = part.strip()
            if len(part) >= min_length:
                units.append(part)
    return units

def tokens(text: str) -> List[str]:
    return [
        token for token in re.findall(r"[a-z0-9+#]+", normalize(text))
        if len(token) > 1 and token not in STOPWORDS
    ]

def lexical_similarity(first: str, second: str) -> float:
    docs = [tokens(first), tokens(second)]
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    idf = {t: math.log(3 / (1 + f)) + 1 for t, f in df.items()}
    vectors = []
    for doc in docs:
        counts = Counter(doc)
        total = max(len(doc), 1)
        vectors.append({t: (c / total) * idf[t] for t, c in counts.items()})
    a, b = vectors
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(t, 0.0) for t, v in a.items())
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

def phrase_present(text: str, phrase: str) -> bool:
    p = normalize(phrase)
    return bool(p and f" {p} " in f" {normalize(text)} ")

def contains_any(text: str, markers: Iterable[str]) -> bool:
    value = normalize(text)
    return any(normalize(marker) in value for marker in markers)
