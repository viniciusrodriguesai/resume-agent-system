from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter

from resume_ai.domain.concepts import EvidenceContext, RequirementIntent

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


def _phrase_contexts(text: str, phrase: str) -> list[tuple[str, str]]:
    normalized_phrase = normalize(phrase)
    if not normalized_phrase:
        return []
    pattern = rf"(?<![a-z0-9+#]){re.escape(normalized_phrase)}(?![a-z0-9+#])"
    segments = re.split(
        r"(?<=[!?;])\s*|(?<=\.)\s+|[\r\n]+|\s+[â€¢*â€“â€”]\s+",
        text or "",
    )
    contexts: list[tuple[str, str]] = []
    for segment in segments:
        normalized_segment = normalize(segment)
        for match in re.finditer(pattern, normalized_segment):
            contexts.append((
                normalized_segment[max(0, match.start() - 60) : match.start()],
                normalized_segment[match.end() : match.end() + 60],
            ))
    return contexts


def _is_negated_context(context: tuple[str, str]) -> bool:
    before, after = context
    negation = re.compile(
        r"(?:\bsem|\bnao|\bnunca|\bjamais|\bnot|\bwithout|\bnever|\bnenhum(?:a)?|"
        r"\bno\s+(?:[a-z0-9+#./-]+\s+){0,2}experience\s+(?:with|in))"
        r"\s+(?:[a-z0-9+#./-]+\s+){0,3}$"
    )
    no_concept_experience = re.search(r"\bno\s+$", before) and re.match(
        r"\s+(?:professional\s+)?experience\b",
        after,
    )
    explicit_lack_of_experience = re.search(
        r"\b(?:nao\s+tenho|nao\s+possuo|sem|no)\s+"
        r"(?:experiencia|experience)\s+(?:profissional\s+)?"
        r"(?:com|em|with|in)\s+(?:[a-z0-9+#./-]+\s+){0,3}$",
        before,
    )
    return (
        negation.search(before) is not None
        or no_concept_experience is not None
        or explicit_lack_of_experience is not None
    )


def exact_phrase(text: str, phrase: str) -> bool:
    return any(not _is_negated_context(context) for context in _phrase_contexts(text, phrase))


def negated_phrase(text: str, phrase: str) -> bool:
    """Return true when every occurrence of a phrase is explicitly negated."""
    contexts = _phrase_contexts(text, phrase)
    return bool(contexts) and all(_is_negated_context(context) for context in contexts)


def superficial_phrase(text: str, phrase: str) -> bool:
    """Return true when every occurrence only describes reading about a concept."""
    contexts = _phrase_contexts(text, phrase)
    superficial = re.compile(
        r"(?:\bli|\bleu|\blido|\bread|\breading)\s+"
        r"(?:(?:apenas|somente|only)\s+)?"
        r"(?:(?:(?:diversos?|varios?|alguns?|many|several)\s+)?"
        r"(?:artigos?|articles?|tutoriais?|tutorials?|documentacao|documentation)"
        r"(?:\s+(?:e|and)\s+"
        r"(?:artigos?|articles?|tutoriais?|tutorials?|documentacao|documentation))?\s+)?"
        r"(?:sobre|about)\s+$"
    )
    positive_contexts = [context for context in contexts if not _is_negated_context(context)]
    return bool(positive_contexts) and all(
        superficial.search(before) is not None
        for before, _ in positive_contexts
    )


def requirement_demands_experience(text: str) -> bool:
    """Return true when the requirement asks for applied experience."""
    return requirement_intent(text) is not RequirementIntent.KNOWLEDGE


def requirement_intent(text: str) -> RequirementIntent:
    """Classify how strong the context around a cited concept must be."""
    normalized = normalize(text)
    if re.search(r"\b(?:experiencia|experience)\b", normalized) is None:
        return RequirementIntent.KNOWLEDGE
    if re.search(r"\b(?:producao|production)\b", normalized):
        return RequirementIntent.PRODUCTION_EXPERIENCE
    if re.search(r"\b(?:profissional|professional)\b", normalized):
        return RequirementIntent.PROFESSIONAL_EXPERIENCE
    return RequirementIntent.EXPERIENCE


def weak_experience_phrase(text: str, phrase: str) -> bool:
    """Return true when every occurrence is framed as basic or theoretical learning."""
    contexts = _phrase_contexts(text, phrase)
    weak = re.compile(
        r"(?:\bconhecimento\s+(?:basico|teorico)|"
        r"\b(?:tenho|possuo)\s+nocoes|\bnocoes|"
        r"\bestudei(?:\s+(?:conceitos?|fundamentos?))?|"
        r"\bstudied(?:\s+(?:concepts?|fundamentals?))?|"
        r"\bli(?:\s+sobre)?|\bread(?:ing)?(?:\s+about)?|"
        r"\bcurso\s+(?:introdutorio|basico)|"
        r"\b(?:basic|theoretical)\s+knowledge|\bintroductory\s+course)"
        r"(?:\s+(?:de|em|sobre|of|in|about))?\s+$"
    )
    positive_contexts = [context for context in contexts if not _is_negated_context(context)]
    return bool(positive_contexts) and all(
        weak.search(before) is not None
        for before, _ in positive_contexts
    )


def operational_experience_phrase(text: str, phrase: str) -> bool:
    """Return true when a local concept mention includes applied-work context."""
    operational = re.compile(
        r"\b(?:uso|utilizo|implemento|desenvolvo|crio|opero|configuro|mantenho|"
        r"modelo|otimizo|trabalho|administro|construo|"
        r"usei|utilizei|implementei|desenvolvi|criei|operei|configurei|"
        r"mantive|modelei|otimizei|trabalhei|administrei|construi|"
        r"automatizo|automatizei|escrevo|escrevi|"
        r"projeto|project|"
        r"use|implement|develop|build|operate|configure|maintain|deploy|"
        r"used|implemented|developed|built|operated|configured|maintained|deployed|"
        r"automate|automated|write|wrote|"
        r"experiencia\s+profissional|professional\s+experience|producao|production)\b"
    )
    return any(
        operational.search(f"{before} {after}") is not None
        for before, after in _phrase_contexts(text, phrase)
    )


def evidence_context(text: str, phrase: str) -> EvidenceContext:
    """Classify the context of positive concept mentions independently of intent."""
    personal = re.compile(
        r"\b(?:(?:projetos?|aplicac(?:ao|oes)|apis?|sistemas?)\s+pesso(?:al|ais)|"
        r"personal\s+(?:projects?|applications?|apis?|systems?))\b"
    )
    academic = re.compile(
        r"\b(?:academico|academica|faculdade|universidade|laboratorio|curso|"
        r"hackathon|estudo|academic|college|university|laboratory|course|study)\b"
    )
    production = re.compile(
        r"\b(?:em\s+producao|de\s+producao|ambiente\s+produtivo|"
        r"sistema\s+produtivo|servico\s+em\s+producao|production|"
        r"deployed\s+to\s+production)\b"
    )
    professional = re.compile(
        r"\b(?:experiencia\s+profissional|professional\s+experience|"
        r"profissionalmente|professionally|emprego|employment|empresa|company|"
        r"clientes?|clients?|no\s+trabalho|at\s+work|na\s+empresa|cargo|role)\b"
    )
    non_production = re.compile(
        r"\b(?:localmente|cluster\s+local|ambiente\s+local|staging|"
        r"desenvolvimento|development)\b"
    )

    has_personal = False
    has_academic = False
    has_professional = False
    has_production = False
    for context in _phrase_contexts(text, phrase):
        if _is_negated_context(context):
            continue
        local_context = f"{context[0]} {context[1]}"
        personal_here = personal.search(local_context) is not None
        academic_here = academic.search(local_context) is not None
        production_here = production.search(local_context) is not None
        has_personal = has_personal or personal_here
        has_academic = has_academic or academic_here
        has_professional = has_professional or (
            not personal_here
            and not academic_here
            and (
                professional.search(local_context) is not None
                or production_here
            )
        )
        has_production = has_production or (
            production_here
            and not personal_here
            and not academic_here
            and non_production.search(local_context) is None
        )
    return EvidenceContext(
        professional_experience=has_professional,
        production_experience=has_production,
        personal_project_context=has_personal,
        academic_context=has_academic,
    )


def production_experience_phrase(text: str, phrase: str) -> bool:
    """Return true when a positive concept mention is explicitly tied to production."""
    return evidence_context(text, phrase).production_experience


def high_volume_request_requirement(text: str) -> bool:
    normalized = normalize(text)
    volume = "alto volume" in normalized or "high volume" in normalized
    requests = re.search(r"\b(?:requisicoes|requests?)\b", normalized) is not None
    return volume and requests


def quantified_request_volume(text: str) -> bool:
    """Detect a non-trivial request count without declaring it universally high volume."""
    normalized = normalize(text)
    pattern = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*"
        r"(milhoes?|milhao|mil|millions?|thousand|[km])?\s+"
        r"(?:de\s+)?(?:requisicoes|requests?)\b"
    )
    match = pattern.search(normalized)
    if match is None:
        return False
    value = float(match.group(1).replace(",", "."))
    multiplier = {
        "mil": 1_000,
        "thousand": 1_000,
        "k": 1_000,
        "milhao": 1_000_000,
        "milhoes": 1_000_000,
        "million": 1_000_000,
        "millions": 1_000_000,
        "m": 1_000_000,
    }.get(match.group(2) or "", 1)
    return value * multiplier >= 1_000


def content_hash(*parts: str) -> str:
    joined = "\0".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(joined).hexdigest()
