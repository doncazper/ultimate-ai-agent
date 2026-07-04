from __future__ import annotations

from scripts import verify_beta_09_provider_draft_preview as verifier


def test_beta_09_provider_draft_preview_verifier_passes() -> None:
    assert verifier.main() == 0
