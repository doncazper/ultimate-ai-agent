from __future__ import annotations

from scripts import verify_beta_07_trust_authority_map as verifier


def test_beta_07_trust_authority_map_verifier_passes() -> None:
    assert verifier.main() == 0
