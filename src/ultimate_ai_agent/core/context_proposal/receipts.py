from __future__ import annotations

from ultimate_ai_agent.core.context_proposal.contracts import SafeContextProposal, SafeContextProposalReceiptPlan


def context_proposal_suffix(ref: str) -> str:
    return ref.split(":", 1)[-1].replace("/", "-")


def build_safe_context_proposal_receipt_plan(proposal: SafeContextProposal) -> SafeContextProposalReceiptPlan:
    return SafeContextProposalReceiptPlan(
        receipt_plan_ref=f"safe-context-proposal-receipt:{context_proposal_suffix(proposal.proposal_ref)}",
        proposal_ref=proposal.proposal_ref,
        approval_ref=proposal.binding.approval_ref,
        review_packet_ref=proposal.binding.review_packet_ref,
        preview_result_ref=proposal.binding.preview_result_ref,
        redaction_summary_ref=proposal.binding.redaction_summary_ref,
        file_ref=proposal.binding.file_ref,
        safe_path_ref=proposal.binding.safe_path_ref,
        actor_ref=proposal.binding.actor_ref,
    )
