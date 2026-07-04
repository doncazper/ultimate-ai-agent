from __future__ import annotations

from scripts import verify_beta_08_web_evidence_product_slice as verifier


def test_beta_08_web_evidence_product_slice_verifier_passes() -> None:
    assert verifier.main() == 0
