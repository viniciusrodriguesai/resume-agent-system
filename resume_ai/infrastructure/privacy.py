from __future__ import annotations

import re
from collections import Counter

from resume_ai.domain.models import PrivacyEntity, PrivacyReport
from resume_ai.settings import Settings

PATTERNS = {
    "EMAIL": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "CNPJ": r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
    "CEP": r"\b\d{5}-?\d{3}\b",
    "TELEFONE": r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}",
    "URL": r"https?://\S+|www\.\S+",
}


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

        lines = output.splitlines()
        for index, line in enumerate(lines[:4]):
            value = line.strip()
            if value and len(value.split()) <= 6 and not re.search(r"[@\d:<>]", value):
                counts["NOME_CANDIDATO"] += 1
                lines[index] = "<NOME_CANDIDATO>"
                break
        output = "\n".join(lines)
        entities = [
            PrivacyEntity(entity_type=kind, replacement=f"<{kind}>", count=count)
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
        except Exception:
            return None
        try:
            analyzer = AnalyzerEngine()
            for entity_type in ("BR_CPF", "BR_CNPJ", "BR_CEP"):
                key = entity_type.replace("BR_", "")
                analyzer.registry.add_recognizer(
                    PatternRecognizer(
                        supported_entity=entity_type,
                        patterns=[Pattern(name=key.lower(), regex=PATTERNS[key], score=0.85)],
                    )
                )
            results = analyzer.analyze(text=text, language="en")
            anonymized = AnonymizerEngine().anonymize(text=text, analyzer_results=results).text
            counts = Counter(item.entity_type for item in results)
            entities = [
                PrivacyEntity(entity_type=kind, replacement=f"<{kind}>", count=count)
                for kind, count in counts.items()
            ]
            return anonymized, PrivacyReport(
                method="Microsoft Presidio + reconhecedores pt-BR",
                entities=entities,
                total_removed=sum(counts.values()),
                raw_document_stored=self.settings.store_raw_documents,
                anonymized_document_stored=self.settings.store_anonymized_documents,
            )
        except Exception:
            return None
