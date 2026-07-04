from __future__ import annotations

import scripts.verify_beta_10_connector_draft_only as verifier


def test_beta_10_connector_draft_only_verifier_passes_current_repo() -> None:
    assert verifier.main() == 0
