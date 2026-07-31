from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List

from resume_ai.config import Settings


def first_value(row: Dict[str, str], names: Iterable[str]) -> str:
    lowered = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value:
            return value.strip()
    return ""


def import_esco(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: List[tuple[str, str, str]] = []
        for row in reader:
            label = first_value(
                row,
                [
                    "preferredLabel",
                    "preferred_label",
                    "preferred label",
                    "title",
                    "label",
                ],
            )
            if not label:
                continue
            alternatives = first_value(
                row,
                [
                    "altLabels",
                    "alternative_labels",
                    "alternative labels",
                    "alternativeLabel",
                ],
            )
            uri = first_value(
                row,
                [
                    "conceptUri",
                    "concept_uri",
                    "concept uri",
                    "uri",
                ],
            )
            alternatives = alternatives.replace("\n", "|").replace(";", "|")
            rows.append((label, alternatives, uri))

    with sqlite3.connect(destination) as connection:
        connection.execute("DROP TABLE IF EXISTS skills")
        connection.execute(
            """
            CREATE TABLE skills (
                preferred_label TEXT NOT NULL,
                alternative_labels TEXT,
                concept_uri TEXT
            )
            """
        )
        connection.executemany(
            "INSERT INTO skills VALUES (?, ?, ?)",
            rows,
        )
        connection.execute(
            "CREATE INDEX idx_skills_label ON skills(preferred_label)"
        )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import an ESCO skills CSV into the local SQLite catalog."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Settings().esco_db,
    )
    args = parser.parse_args()
    count = import_esco(args.csv_path, args.output)
    print(f"Imported {count} skills into {args.output}")


if __name__ == "__main__":
    main()
