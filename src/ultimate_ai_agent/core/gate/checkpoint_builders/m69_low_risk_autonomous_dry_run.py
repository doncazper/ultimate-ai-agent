from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    AutonomyRiskClass,
    LowRiskAutonomousDryRunRequest,
    LowRiskAutonomousDryRunStep,
    build_low_risk_autonomous_dry_run_record,
    validate_low_risk_autonomous_dry_run_record,
)
from ultimate_ai_agent.core.gate.checkpoint_builders.m68_autonomy_risk_classifier import _decision as _risk_decision
from ultimate_ai_agent.core.gate.checkpoint_builders.m68_autonomy_risk_classifier import _request as _risk_request


def _step(**overrides: Any) -> Any:
    data = {
        "step_ref": "low-risk-dry-run-step:m69-inspect-redacted-review",
        "intent_ref": "intent:inspect-redacted-review-packet",
        "capability_ref": "capability:observe-only-review",
        "resource_ref": "resource:local-prototype",
        "risk_class": AutonomyRiskClass.low,
        "dry_run_outcome_ref": "dry-run-outcome:m69-review-only",
    }
    data.update(overrides)
    return LowRiskAutonomousDryRunStep(**data)


def _request(**overrides: Any) -> Any:
    risk_decision = overrides.pop("risk_decision", _risk_decision())
    data = {
        "dry_run_request_ref": "low-risk-autonomous-dry-run-request:m69-local-review",
        "risk_decision": risk_decision,
        "risk_decision_ref": risk_decision.decision_ref,
        "actor_ref": risk_decision.actor_ref,
        "resource_refs": list(risk_decision.resource_refs),
        "capability_refs": list(risk_decision.capability_refs),
        "allowlist_refs": list(risk_decision.allowlist_refs),
        "bundle_ref": risk_decision.bundle_ref,
        "revocation_record_ref": risk_decision.revocation_record_ref,
        "source_scope_ref": risk_decision.source_scope_ref,
        "audit_ref": risk_decision.audit_ref,
        "replay_ref": risk_decision.replay_ref,
        "steps": [_step()],
    }
    data.update(overrides)
    return LowRiskAutonomousDryRunRequest(**data)


def _record(**overrides: Any) -> Any:
    request = overrides.pop("dry_run_request", _request())
    record = build_low_risk_autonomous_dry_run_record(request)
    if overrides:
        return record.model_copy(update=overrides)
    return record
