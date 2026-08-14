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

PRIVACY_PLACEHOLDER_RE = re.compile(r"<[A-ZÀ-Ú0-9_ -]+>")
CONTACT_LABEL_RE = re.compile(
    r"\b(?:e-?mail|telefone|celular|whatsapp|cpf|cnpj|cep|linkedin|github)\s*:\s*",
    flags=re.IGNORECASE,
)


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    value = re.sub(r"[^a-z0-9+#./\-\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#]+", normalize(text)) if len(t) > 1 and t not in STOPWORDS]


def remove_privacy_placeholders(text: str) -> str:
    """Remove marcadores técnicos sem destruir as quebras de linha do documento."""
    value = PRIVACY_PLACEHOLDER_RE.sub("", text or "")
    value = CONTACT_LABEL_RE.sub("", value)
    value = re.sub(r"[ \t]+([,.;:])", r"\1", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    return value.strip(" \t\r\n-–—|,;:")


def _is_heading(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    return len(text.split()) <= 8 and sum(char.isupper() for char in letters) / len(letters) >= 0.88


def split_chunks(text: str, max_chars: int = 420) -> list[str]:
    """Cria trechos curtos e específicos, preservando uma linha/bullet por evidência.

    A versão anterior acumulava quase o currículo inteiro em poucos blocos. Isso
    aumentava o tempo de embeddings e fazia uma evidência genérica receber nota alta.
    """
    chunks: list[str] = []
    seen: set[str] = set()

    for raw_line in (text or "").splitlines():
        line = re.sub(r"^[\s•*\-–—\d.)]+", "", raw_line).strip()
        line = remove_privacy_placeholders(line)
        if len(line) < 3 or _is_heading(line):
            continue

        sentence_parts = [line]
        if len(line) > max_chars:
            sentence_parts = [
                part.strip()
                for part in re.split(r"(?<=[.!?;:])\s+", line)
                if part.strip()
            ]

        fragments: list[str] = []
        current = ""
        for part in sentence_parts:
            if len(part) > max_chars:
                words = part.split()
                for word in words:
                    if current and len(current) + len(word) + 1 > max_chars:
                        fragments.append(current)
                        current = word
                    else:
                        current = f"{current} {word}".strip()
                if current:
                    fragments.append(current)
                    current = ""
            elif current and len(current) + len(part) + 1 > max_chars:
                fragments.append(current)
                current = part
            else:
                current = f"{current} {part}".strip()
        if current:
            fragments.append(current)

        for fragment in fragments:
            key = normalize(fragment)
            if key and key not in seen:
                chunks.append(fragment)
                seen.add(key)

    return chunks


def best_snippet(text: str, query: str, max_chars: int = 360) -> str:
    """Seleciona o trecho mais relacionado ao requisito e limita o tamanho visual."""
    clean = remove_privacy_placeholders(text)
    if len(clean) <= max_chars:
        return clean

    query_tokens = set(tokenize(query))
    parts = [part.strip() for part in re.split(r"(?<=[.!?;:])\s+|\s+[|•]\s+", clean) if part.strip()]
    if not parts:
        return clean[: max_chars - 1].rstrip() + "…"

    def score(part: str) -> tuple[float, int]:
        tokens = set(tokenize(part))
        overlap = len(tokens & query_tokens) / max(len(query_tokens), 1)
        return overlap, -len(part)

    selected = max(parts, key=score)
    return selected if len(selected) <= max_chars else selected[: max_chars - 1].rstrip() + "…"


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


def _phrase_contexts(text: str, phrase: str) -> list[str]:
    normalized_phrase = normalize(phrase)
    normalized_text = normalize(text)
    if not normalized_phrase or not normalized_text:
        return []
    pattern = rf"(?<![a-z0-9+#]){re.escape(normalized_phrase)}(?![a-z0-9+#])"
    return [
        normalized_text[max(0, match.start() - 60) : match.start()]
        for match in re.finditer(pattern, normalized_text)
    ]


def _is_negated_context(context: str) -> bool:
    negation = re.compile(
        r"(?:\bsem|\bnao|\bnot|\bwithout|\bnever|\bnenhum(?:a)?|"
        r"\bno experience (?:with|in))\s+(?:[a-z0-9+#./-]+\s+){0,3}$"
    )
    return negation.search(context) is not None


def exact_phrase(text: str, phrase: str) -> bool:
    return any(not _is_negated_context(context) for context in _phrase_contexts(text, phrase))


def negated_phrase(text: str, phrase: str) -> bool:
    """Return true when every occurrence of a phrase is explicitly negated."""
    contexts = _phrase_contexts(text, phrase)
    return bool(contexts) and all(_is_negated_context(context) for context in contexts)


def content_hash(*parts: str) -> str:
    joined = "\0".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(joined).hexdigest()
