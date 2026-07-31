from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter

STOPWORDS = {
    "a", "as", "ao", "aos", "com", "da", "das", "de", "do", "dos", "e", "em",
    "entre", "é", "o", "os", "ou", "para", "por", "que", "se", "um", "uma",
    "the", "and", "of", "to", "in", "for", "with", "is", "are",
}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    value = re.sub(r"[^a-z0-9+#./\-\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#]+", normalize(text)) if len(t) > 1 and t not in STOPWORDS]


def split_chunks(text: str, max_chars: int = 900) -> list[str]:
    chunks: list[str] = []
    current = ""
    for raw_line in (text or "").splitlines():
        line = re.sub(r"^[\s•*\-–—\d.)]+", "", raw_line).strip()
        if not line:
            continue
        parts = re.split(r"(?<=[.!?;:])\s+", line)
        for part in parts:
            part = part.strip()
            if len(part) < 3:
                continue
            if current and len(current) + len(part) + 1 > max_chars:
                chunks.append(current)
                current = part
            else:
                current = f"{current} {part}".strip()
    if current:
        chunks.append(current)
    return chunks


def tfidf_similarity(a: str, b: str) -> float:
    docs = [tokenize(a), tokenize(b)]
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    idf = {token: math.log(3 / (1 + freq)) + 1 for token, freq in df.items()}
    vectors = []
    for doc in docs:
        counts = Counter(doc)
        total = max(len(doc), 1)
        vectors.append({token: (count / total) * idf[token] for token, count in counts.items()})
    va, vb = vectors
    if not va or not vb:
        return 0.0
    product = sum(value * vb.get(token, 0.0) for token, value in va.items())
    na = math.sqrt(sum(value * value for value in va.values()))
    nb = math.sqrt(sum(value * value for value in vb.values()))
    return product / (na * nb) if na and nb else 0.0


def exact_phrase(text: str, phrase: str) -> bool:
    normalized = normalize(phrase)
    return bool(normalized and f" {normalized} " in f" {normalize(text)} ")


def content_hash(*parts: str) -> str:
    joined = "\0".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(joined).hexdigest()
