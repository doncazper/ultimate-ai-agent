from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    ABUSE_LOOP_DETECTION_DOCS,
    M139_MAX_SIGNAL_REFS,
    AbuseLoopDetectionDecision,
    AbuseLoopDetectionPolicy,
    AbuseLoopDetectionRequest,
    AbuseLoopDetectionStatus,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    build_abuse_loop_detection_decision,
    validate_abuse_loop_detection_decision,
    validate_abuse_loop_detection_policy,
    validate_abuse_loop_detection_request,
)


def _request(**updates: Any) -> AbuseLoopDetectionRequest:
    payload = {
        "request_ref": "abuse-loop-detection-request:test",
        "detection_plan_ref": "abuse-loop-detection-plan:test",
        "mode_ref": "autonomy-mode:trusted-recurring-automation",
        "actor_ref": "actor:test",
        "user_ref": "user:test",
        "workspace_ref": "workspace:test",
        "scope_ref": "scope:test",
        "resource_refs": ["resource:test"],
        "capability_refs": ["capability:abuse-loop-review"],
        "allowlist_refs": ["allowlist:test"],
        "m138_error_guardrail_decision_ref": "error-handling-guardrail-decision:test",
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
        "abuse_signal_refs": ["abuse-signal:prompt-loop-risk"],
        "loop_signal_refs": ["loop-signal:repeated-plan"],
        "pattern_policy_ref": "abuse-loop-pattern-policy:test",
        "threshold_policy_ref": "abuse-loop-threshold-policy:test",
        "intervention_plan_ref": "loop-intervention-plan:review-only",
        "escalation_plan_ref": "loop-escalation-plan:human-checkpoint",
        "human_checkpoint_ref": "human-checkpoint:test",
        "risk_decision_ref": "risk-decision:low",
        "audit_ref": "audit:abuse-loop",
        "replay_ref": "replay:abuse-loop",
        "revocation_ref": "revocation:abuse-loop",
        "kill_switch_ref": "kill-switch:abuse-loop",
        "no_effect_receipt_plan_ref": "receipt-plan:abuse-loop",
        "max_signal_refs": M139_MAX_SIGNAL_REFS,
        "max_pattern_refs": 8,
        "safe_detection_summary": (
            "Review-only abuse and loop detection refs for a scoped workflow."
        ),
    }
    payload.update(updates)
    return AbuseLoopDetectionRequest(**payload)
