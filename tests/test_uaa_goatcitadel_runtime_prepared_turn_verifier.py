from scripts import verify_uaa_goatcitadel_runtime_prepared_turn


def test_prepared_turn_verifier_passes() -> None:
    assert verify_uaa_goatcitadel_runtime_prepared_turn.main() == 0
