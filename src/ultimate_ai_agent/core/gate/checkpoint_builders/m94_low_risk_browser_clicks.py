from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.gate.checkpoint_builders.m93_multi_tool_dry_run_promotion import _request as _m93_request
from ultimate_ai_agent.core.autonomy import build_multi_tool_dry_run_promotion_decision
from ultimate_ai_agent.core.browser import (
    LowRiskBrowserClickPolicy,
    LowRiskBrowserClickRequest,
    LowRiskBrowserClickStatus,
    LowRiskBrowserClickTransportResponse,
    build_low_risk_browser_click_decision,
    perform_low_risk_browser_click,
    validate_low_risk_browser_click_decision,
    validate_low_risk_browser_click_policy,
    validate_low_risk_browser_click_request,
    validate_low_risk_browser_click_result,
)


def _m93_decision() -> Any:
    return build_multi_tool_dry_run_promotion_decision(_m93_request())


def _request(**overrides: Any) -> Any:
    m93_decision = overrides.pop("m93_promotion_decision", _m93_decision())
    data = {
        "request_ref": "low-risk-browser-click-request:m94",
        "click_ref": "low-risk-browser-click:m94-open-safe-details",
        "m93_promotion_decision_ref": m93_decision.decision_ref,
        "m93_promotion_decision": m93_decision,
        "actor_ref": m93_decision.actor_ref,
        "click_approval_ref": "approval:click-m94-safe-details",
        "scoped_session_ref": m93_decision.safe_execution_scope_ref,
        "allowed_page_ref": "browser-page:m94-docs-status",
        "allowed_action_ref": "browser-action:m94-open-safe-details",
        "observed_page_ref": "browser-observe-output:m94-redacted-page",
        "dry_run_plan_ref": m93_decision.dry_run_plan_ref,
        "safe_target_ref": "browser-target:m94-details-button",
        "low_risk_classification_ref": "risk-classification:m94-low-risk-click",
        "audit_ref": m93_decision.audit_ref,
        "replay_ref": m93_decision.replay_ref,
        "revocation_ref": "revocation:m94-click-window",
        "kill_switch_ref": "kill-switch:m94-click-window",
        "prior_milestone_refs": [
            "milestone:M73",
            "milestone:M75",
            "milestone:M91",
            "milestone:M92",
            "milestone:M93",
        ],
        "safe_click_summary": (
            "Activate a safe details disclosure on an allowlisted documentation page."
        ),
    }
    data.update(overrides)
    return LowRiskBrowserClickRequest(**data)


def _transport(_decision: Any) -> Any:
    return LowRiskBrowserClickTransportResponse(
        click_completed=True,
        safe_result_ref="browser-click-result:m94-safe-details-opened",
        safe_summary="Safe details disclosure was activated.",
    )
