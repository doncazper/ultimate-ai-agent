from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyCapabilityToggle,
    AutonomyModeCharter,
    AutonomyRiskClass,
    build_autonomy_mode_decision,
    validate_autonomy_capability_toggle,
    validate_autonomy_mode_charter,
)


def _toggle(**overrides: Any) -> Any:
    data = {
        "toggle_ref": "autonomy-toggle:m61-observe",
        "capability_ref": "capability:autonomy-observe-only",
        "requested_mode": AutonomyAuthorityMode.off,
        "actor_ref": "actor:local-reviewer",
        "scope_ref": "scope:m61-contract-review",
        "resource_refs": ["resource:local-prototype"],
        "duration_seconds": 0,
        "risk_class": AutonomyRiskClass.low,
        "approval_ref": None,
        "revocation_ref": "revocation:m61-contract-review",
        "audit_ref": "audit:m61-contract-review",
    }
    data.update(overrides)
    return AutonomyCapabilityToggle(**data)


def test_autonomy_mode_charter_defines_modes_but_defaults_to_off() -> None:
    charter = validate_autonomy_mode_charter(AutonomyModeCharter())

    assert charter.default_mode == AutonomyAuthorityMode.off
    assert set(charter.available_modes) == set(AutonomyAuthorityMode)
    assert charter.disabled_by_default is True
    assert charter.dry_run_first is True
    assert charter.limited_allowlist_required is True
    assert charter.explicit_approval_required is True
    assert charter.scoped_autonomy_window_required is True
    assert charter.audit_replay_required is True
    assert charter.revocation_required is True
    assert charter.production_authority_enabled is False
    assert charter.global_autonomy_switch_enabled is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("global_autonomy_switch_enabled", "GLOBAL_AUTONOMY_SWITCH_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
        ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
        ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
    ],
)
def test_autonomy_mode_charter_denies_enablement_flags(field: str, reason: str) -> None:
    charter = AutonomyModeCharter(**{field: True})

    with pytest.raises(ValueError, match=reason):
        validate_autonomy_mode_charter(charter)


def test_autonomy_capability_toggle_requires_scope_resource_revocation_and_audit() -> None:
    validated = validate_autonomy_capability_toggle(_toggle())

    assert validated.enabled is False
    assert validated.dry_run_only is True
    assert validated.resource_refs == ["resource:local-prototype"]

    with pytest.raises(ValueError, match="RESOURCE_BINDING_REQUIRED"):
        validate_autonomy_capability_toggle(_toggle(resource_refs=[]))

    with pytest.raises(ValueError, match="revocation_ref is required"):
        validate_autonomy_capability_toggle(_toggle(revocation_ref=""))

    with pytest.raises(ValueError, match="audit_ref is required"):
        validate_autonomy_capability_toggle(_toggle(audit_ref=""))


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("enabled", "AUTONOMY_TOGGLE_ENABLEMENT_DENIED"),
        ("dry_run_only", "AUTONOMY_DRY_RUN_FIRST_REQUIRED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ],
)
def test_autonomy_capability_toggle_denies_runtime_flags(field: str, reason: str) -> None:
    toggle = _toggle(**{field: True if field != "dry_run_only" else False})

    with pytest.raises(ValueError, match=reason):
        validate_autonomy_capability_toggle(toggle)


def test_autonomy_capability_toggle_denies_non_off_modes_even_with_approval_ref() -> None:
    toggle = _toggle(
        requested_mode=AutonomyAuthorityMode.ask_before_every_action,
        duration_seconds=300,
        approval_ref="approval:m61-review-only",
    )

    with pytest.raises(ValueError, match="AUTONOMY_MODE_ENABLEMENT_DENIED"):
        validate_autonomy_capability_toggle(toggle)


def test_autonomy_capability_toggle_denies_future_modes_and_approval_test_refs() -> None:
    future_toggle = _toggle(
        requested_mode=AutonomyAuthorityMode.scoped_autonomy_window,
        duration_seconds=300,
    )

    with pytest.raises(ValueError, match="AUTONOMY_MODE_FUTURE_MILESTONE_DENIED"):
        validate_autonomy_capability_toggle(future_toggle)

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        validate_autonomy_capability_toggle(_toggle(approval_test_ref="approval_test_:m61"))


def test_autonomy_mode_decision_is_review_only_and_no_effect() -> None:
    decision = build_autonomy_mode_decision(_toggle())

    assert decision.selected_mode == AutonomyAuthorityMode.off
    assert decision.allowed is False
    assert decision.dry_run_only is True
    assert decision.side_effects_performed == []
    assert decision.reason_codes == ["M61_AUTONOMY_MODE_CHARTER_DEFAULT_OFF"]
    assert "private key" not in str(decision.model_dump()).lower()


def test_autonomy_mode_charter_revalidates_model_copy_mutated_objects() -> None:
    charter = AutonomyModeCharter().model_copy(update={"default_mode": AutonomyAuthorityMode.dry_run_plan})
    toggle = _toggle().model_copy(
        update={
            "enabled": True,
            "approval_ref": "approval:m61-review-only",
            "metadata": {"token": "abcde12345678901234"},
        }
    )

    with pytest.raises(ValueError, match="AUTONOMY_DEFAULT_MODE_OFF_REQUIRED"):
        validate_autonomy_mode_charter(charter)

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMY_CONTENT_DENIED"):
        validate_autonomy_capability_toggle(toggle)
