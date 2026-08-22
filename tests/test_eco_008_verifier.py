from __future__ import annotations

from scripts.verify_eco_008_changesets import verify


def test_eco_008_verifier_passes() -> None:
    assert verify() == []
