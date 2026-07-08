from scripts.verify_uaa_runtime_turn_run_approval_chain import verify


def test_turn_run_approval_chain_verifier_passes() -> None:
    assert verify() == []
