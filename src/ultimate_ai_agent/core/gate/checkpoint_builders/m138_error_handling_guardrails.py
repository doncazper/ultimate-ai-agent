from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    ErrorHandlingGuardrailDecision,
    ErrorHandlingGuardrailPolicy,
    ErrorHandlingGuardrailRequest,
    ErrorHandlingGuardrailStatus,
    build_error_handling_guardrail_decision,
    validate_error_handling_guardrail_decision,
    validate_error_handling_guardrail_policy,
    validate_error_handling_guardrail_request,
)
from ultimate_ai_agent.core.autonomy.error_handling_guardrails import (
    ERROR_HANDLING_GUARDRAILS_DOCS,
    M138_MAX_ERROR_SIGNAL_REFS,
)


def _request(**updates: Any) -> ErrorHandlingGuardrailRequest:
    payload = {
        "request_ref": "error-handling-guardrail-request:test",
        "guardrail_plan_ref": "error-handling-guardrail-plan:test",
        "mode_ref": "autonomy-mode:trusted-recurring-automation",
        "actor_ref": "actor:test",
        "user_ref": "user:test",
        "workspace_ref": "workspace:test",
        "scope_ref": "scope:test",
        "resource_refs": ["resource:test"],
        "capability_refs": ["capability:error-guardrail-review"],
        "allowlist_refs": ["allowlist:test"],
        "m137_combined_workflow_decision_ref": (
            "browser-connector-combined-workflow-decision:test"
        ),
        "m136_dependency_execution_decision_ref": (
            "cross-tool-dependency-execution-decision:test"
        ),
        "m135_recovery_planner_decision_ref": "autonomous-recovery-decision:test",
        "m134_human_checkpoint_decision_ref": "human-checkpoint-decision:test",
        "m133_supervisor_decision_ref": "long-running-supervisor-decision:test",
        "m132_trusted_workflow_decision_ref": "trusted-workflow-decision:test",
        "error_signal_refs": ["error-signal:primary"],
        "guardrail_policy_ref": "error-guardrail-policy:test",
        "failure_mode_ref": "failure-mode:transient",
        "retry_policy_ref": "retry-policy:review-only",
        "fallback_policy_ref": "fallback-policy:review-only",
        "escalation_policy_ref": "escalation-policy:human-checkpoint",
        "recovery_plan_ref": "recovery-plan:review-only",
        "rollback_plan_ref": "rollback-plan:review-only",
        "resume_plan_ref": "resume-plan:review-only",
        "human_checkpoint_ref": "human-checkpoint:test",
        "risk_decision_ref": "risk-decision:low",
        "audit_ref": "audit:error-guardrail",
        "replay_ref": "replay:error-guardrail",
        "revocation_ref": "revocation:error-guardrail",
        "kill_switch_ref": "kill-switch:error-guardrail",
        "no_effect_receipt_plan_ref": "receipt-plan:error-guardrail",
        "max_error_signals": M138_MAX_ERROR_SIGNAL_REFS,
        "max_guardrail_refs": 8,
        "safe_guardrail_summary": (
            "Review-only error handling guardrails for a low-risk scoped workflow."
        ),
    }
    payload.update(updates)
    return ErrorHandlingGuardrailRequest(**payload)
