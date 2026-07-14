import json
from pathlib import Path

import pytest

from scripts.verification.verify_mutation_score import (
    MutationScoreError,
    verify_mutation_score,
)


def _write_stats(path: Path, *, killed: int, survived: int) -> None:
    path.write_text(
        json.dumps(
            {
                "killed": killed,
                "survived": survived,
                "total": killed + survived,
                "no_tests": 0,
                "suspicious": 0,
                "timeout": 0,
                "check_was_interrupted_by_user": 0,
                "segfault": 0,
            }
        ),
        encoding="utf-8",
    )


def test_mutation_score_accepts_complete_evidence_above_floor(tmp_path: Path) -> None:
    stats = tmp_path / "stats.json"
    _write_stats(stats, killed=140, survived=60)

    assert verify_mutation_score(stats, minimum_score=60.0, minimum_total=200) == 70.0


def test_mutation_score_rejects_regression_below_floor(tmp_path: Path) -> None:
    stats = tmp_path / "stats.json"
    _write_stats(stats, killed=119, survived=81)

    with pytest.raises(MutationScoreError, match="MUTATION_SCORE_BELOW_FLOOR"):
        verify_mutation_score(stats, minimum_score=60.0, minimum_total=200)
