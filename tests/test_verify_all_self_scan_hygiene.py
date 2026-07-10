from __future__ import annotations

from scripts.verification import run_all_legacy


def test_mobile_sensor_guard_does_not_flag_verifier_literals() -> None:
    run_all_legacy.verify_no_mobile_native_or_sensor_implementation()


def test_openwebui_guard_does_not_flag_foundation_gate_policy_literals() -> None:
    run_all_legacy.verify_no_openwebui_runtime_or_config_implementation()


def test_control_center_guard_allows_safe_blocker_and_billing_reason_refs() -> None:
    run_all_legacy.verify_no_control_center_runtime_or_frontend_expansion()
