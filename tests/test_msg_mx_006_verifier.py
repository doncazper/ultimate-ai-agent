from __future__ import annotations

from scripts.verify_msg_mx_006_read_only_sync import verify


def test_msg_mx_006_verifier_accepts_current_repository() -> None:
    assert verify() == []
