from typing import Any
import pytest

from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyPolicyEnginePolicy,
    AutonomyPolicyEvaluationRequest,
    AutonomyPolicyRule,
    AutonomyRiskClass,
    AutonomyRiskSignal,
    AutonomyRiskSignalKind,
    AutonomyRiskClassificationRequest,
    AutonomousPlanSimulationRequest,
    AutonomousPlanSimulationStep,
    ScopedAutonomySessionRequest,
    ScopedAutonomySessionScope,
    build_autonomous_plan_simulation_result,
    build_autonomy_audit_replay_view,
    build_autonomy_policy_decision,
    build_autonomy_risk_classification_decision,
    build_revocation_kill_switch_record,
    build_scoped_approval_bundle,
    validate_autonomy_risk_classification_decision,
)


def _scope(**overrides: Any) -> Any:
    data = {
        "scope_ref": "autonomy-session-scope:m68-local-review",
        "actor_ref": "actor:local-reviewer",
        "resource_refs": ["resource:local-prototype"],
        "capability_refs": ["capability:observe-only-review"],
        "allowlist_refs": ["allowlist:m68-local-review"],
        "max_duration_seconds": 900,
        "risk_class": AutonomyRiskClass.low,
        "revocation_ref": "revocation:m68-local-review",
        "audit_ref": "audit:m68-local-review",
        "replay_ref": "replay:m68-local-review",
    }
    data.update(overrides)
    return ScopedAutonomySessionScope(**data)


def _policy_decision(scope: Any | None = None) -> Any:
    active_scope = scope or _scope()
    request = ScopedAutonomySessionRequest(
        session_request_ref="autonomy-session-request:m68-local-review",
        requested_mode=AutonomyAuthorityMode.dry_run_plan,
        scope=active_scope,
    )
    rule = AutonomyPolicyRule(
        rule_ref="autonomy-policy-rule:m68-local-review",
        allowed_actor_refs=[active_scope.actor_ref],
        allowed_resource_refs=list(active_scope.resource_refs),
        allowed_capability_refs=list(active_scope.capability_refs),
        required_allowlist_refs=list(active_scope.allowlist_refs),
        max_mode=AutonomyAuthorityMode.dry_run_plan,
        max_risk_class=AutonomyRiskClass.high,
        max_duration_seconds=900,
    )
    return build_autonomy_policy_decision(
        AutonomyPolicyEvaluationRequest(
            evaluation_request_ref="autonomy-policy-evaluation:m68-local-review",
            policy=AutonomyPolicyEnginePolicy(
                policy_ref="autonomy-policy:m68-local-review",
                policy_version_ref="autonomy-policy-version:m68-v1",
                rules=[rule],
            ),
            session_request=request,
        )
    )


def _audit_view(scope: Any | None = None) -> Any:
    active_scope = scope or _scope()
    simulation_result = build_autonomous_plan_simulation_result(
        AutonomousPlanSimulationRequest(
            simulation_request_ref="autonomy-plan-simulation-request:m68-local-review",
            policy_decision=_policy_decision(active_scope),
            steps=[
                AutonomousPlanSimulationStep(
                    step_ref="autonomy-simulation-step:m68-inspect",
                    intent_ref="intent:inspect-redacted-review-packet",
                    capability_ref="capability:observe-only-review",
                    resource_ref="resource:local-prototype",
                    simulated_outcome_ref="simulation-outcome:m68-review-only",
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
        audit_view_ref="autonomy-audit-replay-view:m68-local-review",
        simulation_result=simulation_result,
        actor_ref=active_scope.actor_ref,
        audit_ref=active_scope.audit_ref,
        replay_ref=active_scope.replay_ref,
    )


def _bundle(**overrides: Any) -> Any:
    scope = overrides.pop("source_scope", _scope())
    data = {
        "bundle_ref": "scoped-approval-bundle:m68-local-review",
        "source_scope": scope,
        "audit_replay_view": _audit_view(scope),
        "approval_refs": [
            "approval:m68-redacted-review",
            "approval:m68-dry-run-window",
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


def _revocation_record(bundle: Any | None = None) -> Any:
    active_bundle = bundle or _bundle()
    return build_revocation_kill_switch_record(
        revocation_record_ref="revocation-kill-switch-record:m68-local-review",
        approval_bundle=active_bundle,
        actor_ref=active_bundle.actor_ref,
        resource_refs=list(active_bundle.resource_refs),
        capability_refs=list(active_bundle.capability_refs),
        allowlist_refs=list(active_bundle.allowlist_refs),
        bundle_ref=active_bundle.bundle_ref,
        source_scope_ref=active_bundle.source_scope_ref,
        audit_view_ref=active_bundle.audit_view_ref,
        simulation_result_ref=active_bundle.simulation_result_ref,
        revocation_ref=active_bundle.revocation_ref,
        audit_ref=active_bundle.audit_ref,
        replay_ref=active_bundle.replay_ref,
    )


def _request(**overrides: Any) -> Any:
    bundle = overrides.pop("approval_bundle", _bundle())
    revocation_record = overrides.pop("revocation_record", _revocation_record(bundle))
    data = {
        "classification_request_ref": "autonomy-risk-classification-request:m68-local-review",
        "approval_bundle": bundle,
        "revocation_record": revocation_record,
        "declared_risk_class": AutonomyRiskClass.low,
        "risk_signals": [
            AutonomyRiskSignal(
                signal_ref="autonomy-risk-signal:m68-redacted-preview",
                signal_kind=AutonomyRiskSignalKind.redacted_review,
                risk_class=AutonomyRiskClass.low,
                source_ref="evidence:redacted-review-packet",
                reason_code="M68_SIGNAL_REDACTED_REVIEW_LOW",
            )
        ],
        "actor_ref": bundle.actor_ref,
        "resource_refs": list(bundle.resource_refs),
        "capability_refs": list(bundle.capability_refs),
        "allowlist_refs": list(bundle.allowlist_refs),
        "bundle_ref": bundle.bundle_ref,
        "revocation_record_ref": revocation_record.revocation_record_ref,
        "source_scope_ref": bundle.source_scope_ref,
        "audit_ref": bundle.audit_ref,
        "replay_ref": bundle.replay_ref,
    }
    data.update(overrides)
    return AutonomyRiskClassificationRequest(**data)


def _decision(**overrides: Any) -> Any:
    request = overrides.pop("classification_request", _request())
    decision = build_autonomy_risk_classification_decision(request)
    if overrides:
        return decision.model_copy(update=overrides)
    return decision


def test_autonomy_risk_classifier_is_review_only_exact_bound_and_non_authoritative() -> None:
    decision = _decision()

    assert decision.classification_valid_for_review is True
    assert decision.review_only is True
    assert decision.deterministic is True
    assert decision.declared_risk_class == AutonomyRiskClass.low
    assert decision.derived_risk_class == AutonomyRiskClass.low
    assert decision.authority_granted is False
    assert decision.policy_activation_requested is False
    assert decision.session_start_requested is False
    assert decision.execution_performed is False
    assert decision.side_effects_performed == []
    assert decision.reason_codes == [
        "M68_AUTONOMY_RISK_CLASSIFICATION_REVIEW_ONLY",
        "M68_DERIVED_RISK_LOW",
    ]


def test_autonomy_risk_classifier_highest_signal_wins_over_declared_risk() -> None:
    request = _request(
        declared_risk_class=AutonomyRiskClass.low,
        risk_signals=[
            AutonomyRiskSignal(
                signal_ref="autonomy-risk-signal:m68-shell-intent",
                signal_kind=AutonomyRiskSignalKind.shell_intent,
                risk_class=AutonomyRiskClass.critical,
                source_ref="intent:shell-dry-run-review",
                reason_code="M68_SIGNAL_SHELL_INTENT_CRITICAL",
            )
        ],
    )
    decision = build_autonomy_risk_classification_decision(request)

    assert decision.declared_risk_class == AutonomyRiskClass.low
    assert decision.derived_risk_class == AutonomyRiskClass.critical
    assert "M68_DERIVED_RISK_CRITICAL" in decision.reason_codes


def test_autonomy_risk_classifier_bundle_risk_wins_over_declared_risk() -> None:
    scope = _scope(risk_class=AutonomyRiskClass.high)
    bundle = _bundle(source_scope=scope, risk_class=AutonomyRiskClass.high)
    decision = build_autonomy_risk_classification_decision(
        _request(approval_bundle=bundle, declared_risk_class=AutonomyRiskClass.low)
    )

    assert decision.derived_risk_class == AutonomyRiskClass.high


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authority_granted", "AUTONOMY_RISK_CLASSIFIER_AUTHORITY_DENIED"),
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
    ],
)
def test_autonomy_risk_classifier_denies_authority_and_activation_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_autonomy_risk_classification_decision(_decision(**{field: True}))


def test_autonomy_risk_classifier_denies_risk_downgrade_and_revalidates_inputs() -> None:
    critical_decision = _decision(
        classification_request=_request(
            risk_signals=[
                AutonomyRiskSignal(
                    signal_ref="autonomy-risk-signal:m68-network-intent",
                    signal_kind=AutonomyRiskSignalKind.network_intent,
                    risk_class=AutonomyRiskClass.critical,
                    source_ref="intent:network-review",
                    reason_code="M68_SIGNAL_NETWORK_INTENT_CRITICAL",
                )
            ]
        )
    )
    with pytest.raises(ValueError, match="AUTONOMY_RISK_DOWNGRADE_DENIED"):
        validate_autonomy_risk_classification_decision(
            critical_decision.model_copy(update={"derived_risk_class": AutonomyRiskClass.low})
        )

    mutated_bundle = _bundle().model_copy(update={"authority_granted": True})
    with pytest.raises(ValueError, match="AUTONOMY_POLICY_AUTHORITY_DENIED"):
        validate_autonomy_risk_classification_decision(
            _decision().model_copy(
                update={"classification_request": _request(approval_bundle=mutated_bundle)}
            )
        )


def test_autonomy_risk_classifier_denies_binding_drift_test_refs_and_secret_metadata() -> None:
    for update, reason in [
        ({"approval_test_ref": "approval_test_:m68"}, "APPROVAL_TEST_REF_DENIED"),
        ({"bundle_ref": "scoped-approval-bundle:other"}, "AUTONOMY_RISK_BUNDLE_BINDING_MISMATCH_DENIED"),
        ({"revocation_record_ref": "revocation-kill-switch-record:other"}, "AUTONOMY_RISK_REVOCATION_RECORD_BINDING_MISMATCH_DENIED"),
        ({"actor_ref": "actor:other-reviewer"}, "AUTONOMY_RISK_ACTOR_BINDING_MISMATCH_DENIED"),
        ({"resource_refs": ["resource:other"]}, "AUTONOMY_RISK_RESOURCE_BINDING_MISMATCH_DENIED"),
        ({"capability_refs": ["capability:other"]}, "AUTONOMY_RISK_CAPABILITY_BINDING_MISMATCH_DENIED"),
        ({"allowlist_refs": ["allowlist:other"]}, "AUTONOMY_RISK_ALLOWLIST_BINDING_MISMATCH_DENIED"),
        ({"metadata": {"api_key": "secret-value"}}, "SECRET_LIKE_AUTONOMY_RISK_CONTENT_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_autonomy_risk_classification_decision(_decision().model_copy(update=update))


def test_autonomy_risk_classifier_denies_side_effects_and_signal_authority() -> None:
    with pytest.raises(ValueError, match="AUTONOMY_SIDE_EFFECTS_DENIED"):
        validate_autonomy_risk_classification_decision(
            _decision(side_effects_performed=["risk-classification:persisted"])
        )

    signal = AutonomyRiskSignal(
        signal_ref="autonomy-risk-signal:m68-authority",
        signal_kind=AutonomyRiskSignalKind.approval_ref,
        risk_class=AutonomyRiskClass.medium,
        source_ref="approval:m68-review",
        reason_code="M68_SIGNAL_APPROVAL_REF_MEDIUM",
        authority_granted=True,
    )
    with pytest.raises(ValueError, match="AUTONOMY_RISK_SIGNAL_AUTHORITY_DENIED"):
        build_autonomy_risk_classification_decision(_request(risk_signals=[signal]))

