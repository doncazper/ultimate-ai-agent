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
    build_scoped_approval_bundle,
    validate_scoped_approval_bundle,
)


def _scope(**overrides: Any) -> Any:
    data = {
        "scope_ref": "autonomy-session-scope:m66-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m66-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m66-local-review",
        "audit_ref": "audit:m66-local-review",
        "replay_ref": "replay:m66-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _policy_decision(scope: Any | None = None) -> Any:
    active_scope = scope or _scope()
    request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:m66-local-review",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=active_scope,
    )
    rule = AutonomyPolicyRule(
        rule_ref="autonomy-policy-rule:m66-local-review",
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
            evaluation_request_ref="autonomy-policy-evaluation:m66-local-review",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:m66-local-review",
                policy_version_ref="autonomy-policy-version:m66-v1",
                rules=[rule],
            ),
            session_request=request,
        )
    )


def _audit_view(scope: Any | None = None) -> Any:
    active_scope = scope or _scope()
    simulation_result = build_autonomous_plan_simulation_result(
        AutonomousPlanSimulationRequest(
            simulation_request_ref="autonomy-plan-simulation-request:m66-local-review",
            policy_decision=_policy_decision(active_scope),
            steps=[
                AutonomousPlanSimulationStep(
                    step_ref="autonomy-simulation-step:m66-inspect",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    simulated_outcome_ref="simulation-outcome:m66-review-only",
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
        audit_view_ref="autonomy-audit-replay-view:m66-local-review",
        simulation_result=simulation_result,
        actor_ref=active_scope.actor_ref,
        audit_ref=active_scope.audit_ref,
        replay_ref=active_scope.replay_ref,
    )


def _bundle(**overrides: Any) -> Any:
    scope = overrides.pop("source_scope", _scope())
    data = {
        "bundle_ref": "scoped-approval-bundle:m66-local-review",
        "source_scope": scope,
        "audit_replay_view": _audit_view(scope),
        "approval_refs": [
            "approval:m66-redacted-review",
            "approval:m66-dry-run-window",
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


def test_scoped_approval_bundle_is_exact_bound_review_only_and_identifier_only() -> None:
    bundle = _bundle()

    assert bundle.bundle_valid_for_review is True
    assert bundle.review_only is True
    assert bundle.deterministic is True
    assert bundle.actor_bound is True
    assert bundle.resource_bound is True
    assert bundle.capability_bound is True
    assert bundle.allowlist_bound is True
    assert bundle.non_transferable is True
    assert bundle.revocable is True
    assert bundle.replay_safe is True
    assert bundle.approval_refs_are_identifiers_only is True
    assert bundle.authority_granted is False
    assert bundle.session_started is False
    assert bundle.execution_performed is False
    assert bundle.side_effects_performed == []
    assert bundle.source_scope_ref == "autonomy-session-scope:m66-local-review"
    assert bundle.audit_view_ref == "autonomy-audit-replay-view:m66-local-review"
    assert bundle.simulation_result_ref == "autonomy-plan-simulation-result:m66-local-review"
    assert bundle.reason_codes == ["M66_SCOPED_APPROVAL_BUNDLE_REVIEW_ONLY"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
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
def test_scoped_approval_bundle_denies_runtime_and_authority_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_scoped_approval_bundle(_bundle().model_copy(update={field: True}))


def test_scoped_approval_bundle_denies_test_refs_duplicates_revoked_expired_and_replay() -> None:
    for update, reason in [
        ({"approval_refs": []}, "APPROVAL_BUNDLE_APPROVAL_REF_REQUIRED"),
        (
            {"approval_refs": ["approval:m66-redacted-review", "approval:m66-redacted-review"]},
            "APPROVAL_BUNDLE_DUPLICATE_REF_DENIED",
        ),
        ({"approval_refs": ["approval_test_:m66"]}, "APPROVAL_TEST_REF_DENIED"),
        ({"approval_test_ref": "approval_test_:m66"}, "APPROVAL_TEST_REF_DENIED"),
        ({"revoked": True}, "APPROVAL_BUNDLE_REVOKED_DENIED"),
        ({"expired": True}, "APPROVAL_BUNDLE_EXPIRED_DENIED"),
        ({"replay_used": True}, "APPROVAL_BUNDLE_REPLAY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_approval_bundle(_bundle().model_copy(update=update))


def test_scoped_approval_bundle_revalidates_mutated_scope_and_replay_view() -> None:
    for source_scope, reason in [
        (_scope(actor_ref="actor:other-reviewer"), "APPROVAL_BUNDLE_ACTOR_BINDING_MISMATCH_DENIED"),
        (
            _scope(metadata={"api_key": "secret-value"}),
            "SECRET_LIKE_SCOPED_APPROVAL_BUNDLE_CONTENT_DENIED",
        ),
        (
            _scope(session_start_enabled=True),
            "AUTONOMY_SESSION_START_DENIED",
        ),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_approval_bundle(_bundle().model_copy(update={"source_scope": source_scope}))

    for update, reason in [
        ({"actor_ref": "actor:other-reviewer"}, "APPROVAL_BUNDLE_ACTOR_BINDING_MISMATCH_DENIED"),
        ({"audit_ref": "audit:other"}, "APPROVAL_BUNDLE_AUDIT_BINDING_MISMATCH_DENIED"),
        ({"replay_ref": "replay:other"}, "APPROVAL_BUNDLE_REPLAY_BINDING_MISMATCH_DENIED"),
        ({"authority_granted": True}, "AUTONOMY_POLICY_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_approval_bundle(
                _bundle().model_copy(update={"audit_replay_view": _audit_view().model_copy(update=update)})
            )


def test_scoped_approval_bundle_denies_hidden_scope_drift() -> None:
    for update, reason in [
        ({"actor_ref": "actor:other-reviewer"}, "APPROVAL_BUNDLE_ACTOR_BINDING_MISMATCH_DENIED"),
        ({"resource_refs": ["resource:other"]}, "APPROVAL_BUNDLE_RESOURCE_BINDING_MISMATCH_DENIED"),
        ({"capability_refs": ["capability:other"]}, "APPROVAL_BUNDLE_CAPABILITY_BINDING_MISMATCH_DENIED"),
        ({"allowlist_refs": ["allowlist:other"]}, "APPROVAL_BUNDLE_ALLOWLIST_BINDING_MISMATCH_DENIED"),
        ({"max_duration_seconds": 901}, "APPROVAL_BUNDLE_DURATION_BINDING_MISMATCH_DENIED"),
        ({"risk_class": AutonomyRiskClass.medium}, "APPROVAL_BUNDLE_RISK_BINDING_MISMATCH_DENIED"),
        ({"revocation_ref": "revocation:other"}, "APPROVAL_BUNDLE_REVOCATION_BINDING_MISMATCH_DENIED"),
        ({"audit_ref": "audit:other"}, "APPROVAL_BUNDLE_AUDIT_BINDING_MISMATCH_DENIED"),
        ({"replay_ref": "replay:other"}, "APPROVAL_BUNDLE_REPLAY_BINDING_MISMATCH_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_scoped_approval_bundle(_bundle().model_copy(update=update))
