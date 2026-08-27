from __future__ import annotations

import re
from collections import Counter

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


def _is_probable_name_line(value: str) -> bool:
    if not value or len(value.split()) > 6 or re.search(r"[@\d:<>]", value):
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
