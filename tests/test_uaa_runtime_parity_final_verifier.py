from scripts import verify_uaa_runtime_parity_final


def test_runtime_parity_final_verifier_passes() -> None:
    assert verify_uaa_runtime_parity_final.main() == 0
