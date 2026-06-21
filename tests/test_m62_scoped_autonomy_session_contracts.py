from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    ScopedAutonomySessionRequest,
    ScopedAutonomySessionScope,
    build_scoped_autonomy_session_decision,
    validate_scoped_autonomy_session_request,
    validate_scoped_autonomy_session_scope,
)


def _scope(**overrides: Any) -> Any:
    data = {
        "scope_ref": "autonomy-session-scope:m62-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m62-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m62-local-review",
        "audit_ref": "audit:m62-local-review",
        "replay_ref": "replay:m62-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "session_request_ref": "autonomy-session-request:m62-local-review",
        "requested_mode": AutonomyAuthorityMode.dry_run_plan,
        "scope": _scope(),
        "approval_ref": "approval:m62-review-only",
    }
    data.update(overrides)
    return ScopedAutonomySessionRequest(**data)


def test_scoped_autonomy_session_scope_is_bounded_review_only() -> None:
    scope = validate_scoped_autonomy_session_scope(_scope())

    assert scope.disabled_by_default is True
    assert scope.dry_run_only is True
    assert scope.max_duration_seconds == 900
    assert scope.resource_refs == ["resource:local-prototype"]
    assert scope.allowlist_refs == ["allowlist:m62-local-review"]

    with pytest.raises(ValueError, match="RESOURCE_BINDING_REQUIRED"):
        validate_scoped_autonomy_session_scope(_scope(resource_refs=[]))

    with pytest.raises(ValueError, match="ALLOWLIST_REQUIRED"):
        validate_scoped_autonomy_session_scope(_scope(allowlist_refs=[]))

    with pytest.raises(ValueError, match="SESSION_DURATION_BOUND_EXCEEDED"):
        validate_scoped_autonomy_session_scope(_scope(max_duration_seconds=86_400))


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("disabled_by_default", "DISABLED_BY_DEFAULT_REQUIRED"),
        ("dry_run_only", "DRY_RUN_FIRST_REQUIRED"),
        ("session_start_enabled", "AUTONOMY_SESSION_START_DENIED"),
        ("session_activation_enabled", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
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
def test_scoped_autonomy_session_scope_denies_runtime_flags(field: str, reason: str) -> None:
    value = False if field in {"disabled_by_default", "dry_run_only"} else True

    with pytest.raises(ValueError, match=reason):
        validate_scoped_autonomy_session_scope(_scope(**{field: value}))


def test_scoped_autonomy_session_request_is_contract_only() -> None:
    request = validate_scoped_autonomy_session_request(_request())

    assert request.requested_mode == AutonomyAuthorityMode.dry_run_plan
    assert request.start_requested is False
    assert request.session_active is False
    assert request.execution_requested is False

    decision = build_scoped_autonomy_session_decision(request)
    assert decision.contract_valid_for_review is True
    assert decision.session_started is False
    assert decision.session_active is False
    assert decision.execution_performed is False
    assert decision.side_effects_performed == []
    assert decision.reason_codes == ["M62_SCOPED_AUTONOMY_SESSION_CONTRACT_REVIEW_ONLY"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ],
)
def test_scoped_autonomy_session_request_denies_activation_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_scoped_autonomy_session_request(_request(**{field: True}))


def test_scoped_autonomy_session_request_denies_approval_refs_as_authority() -> None:
    with pytest.raises(ValueError, match="AUTONOMY_MODE_ENABLEMENT_DENIED"):
        validate_scoped_autonomy_session_request(
            _request(
                requested_mode=AutonomyAuthorityMode.ask_before_every_action,
                approval_ref="approval:m62-review-only",
            )
        )

    with pytest.raises(ValueError, match="AUTONOMY_MODE_FUTURE_MILESTONE_DENIED"):
        validate_scoped_autonomy_session_request(
            _request(requested_mode=AutonomyAuthorityMode.scoped_autonomy_window)
        )

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        validate_scoped_autonomy_session_request(_request(approval_test_ref="approval_test_:m62"))


def test_scoped_autonomy_session_revalidates_model_copy_mutations() -> None:
    safe_request = _request()
    mutated_scope = safe_request.scope.model_copy(update={"session_activation_enabled": True})
    mutated_request = safe_request.model_copy(
        update={
            "scope": mutated_scope,
            "start_requested": True,
            "metadata": {"token": "abcde12345678901234"},
        }
    )

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMY_SESSION_CONTENT_DENIED"):
        validate_scoped_autonomy_session_request(mutated_request)
