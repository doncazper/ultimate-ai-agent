from __future__ import annotations

from scripts.verification import run_all_legacy


def test_mobile_sensor_guard_does_not_flag_verifier_literals() -> None:
    run_all_legacy.verify_no_mobile_native_or_sensor_implementation()
