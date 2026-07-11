from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m92_low_risk_tool_autonomy_single_session import _request as _m92_request
from ultimate_ai_agent.core.autonomy import (
    MultiToolDryRunPromotionRequest,
    build_low_risk_tool_autonomy_single_session_decision,
)


def _m92_decision() -> Any:
    return build_low_risk_tool_autonomy_single_session_decision(_m92_request())


def _request(**overrides: Any) -> Any:
    m92_decision = overrides.pop("m92_single_session_decision", _m92_decision())
    data = {
        "request_ref": "multi-tool-dry-run-promotion-request:m93",
        "promotion_ref": "multi-tool-dry-run-promotion:m93-review-only",
        "m92_single_session_decision_ref": m92_decision.decision_ref,
        "m92_single_session_decision": m92_decision,
        "actor_ref": m92_decision.actor_ref,
        "promotion_approval_ref": "approval:promotion-m93-exact-plan",
        "dry_run_plan_ref": "dry-run-plan:m93-redacted-review",
        "dry_run_plan_hash_ref": "plan-hash:m93-dry-run",
        "dry_run_plan_hash": "sha256:m93-equivalent-plan-0001",
        "real_run_plan_ref": "real-run-plan:m93-redacted-review",
        "real_run_plan_hash_ref": "plan-hash:m93-real-run",
        "real_run_plan_hash": "sha256:m93-equivalent-plan-0001",
        "safe_execution_scope_ref": m92_decision.safe_execution_scope_ref,
        "audit_ref": m92_decision.audit_ref,
        "replay_ref": m92_decision.replay_ref,
        "safe_tool_refs": [
            m92_decision.safe_tool_ref,
            "tool:m93-low-risk-review-only-second-tool",
        ],
        "prior_milestone_refs": ["milestone:M69", "milestone:M91", "milestone:M92"],
        "safe_promotion_summary": (
            "Compare a dry-run plan and proposed real-run plan for review without execution."
        ),
    }
    data.update(overrides)
    return MultiToolDryRunPromotionRequest(**data)
