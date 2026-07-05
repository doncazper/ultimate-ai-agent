from scripts.verify_uaa_goatcitadel_runtime_route_decision_binding import verify


def test_route_decision_binding_verifier_passes() -> None:
    assert verify() == []
