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
    ScopedAutonomySessionRequest,
    ScopedAutonomySessionScope,
    build_autonomous_plan_simulation_result,
    build_autonomy_audit_replay_view,
    build_autonomy_policy_decision,
    build_revocation_kill_switch_record,
    build_scoped_approval_bundle,
    validate_revocation_kill_switch_record,
)


def _scope(**overrides: Any) -> Any:
    data = {
        "scope_ref": "autonomy-session-scope:m67-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m67-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m67-local-review",
        "audit_ref": "audit:m67-local-review",
        "replay_ref": "replay:m67-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _policy_decision(scope: Any | None = None) -> Any:
    active_scope = scope or _scope()
    request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:m67-local-review",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=active_scope,
    )
    rule = AutonomyPolicyRule(
        rule_ref="autonomy-policy-rule:m67-local-review",
        allowed_actor_refs=[active_scope.actor_ref],
        allowed_resource_refs=list(active_scope.resource_refs),
        allowed_capability_refs=list(active_scope.capability_refs),
        required_allowlist_refs=list(active_scope.allowlist_refs),
        max_mode=AutonomyAuthorityMode.dry_run_plan,
        max_risk_class=AutonomyRiskClass.low,
        max_duration_seconds=900,
    )
    return build_autonomy_policy_decision(
        AutonomyPolicyEvaluationRequest(
            evaluation_request_ref="autonomy-policy-evaluation:m67-local-review",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:m67-local-review",
                policy_version_ref="autonomy-policy-version:m67-v1",
                rules=[rule],
            ),
            session_request=request,
        )
    )


def _audit_view(scope: Any | None = None) -> Any:
    active_scope = scope or _scope()
    simulation_result = build_autonomous_plan_simulation_result(
        AutonomousPlanSimulationRequest(
            simulation_request_ref="autonomy-plan-simulation-request:m67-local-review",
            policy_decision=_policy_decision(active_scope),
            steps=[
                AutonomousPlanSimulationStep(
                    step_ref="autonomy-simulation-step:m67-inspect",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    simulated_outcome_ref="simulation-outcome:m67-review-only",
                )
            ],
            actor_ref=active_scope.actor_ref,
            resource_refs=list(active_scope.resource_refs),
            capability_refs=list(active_scope.capability_refs),
            allowlist_refs=list(active_scope.allowlist_refs),
            audit_ref=active_scope.audit_ref,
            replay_ref=active_scope.replay_ref,
        )
    )
    return build_autonomy_audit_replay_view(
        audit_view_ref="autonomy-audit-replay-view:m67-local-review",
        simulation_result=simulation_result,
        actor_ref=active_scope.actor_ref,
        audit_ref=active_scope.audit_ref,
        replay_ref=active_scope.replay_ref,
    )


def _bundle(**overrides: Any) -> Any:
    scope = overrides.pop("source_scope", _scope())
    data = {
        "bundle_ref": "scoped-approval-bundle:m67-local-review",
        "source_scope": scope,
        "audit_replay_view": _audit_view(scope),
        "approval_refs": [
            "approval:m67-redacted-review",
            "approval:m67-dry-run-window",
        ],
        "actor_ref": scope.actor_ref,
        "resource_refs": list(scope.resource_refs),
        "capability_refs": list(scope.capability_refs),
        "allowlist_refs": list(scope.allowlist_refs),
        "max_duration_seconds": scope.max_duration_seconds,
        "risk_class": scope.risk_class,
        "revocation_ref": scope.revocation_ref,
        "audit_ref": scope.audit_ref,
        "replay_ref": scope.replay_ref,
    }
    data.update(overrides)
    return build_scoped_approval_bundle(**data)


def _record(**overrides: Any) -> Any:
    bundle = overrides.pop("approval_bundle", _bundle())
    data = {
        "revocation_record_ref": "revocation-kill-switch-record:m67-local-review",
        "approval_bundle": bundle,
        "actor_ref": bundle.actor_ref,
        "resource_refs": list(bundle.resource_refs),
        "capability_refs": list(bundle.capability_refs),
        "allowlist_refs": list(bundle.allowlist_refs),
        "bundle_ref": bundle.bundle_ref,
        "source_scope_ref": bundle.source_scope_ref,
        "audit_view_ref": bundle.audit_view_ref,
        "simulation_result_ref": bundle.simulation_result_ref,
        "revocation_ref": bundle.revocation_ref,
        "audit_ref": bundle.audit_ref,
        "replay_ref": bundle.replay_ref,
    }
    data.update(overrides)
    return build_revocation_kill_switch_record(**data)


def test_revocation_kill_switch_record_is_review_only_exact_bound_and_non_authoritative() -> None:
    record = _record()

    assert record.record_valid_for_review is True
    assert record.review_only is True
    assert record.deterministic is True
    assert record.revocation_requested is True
    assert record.kill_switch_requested is True
    assert record.actor_bound is True
    assert record.resource_bound is True
    assert record.capability_bound is True
    assert record.allowlist_bound is True
    assert record.non_transferable is True
    assert record.replay_safe is True
    assert record.approval_refs_are_identifiers_only is True
    assert record.authority_granted is False
    assert record.revocation_performed is False
    assert record.kill_switch_activated is False
    assert record.session_stopped is False
    assert record.execution_performed is False
    assert record.side_effects_performed == []
    assert record.bundle_ref == "scoped-approval-bundle:m67-local-review"
    assert record.source_scope_ref == "autonomy-session-scope:m67-local-review"
    assert record.audit_view_ref == "autonomy-audit-replay-view:m67-local-review"
    assert record.simulation_result_ref == "autonomy-plan-simulation-result:m67-local-review"
    assert record.reason_codes == ["M67_REVOCATION_KILL_SWITCH_REVIEW_ONLY"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("revocation_performed", "REVOCATION_ACTION_DENIED"),
        ("kill_switch_activated", "KILL_SWITCH_ACTIVATION_DENIED"),
        ("session_stopped", "AUTONOMY_SESSION_STOP_DENIED"),
        ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
        ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
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
def test_revocation_kill_switch_denies_activation_execution_and_authority_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_revocation_kill_switch_record(_record().model_copy(update={field: True}))


def test_revocation_kill_switch_revalidates_mutated_bundle_and_scope() -> None:
    for bundle, reason in [
        (
            _bundle().model_copy(update={"actor_ref": "actor:other-reviewer"}),
            "REVOCATION_KILL_SWITCH_ACTOR_BINDING_MISMATCH_DENIED",
        ),
        (
            _bundle().model_copy(update={"source_scope": _scope(metadata={"api_key": "secret-value"})}),
            "SECRET_LIKE_REVOCATION_KILL_SWITCH_CONTENT_DENIED",
        ),
        (
            _bundle().model_copy(update={"authority_granted": True}),
            "AUTONOMY_POLICY_AUTHORITY_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_revocation_kill_switch_record(
                _record().model_copy(update={"approval_bundle": bundle})
            )


def test_revocation_kill_switch_denies_hidden_binding_drift_and_test_refs() -> None:
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m67"}, "APPROVAL_TEST_REF_DENIED"),
        ({"approval_refs": ["approval_test_:m67"]}, "APPROVAL_TEST_REF_DENIED"),
        ({"bundle_ref": "scoped-approval-bundle:other"}, "REVOCATION_KILL_SWITCH_BUNDLE_BINDING_MISMATCH_DENIED"),
        ({"source_scope_ref": "autonomy-session-scope:other"}, "REVOCATION_KILL_SWITCH_SCOPE_BINDING_MISMATCH_DENIED"),
        ({"audit_view_ref": "autonomy-audit-replay-view:other"}, "REVOCATION_KILL_SWITCH_AUDIT_VIEW_BINDING_MISMATCH_DENIED"),
        ({"simulation_result_ref": "autonomy-plan-simulation-result:other"}, "REVOCATION_KILL_SWITCH_SIMULATION_BINDING_MISMATCH_DENIED"),
        ({"actor_ref": "actor:other-reviewer"}, "REVOCATION_KILL_SWITCH_ACTOR_BINDING_MISMATCH_DENIED"),
        ({"resource_refs": ["resource:other"]}, "REVOCATION_KILL_SWITCH_RESOURCE_BINDING_MISMATCH_DENIED"),
        ({"capability_refs": ["capability:other"]}, "REVOCATION_KILL_SWITCH_CAPABILITY_BINDING_MISMATCH_DENIED"),
        ({"allowlist_refs": ["allowlist:other"]}, "REVOCATION_KILL_SWITCH_ALLOWLIST_BINDING_MISMATCH_DENIED"),
        ({"revocation_ref": "revocation:other"}, "REVOCATION_KILL_SWITCH_REVOCATION_BINDING_MISMATCH_DENIED"),
        ({"audit_ref": "audit:other"}, "REVOCATION_KILL_SWITCH_AUDIT_BINDING_MISMATCH_DENIED"),
        ({"replay_ref": "replay:other"}, "REVOCATION_KILL_SWITCH_REPLAY_BINDING_MISMATCH_DENIED"),
        ({"metadata": {"token": "secret-value"}}, "SECRET_LIKE_REVOCATION_KILL_SWITCH_CONTENT_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_revocation_kill_switch_record(_record().model_copy(update=update))
