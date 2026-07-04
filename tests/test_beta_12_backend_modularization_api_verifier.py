from __future__ import annotations

import scripts.verify_beta_12_backend_modularization_api as verifier


def test_beta_12_backend_modularization_api_verifier_passes_current_repo() -> None:
    assert verifier.validate_beta_12_backend_modularization_api() == []
