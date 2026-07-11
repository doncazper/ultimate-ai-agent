from __future__ import annotations
from typing import Any
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
