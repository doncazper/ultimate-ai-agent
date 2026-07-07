from __future__ import annotations
from typing import Any
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
