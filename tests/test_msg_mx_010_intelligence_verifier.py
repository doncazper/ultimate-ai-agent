from __future__ import annotations

from scripts import verify_msg_mx_010_intelligence_proposals as verifier


def test_msg_mx_010_canonical_verifier_passes() -> None:
    assert verifier.verify() == []
