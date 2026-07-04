from __future__ import annotations

import scripts.verify_beta_11_operator_workspace_spine as verifier


def test_beta_11_operator_workspace_spine_verifier_passes_current_repo() -> None:
    assert verifier.validate_beta_11_operator_workspace_spine() == []
