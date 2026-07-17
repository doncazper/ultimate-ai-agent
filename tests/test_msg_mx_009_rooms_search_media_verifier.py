from __future__ import annotations

from scripts import verify_msg_mx_009_rooms_search_media as verifier


def test_msg_mx_009_canonical_verifier_passes() -> None:
    assert verifier.verify() == []
