from __future__ import annotations

import re
from collections import Counter
from copy import copy
from typing import Any

from resume_ai.domain.models import PrivacyEntity, PrivacyReport
from resume_ai.settings import Settings
from resume_ai.utils.text import normalize

PATTERNS = {
    "NOME_CANDIDATO": r"(?im)^(?:nome(?:\s+completo)?|full\s+name|name)\s*:\s*[^\n]+$",
    "EMAIL": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "CNPJ": r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
    "CEP": r"\b\d{5}-?\d{3}\b",
    "TELEFONE": r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}",
    "URL": r"https?://\S+|www\.\S+",
    "RG": r"\b(?:RG\s*[:#-]?\s*)?\d{1,2}\.?\d{3}\.?\d{3}-?[\dX]\b",
    "NASCIMENTO": r"(?im)^(?:data\s+de\s+nascimento|nascimento|date\s+of\s+birth|dob)\s*:?\s*[^\n]+$",
    "ENDERECO": r"(?im)^(?:(?:endere[cç]o)\s*:?\s*)?(?:rua|avenida|av\.?|alameda|travessa|rodovia|estrada)\s+[^\n]+$",
    "SOCIAL_HANDLE": r"(?im)^(?:linkedin|github|telegram|instagram)\s*:\s*[^\n]+$",
}

_RESUME_HEADINGS = {"curriculo", "curriculum vitae", "resume", "cv"}
_TECHNICAL_CONTEXT_WORDS = {
    "administro",
    "artigos",
    "com",
    "configurei",
    "conhecimento",
    "desenvolvi",
    "experiencia",
    "implementei",
    "li",
    "monitoramento",
    "nao",
    "nunca",
    "operei",
    "producao",
    "sobre",
    "tested",
    "testei",
    "trabalhei",
    "utilizei",
    "utilizo",
}


def _technical_spans(text: str) -> list[tuple[int, int]]:
    from resume_ai.agents.catalog import SKILLS

    terms = {
        value
        for canonical, (_, aliases) in SKILLS.items()
        for value in (canonical, *aliases)
        if value
    }
    spans = {
        match.span()
        for term in terms
        for match in re.finditer(
            rf"(?<![\w+#]){re.escape(term)}(?![\w+#])",
            text,
            flags=re.IGNORECASE,
        )
    }
    spans.update(
        match.span()
        for match in re.finditer(
            r"\b[A-Z][A-Za-z0-9]*(?:API|Cache|DB|JS|ML|MQ|SQL)\b",
            text,
        )
    )
    return sorted(spans)


def _looks_like_person_name_line(value: str) -> bool:
    if not value or re.search(r"[@\d:<>]", value):
        return False
    if re.fullmatch(r"[A-Z0-9_]+(?:-[A-Z0-9_]+)+", value):
        return False
    normalized_words = set(normalize(value).split())
    if normalized_words & _TECHNICAL_CONTEXT_WORDS:
        return False
    words = re.findall(r"[^\W\d_]+(?:['’-][^\W\d_]+)?", value, flags=re.UNICODE)
    if not 2 <= len(words) <= 6:
        return False
    connectors = {"da", "das", "de", "do", "dos", "e"}
    if not all(word.lower() in connectors or word[0].isupper() for word in words):
        return False
    return len(_technical_spans(value)) < 2


def _probable_person_name_spans(value: str, offset: int) -> list[tuple[int, int]]:
    """Find title-cased name sequences inside a broader Presidio PERSON span."""
    word_matches = list(
        re.finditer(r"[^\W\d_]+(?:['â€™-][^\W\d_]+)?", value, flags=re.UNICODE)
    )
    connectors = {"da", "das", "de", "do", "dos", "e"}
    sequences: list[list[re.Match[str]]] = []
    current: list[re.Match[str]] = []
    for word_match in word_matches:
        word = word_match.group()
        if word[0].isupper() or (current and word.lower() in connectors):
            current.append(word_match)
            continue
        if current:
            sequences.append(current)
            current = []
    if current:
        sequences.append(current)

    spans: list[tuple[int, int]] = []
    for sequence in sequences:
        while sequence and sequence[-1].group().lower() in connectors:
            sequence.pop()
        if len(sequence) < 2:
            continue
        start = sequence[0].start()
        end = sequence[-1].end()
        if _looks_like_person_name_line(value[start:end]):
            spans.append((offset + start, offset + end))
            continue
        for fragment_start, fragment_end in _nontechnical_fragments(
            value,
            start,
            end,
            _technical_spans(value),
        ):
            if _looks_like_person_name_line(value[fragment_start:fragment_end]):
                spans.append(
                    (offset + fragment_start, offset + fragment_end)
                )
    return spans


def _nontechnical_fragments(
    text: str,
    start: int,
    end: int,
    technical_spans: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Split a PERSON span around overlapping technology spans."""
    overlaps = [
        (max(start, technical_start), min(end, technical_end))
        for technical_start, technical_end in technical_spans
        if max(start, technical_start) < min(end, technical_end)
    ]
    if not overlaps:
        return [(start, end)]

    fragments: list[tuple[int, int]] = []
    cursor = start
    for technical_start, technical_end in overlaps:
        fragment_start = cursor
        fragment_end = technical_start
        while fragment_start < fragment_end and text[fragment_start].isspace():
            fragment_start += 1
        while fragment_end > fragment_start and text[fragment_end - 1].isspace():
            fragment_end -= 1
        if fragment_start < fragment_end:
            fragments.append((fragment_start, fragment_end))
        cursor = max(cursor, technical_end)

    fragment_start = cursor
    fragment_end = end
    while fragment_start < fragment_end and text[fragment_start].isspace():
        fragment_start += 1
    while fragment_end > fragment_start and text[fragment_end - 1].isspace():
        fragment_end -= 1
    if fragment_start < fragment_end:
        fragments.append((fragment_start, fragment_end))
    return fragments


def _redact_probable_person_names(text: str) -> tuple[str, int]:
    """Anonymize detectable title-cased names without consuming technologies."""
    technical_spans = _technical_spans(text)
    person_spans = _probable_person_name_spans(text, 0)
    fragments = [
        fragment
        for start, end in person_spans
        for fragment in _nontechnical_fragments(text, start, end, technical_spans)
    ]
    output = text
    for start, end in reversed(fragments):
        output = f"{output[:start]}<NOME_CANDIDATO>{output[end:]}"
    return output, len(person_spans)


def _filter_presidio_results(text: str, results: list[Any]) -> list[Any]:
    """Drop PERSON false positives only when their spans are technical terms."""
    technical_spans = _technical_spans(text)
    filtered: list[Any] = []
    for item in results:
        if item.entity_type != "PERSON":
            filtered.append(item)
            continue
        person_value = normalize(text[item.start:item.end])
        if " " not in person_value and person_value in _TECHNICAL_CONTEXT_WORDS:
            continue
        overlapping_spans = [
            (max(item.start, technical_start), min(item.end, technical_end))
            for technical_start, technical_end in technical_spans
            if max(item.start, technical_start) < min(item.end, technical_end)
        ]
        if not overlapping_spans:
            filtered.append(item)
            continue

        probable_name_spans = _probable_person_name_spans(
            text[item.start:item.end],
            item.start,
        )
        source_spans = probable_name_spans or [(item.start, item.end)]
        for source_start, source_end in source_spans:
            for start, end in _nontechnical_fragments(
                text,
                source_start,
                source_end,
                technical_spans,
            ):
                fragment = copy(item)
                fragment.start = start
                fragment.end = end
                filtered.append(fragment)
    return filtered


def _is_probable_name_line(value: str) -> bool:
    if not value or len(value.split()) > 6 or re.search(r"[@\d:<>]", value):
        return False
    if _looks_like_person_name_line(value):
        return True
    if _technical_spans(value):
        return False
    # Import locally to keep the privacy module independent during agent package import.
    from resume_ai.agents.catalog import detect_skills

    return not detect_skills(value)


class PrivacyService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def anonymize(self, text: str) -> tuple[str, PrivacyReport]:
        if self.settings.presidio_enabled:
            result = self._presidio(text)
            if result is not None:
                return result
        return self._regex(text)

    def _regex(self, text: str) -> tuple[str, PrivacyReport]:
        output = text
        counts: Counter[str] = Counter()
        for entity_type, pattern in PATTERNS.items():
            matches = re.findall(pattern, output, flags=re.IGNORECASE)
            if matches:
                counts[entity_type] += len(matches)
                output = re.sub(pattern, f"<{entity_type}>", output, flags=re.IGNORECASE)

        output, probable_names = _redact_probable_person_names(output)
        if probable_names:
            counts["NOME_CANDIDATO"] += probable_names
        if not counts["NOME_CANDIDATO"]:
            lines = output.splitlines()
            for index, line in enumerate(lines[:4]):
                value = line.strip()
                if normalize(value) in _RESUME_HEADINGS:
                    continue
                if _is_probable_name_line(value):
                    counts["NOME_CANDIDATO"] += 1
                    lines[index] = "<NOME_CANDIDATO>"
                    break
            output = "\n".join(lines)
        entities = [
            PrivacyEntity(entity_type=kind, replacement="REMOVIDO", count=count)
            for kind, count in counts.items()
        ]
        return output, PrivacyReport(
            method="expressões regulares locais pt-BR",
            entities=entities,
            total_removed=sum(counts.values()),
            raw_document_stored=self.settings.store_raw_documents,
            anonymized_document_stored=self.settings.store_anonymized_documents,
        )

    def _presidio(self, text: str) -> tuple[str, PrivacyReport] | None:
        try:
            from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
            from presidio_anonymizer import AnonymizerEngine
            from presidio_anonymizer.entities import (
                RecognizerResult as AnonymizerRecognizerResult,
            )
        except Exception:
            return None
        try:
            baseline_text, baseline_report = self._regex(text)
            analyzer = AnalyzerEngine()
            for entity_type in ("BR_CPF", "BR_CNPJ", "BR_CEP"):
                key = entity_type.replace("BR_", "")
                analyzer.registry.add_recognizer(
                    PatternRecognizer(
                        supported_entity=entity_type,
                        patterns=[Pattern(name=key.lower(), regex=PATTERNS[key], score=0.85)],
                    )
                )
            results = analyzer.analyze(text=baseline_text, language="en")
            results = _filter_presidio_results(baseline_text, results)
            anonymizer_results = [
                AnonymizerRecognizerResult(
                    entity_type=item.entity_type,
                    start=item.start,
                    end=item.end,
                    score=item.score,
                )
                for item in results
            ]
            anonymized = AnonymizerEngine().anonymize(
                text=baseline_text,
                analyzer_results=anonymizer_results,
            ).text
            counts = Counter({item.entity_type: item.count for item in baseline_report.entities})
            counts.update(item.entity_type for item in results)
            entities = [
                PrivacyEntity(entity_type=kind, replacement="REMOVIDO", count=count)
                for kind, count in counts.items()
            ]
            return anonymized, PrivacyReport(
                method="expressoes regulares pt-BR + Microsoft Presidio",
                entities=entities,
                total_removed=sum(counts.values()),
                raw_document_stored=self.settings.store_raw_documents,
                anonymized_document_stored=self.settings.store_anonymized_documents,
            )
        except Exception:
            return None
