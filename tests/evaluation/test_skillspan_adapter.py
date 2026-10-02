import importlib.util
import sys
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("skillspan_evaluation", Path(__file__).resolve().parents[2] / "scripts/evaluate_skillspan.py")
assert spec is not None and spec.loader is not None
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)


def test_catalog_mentions_use_minimal_windows_and_do_not_match_substrings() -> None:
    assert adapter.predicted_tokens(["(", "Python", ")", "and", "JavaScript", "with", "Docker"]) == {1, 6}
    assert adapter.predicted_tokens(["No", "experience", "with", "Python"]) == set()
    assert adapter.predicted_tokens(["machine", "learning", "and", "SQL"]) == {0, 1, 3}


def test_external_gold_denominator_includes_uncatalogued_skills() -> None:
    gold = adapter.bio_spans(["B-Skill", "I-Skill", "O", "B-Skill"], "Skill")
    assert gold == [(0, 2), (3, 4)]
    assert adapter.bio_spans(["B", "I", "O", "B"], "Knowledge") == [(0, 2), (3, 4)]
    # Detecting one token of an unknown three-token gold set is not perfect recall.
    assert adapter.score(1, 0, 2)["recall"] == pytest.approx(1 / 3)
    with pytest.raises(ValueError, match="Orphan"):
        adapter.bio_spans(["I-Skill"], "Skill")


def test_overlaps_are_deduplicated_without_merging_adjacent_spans() -> None:
    assert adapter.merge_overlaps([(0, 3), (2, 4), (4, 5)]) == [(0, 4), (4, 5)]
