from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyPolicyEnginePolicy,
    AutonomyPolicyEvaluationRequest,
    AutonomyPolicyRule,
    AutonomyRiskClass,
    AutonomousPlanSimulationRequest,
    AutonomousPlanSimulationStep,
    AutonomyReplayStepView,
    ScopedAutonomySessionRequest,
    ScopedAutonomySessionScope,
    build_autonomous_plan_simulation_result,
    build_autonomy_audit_replay_view,
    build_autonomy_policy_decision,
    validate_autonomy_audit_replay_view,
)


def _scope(**overrides: Any) -> Any:
    data = {
        "scope_ref": "autonomy-session-scope:m65-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m65-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m65-local-review",
        "audit_ref": "audit:m65-local-review",
        "replay_ref": "replay:m65-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _session_request(**overrides: Any) -> Any:
    data = {
        "session_request_ref": "autonomy-session-request:m65-local-review",
        "requested_mode": AutonomyAuthorityMode.dry_run_plan,
        "scope": _scope(),
    }
    data.update(overrides)
    return ScopedAutonomySessionRequest(**data)


def _rule(**overrides: Any) -> Any:
    data = {
        "rule_ref": "autonomy-policy-rule:m65-local-review",
        "allowed_actor_refs": ["actor:local-reviewer"],
        "allowed_resource_refs": ["resource:local-prototype"],
        "allowed_capability_refs": ["capability:observe-only-review"],
        "required_allowlist_refs": ["allowlist:m65-local-review"],
        "max_mode": AutonomyAuthorityMode.dry_run_plan,
        "max_risk_class": AutonomyRiskClass.low,
        "max_duration_seconds": 900,
    }
    data.update(overrides)
    return AutonomyPolicyRule(**data)


def _policy(**overrides: Any) -> Any:
    data = {
        "policy_ref": "autonomy-policy:m65-local-review",
        "policy_version_ref": "autonomy-policy-version:m65-v1",
        "rules": [_rule()],
    }
    data.update(overrides)
    return AutonomyPolicyEnginePolicy(**data)


def _policy_decision(**overrides: Any) -> Any:
    request = AutonomyPolicyEvaluationRequest(
        evaluation_request_ref="autonomy-policy-evaluation:m65-local-review",
        policy=_policy(),
        session_request=_session_request(),
    )
    decision = build_autonomy_policy_decision(request)
    if overrides:
        decision = decision.model_copy(update=overrides)
    return decision


def _step(step_ref: str = "autonomy-simulation-step:m65-inspect-plan", **overrides: Any) -> Any:
    data = {
        "step_ref": step_ref,
        "intent_ref": "intent:inspect-redacted-review-packet",
        "capability_ref": "capability:observe-only-review",
        "resource_ref": "resource:local-prototype",
        "simulated_outcome_ref": "simulation-outcome:redacted-review-only",
        "risk_class": AutonomyRiskClass.low,
        "depends_on_step_refs": [],
    }
    data.update(overrides)
    return AutonomousPlanSimulationStep(**data)


def _simulation_result(**overrides: Any) -> Any:
    simulation_request = AutonomousPlanSimulationRequest(
        simulation_request_ref="autonomy-plan-simulation-request:m65-local-review",
        policy_decision=_policy_decision(),
        steps=[
            _step("autonomy-simulation-step:m65-first"),
            _step(
                "autonomy-simulation-step:m65-second",
                depends_on_step_refs=["autonomy-simulation-step:m65-first"],
            ),
        ],
        actor_ref="actor:local-reviewer",
        resource_refs=["resource:local-prototype"],
        capability_refs=["capability:observe-only-review"],
        allowlist_refs=["allowlist:m65-local-review"],
        audit_ref="audit:m65-local-review",
        replay_ref="replay:m65-local-review",
    )
    result = build_autonomous_plan_simulation_result(simulation_request)
    if overrides:
        result = result.model_copy(update=overrides)
    return result


def _replay_view(**overrides: Any) -> Any:
    data = {
        "audit_view_ref": "autonomy-audit-replay-view:m65-local-review",
        "simulation_result": _simulation_result(),
        "actor_ref": "actor:local-reviewer",
        "audit_ref": "audit:m65-local-review",
        "replay_ref": "replay:m65-local-review",
    }
    data.update(overrides)
    return build_autonomy_audit_replay_view(**data)


def test_autonomy_audit_replay_view_is_review_only_and_exact_bound() -> None:
    view = _replay_view()

    assert view.contract_valid_for_review is True
    assert view.review_only is True
    assert view.replay_view_only is True
    assert view.deterministic is True
    assert view.authority_granted is False
    assert view.session_started is False
    assert view.execution_performed is False
    assert view.side_effects_performed == []
    assert view.simulation_result_ref == "autonomy-plan-simulation-result:m65-local-review"
    assert view.policy_decision_ref == "autonomy-policy-decision:m65-local-review"
    assert view.simulated_step_refs == [
        "autonomy-simulation-step:m65-first",
        "autonomy-simulation-step:m65-second",
    ]
    assert [step.step_ref for step in view.replay_steps] == view.simulated_step_refs
    assert view.reason_codes == ["M65_AUTONOMY_AUDIT_REPLAY_VIEW_REVIEW_ONLY"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("execution_performed", "EXECUTION_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("authority_granted", "AUTONOMY_POLICY_AUTHORITY_DENIED"),
    ],
)
def test_autonomy_audit_replay_view_denies_runtime_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomy_audit_replay_view(_replay_view().model_copy(update={field: True}))


def test_autonomy_audit_replay_view_revalidates_mutated_simulation_result() -> None:
    for update, reason in [
        ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
        ({"session_started": True}, "AUTONOMY_SESSION_START_DENIED"),
        ({"execution_performed": True}, "EXECUTION_DENIED"),
        ({"side_effects_performed": ["tool:unsafe"]}, "AUTONOMY_SIDE_EFFECTS_DENIED"),
        ({"contract_valid_for_review": False}, "REVIEW_ONLY_REQUIRED"),
        ({"dry_run_only": False}, "DRY_RUN_FIRST_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_autonomy_audit_replay_view(
                _replay_view(simulation_result=_simulation_result(**update))
            )


def test_autonomy_audit_replay_view_rejects_forged_replay_steps() -> None:
    view = _replay_view()

    with pytest.raises(ValueError, match="REPLAY_STEP_SEQUENCE_MISMATCH_DENIED"):
        validate_autonomy_audit_replay_view(
            view.model_copy(update={"simulated_step_refs": ["autonomy-simulation-step:m65-forged"]})
        )

    with pytest.raises(ValueError, match="REPLAY_STEP_SEQUENCE_MISMATCH_DENIED"):
        validate_autonomy_audit_replay_view(
            view.model_copy(
                update={
                    "replay_steps": [
                        AutonomyReplayStepView(
                            step_ref="autonomy-simulation-step:m65-forged",
                            replay_outcome_ref="replay-outcome:forged",
                        )
                    ]
                }
            )
        )


def test_autonomy_audit_replay_view_denies_test_approval_and_secret_content() -> None:
    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        validate_autonomy_audit_replay_view(
            _replay_view().model_copy(update={"approval_test_ref": "approval_test_:m65"})
        )

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMY_AUDIT_REPLAY_CONTENT_DENIED"):
        validate_autonomy_audit_replay_view(
            _replay_view().model_copy(update={"metadata": {"api_key": "secret-value"}})
        )
