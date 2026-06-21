from __future__ import annotations
from typing import Any

from datetime import datetime

from ultimate_ai_agent.core.context_handoff.contracts import (
    ContextHandoffApprovalDecision,
    ContextHandoffApprovalPolicy,
    ContextHandoffApprovalRequest,
)
from ultimate_ai_agent.core.context_handoff.enums import (
    ContextHandoffApprovalDecisionStatus,
    ContextHandoffApprovalKind,
)
from ultimate_ai_agent.core.context_handoff.policy import build_context_handoff_approval_policy
from ultimate_ai_agent.core.context_handoff.receipts import (
    build_context_handoff_approval_receipt_plan,
    context_handoff_suffix,
)
from ultimate_ai_agent.core.context_handoff.validation import validate_context_handoff_approval
from ultimate_ai_agent.core.context_proposal.contracts import SafeContextProposal
from ultimate_ai_agent.core.approvals.v2.validation import validate_action_ref


def evaluate_context_handoff_approval(
    *,
    proposal: SafeContextProposal | None,
    request: ContextHandoffApprovalRequest | None = None,
    request_ref: str | None = None,
    policy: ContextHandoffApprovalPolicy | None = None,
    policy_overrides: dict | None = None,
    current_time: datetime | None = None,
) -> ContextHandoffApprovalDecision:
    active_policy = policy or build_context_handoff_approval_policy()
    if policy_overrides:
        active_policy = active_policy.model_copy(update=policy_overrides)
    reasons = validate_context_handoff_approval(
        proposal=proposal,
        request=request,
        policy=active_policy,
        request_ref=request_ref,
        current_time=current_time,
    )
    if reasons:
        status = ContextHandoffApprovalDecisionStatus.denied
        if "proposal_required" in reasons:
            status = ContextHandoffApprovalDecisionStatus.requires_context_proposal
        return _decision(
            status=status,
            reasons=reasons,
            approval_ref=getattr(request, "approval_ref", request_ref),
            proposal_ref=getattr(proposal, "proposal_ref", None),
            handoff_approved=False,
        )
    if request is None or proposal is None:
        return _decision(
            status=ContextHandoffApprovalDecisionStatus.requires_context_proposal,
            reasons=["proposal_required"],
            approval_ref=request_ref,
            proposal_ref=None,
            handoff_approved=False,
        )
    if request.decision == ContextHandoffApprovalKind.deny_handoff_review:
        return _decision(
            status=ContextHandoffApprovalDecisionStatus.denied_for_handoff_review,
            reasons=["handoff_denied_for_review"],
            approval_ref=request.approval_ref,
            proposal_ref=proposal.proposal_ref,
            handoff_approved=False,
        )
    return _decision(
        status=ContextHandoffApprovalDecisionStatus.approved_for_handoff_review_only,
        reasons=["handoff_approved_for_review_only", "no_context_injection"],
        approval_ref=request.approval_ref,
        proposal_ref=proposal.proposal_ref,
        handoff_approved=True,
        receipt_plan=build_context_handoff_approval_receipt_plan(proposal=proposal, request=request),
    )


def _decision(
    *,
    status: ContextHandoffApprovalDecisionStatus,
    reasons: list[str],
    approval_ref: str | None,
    proposal_ref: str | None,
    handoff_approved: bool,
    receipt_plan: Any | None = None,
) -> ContextHandoffApprovalDecision:
    safe_approval_ref = approval_ref if _is_safe_ref(approval_ref, "approval_ref") else None
    suffix_source = safe_approval_ref or proposal_ref or "missing"
    return ContextHandoffApprovalDecision(
        decision_ref=f"context-handoff-approval-decision:{context_handoff_suffix(suffix_source)}",
        status=status,
        approval_ref=safe_approval_ref,
        proposal_ref=proposal_ref,
        handoff_approved_for_review=handoff_approved,
        reason_codes=list(dict.fromkeys(reasons)),
        safe_message=(
            "Context handoff approval is review-only. No context injection, OpenWebUI handoff, "
            "memory write, export, model call, execution, or raw file access was performed."
        ),
        receipt_plan=receipt_plan,
    )


def _is_safe_ref(value: str | None, field_name: str) -> bool:
    if value is None:
        return False
    try:
        validate_action_ref(value, field_name)
    except ValueError:
        return False
    return True
