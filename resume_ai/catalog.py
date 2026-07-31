from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .config import Settings
from .text import normalize, phrase_present


BUILTIN_SKILLS: Dict[str, List[str]] = {
    "python": ["python", "python3"],
    "sql": ["sql", "structured query language"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "r programming": ["r programming", "r language"],
    "machine learning": ["machine learning", "predictive modeling", "predictive analytics", "ml models"],
    "deep learning": ["deep learning", "neural networks", "neural network"],
    "artificial intelligence": ["artificial intelligence", "ai systems"],
    "data analysis": ["data analysis", "data analytics", "analyze data", "analise de dados"],
    "statistics": ["statistics", "statistical analysis", "estatistica"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "keras"],
    "power bi": ["power bi", "powerbi", "business intelligence dashboards"],
    "tableau": ["tableau"],
    "matplotlib": ["matplotlib"],
    "data visualization": ["data visualization", "visual analytics", "dashboards", "visualizacao de dados"],
    "data engineering": ["data engineering", "engenharia de dados"],
    "etl": ["etl", "extract transform load"],
    "api development": ["api development", "apis", "application programming interface"],
    "rest api": ["rest api", "restful api", "web services", "rest services"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo db"],
    "database": ["database", "databases", "relational database", "banco de dados"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "google cloud": ["gcp", "google cloud platform", "google cloud"],
    "docker": ["docker", "containers", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "linux": ["linux"],
    "git": ["git", "version control", "controle de versao"],
    "github": ["github"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous delivery"],
    "communication": ["communication", "communicate", "presentation skills", "comunicacao"],
    "teamwork": ["teamwork", "team work", "collaboration", "worked with a team", "trabalho em equipe"],
    "leadership": ["leadership", "led a team", "team leader", "lideranca"],
    "problem solving": ["problem solving", "problem-solving", "solve problems", "resolucao de problemas"],
    "organization": ["organization", "organized", "time management", "organizacao"],
    "proactivity": ["proactivity", "proactive", "initiative", "proatividade"],
    "english": ["english", "ingles"],
    "portuguese": ["portuguese", "portugues"],
    "spanish": ["spanish", "espanhol"],
}

@dataclass(frozen=True)
class Skill:
    label: str
    aliases: List[str]
    source: str = "builtin"
    uri: str = ""

class SkillCatalog:
    """Local skill catalog with optional ESCO CSV/SQLite enrichment."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.ensure()
        self._skills: Dict[str, Skill] = {
            label: Skill(label=label, aliases=aliases, source="builtin")
            for label, aliases in BUILTIN_SKILLS.items()
        }
        self._load_sample_csv()
        self._load_sqlite()

    def _load_sample_csv(self) -> None:
        sample = self.settings.data_dir / "esco_sample_skills.csv"
        if not sample.exists():
            return
        with sample.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                label = (row.get("preferred_label") or "").strip()
                if not label:
                    continue
                aliases = [
                    value.strip()
                    for value in (row.get("alternative_labels") or "").split("|")
                    if value.strip()
                ]
                aliases = list(dict.fromkeys([label, *aliases]))
                self._skills[normalize(label)] = Skill(
                    label=label,
                    aliases=aliases,
                    source="esco-sample",
                    uri=(row.get("concept_uri") or "").strip(),
                )

    def _load_sqlite(self) -> None:
        if not self.settings.esco_db.exists():
            return
        try:
            with sqlite3.connect(self.settings.esco_db) as connection:
                rows = connection.execute(
                    "SELECT preferred_label, alternative_labels, concept_uri FROM skills"
                ).fetchall()
            for label, aliases_text, uri in rows:
                aliases = [a for a in (aliases_text or "").split("|") if a]
                self._skills[normalize(label)] = Skill(
                    label=label,
                    aliases=list(dict.fromkeys([label, *aliases])),
                    source="esco",
                    uri=uri or "",
                )
        except sqlite3.Error:
            return

    @property
    def size(self) -> int:
        return len(self._skills)

    def skills(self) -> List[Skill]:
        return list(self._skills.values())

    def find_in_text(self, text: str) -> List[Dict[str, object]]:
        matches: List[Dict[str, object]] = []
        for skill in self._skills.values():
            matched_aliases = [
                alias for alias in skill.aliases
                if phrase_present(text, alias)
            ]
            if matched_aliases:
                matches.append(
                    {
                        "label": skill.label,
                        "aliases": skill.aliases,
                        "matched_aliases": matched_aliases,
                        "source": skill.source,
                        "uri": skill.uri,
                    }
                )
        return matches

    def aliases_for(self, label: str) -> List[str]:
        item = self._skills.get(normalize(label))
        return item.aliases if item else [label]
