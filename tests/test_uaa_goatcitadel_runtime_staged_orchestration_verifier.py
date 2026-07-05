from scripts import verify_uaa_goatcitadel_runtime_staged_orchestration


def test_staged_orchestration_verifier_passes() -> None:
    assert verify_uaa_goatcitadel_runtime_staged_orchestration.main() == 0
