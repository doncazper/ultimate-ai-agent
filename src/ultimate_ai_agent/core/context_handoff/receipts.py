from __future__ import annotations

from ultimate_ai_agent.core.context_handoff.contracts import (
    ContextHandoffApprovalReceiptPlan,
    ContextHandoffApprovalRequest,
)
from ultimate_ai_agent.core.context_proposal.contracts import SafeContextProposal


def context_handoff_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")


def build_context_handoff_approval_receipt_plan(
    *,
    proposal: SafeContextProposal,
    request: ContextHandoffApprovalRequest,
) -> ContextHandoffApprovalReceiptPlan:
    return ContextHandoffApprovalReceiptPlan(
        receipt_plan_ref=f"context-handoff-approval-receipt:{context_handoff_suffix(request.approval_ref)}",
        approval_ref=request.approval_ref,
        proposal_ref=proposal.proposal_ref,
        approval_record_ref=proposal.source.approval_record_ref,
        review_packet_ref=proposal.binding.review_packet_ref,
        preview_result_ref=proposal.binding.preview_result_ref,
        redaction_summary_ref=proposal.binding.redaction_summary_ref,
        file_ref=proposal.binding.file_ref,
        safe_path_ref=proposal.binding.safe_path_ref,
        actor_ref=proposal.binding.actor_ref,
    )
