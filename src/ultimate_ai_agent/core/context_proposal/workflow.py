from __future__ import annotations

from ultimate_ai_agent.core.context_proposal.contracts import (
    SafeContextProposal,
    SafeContextProposalBinding,
    SafeContextProposalDecision,
    SafeContextProposalPolicy,
    SafeContextProposalRedactionVerification,
    SafeContextProposalSection,
    SafeContextProposalSource,
)
from ultimate_ai_agent.core.context_proposal.enums import SafeContextProposalDecisionStatus
from ultimate_ai_agent.core.context_proposal.policy import build_safe_context_proposal_policy
from ultimate_ai_agent.core.context_proposal.receipts import (
    build_safe_context_proposal_receipt_plan,
    context_proposal_suffix,
)
from ultimate_ai_agent.core.context_proposal.validation import (
    validate_safe_context_proposal,
    validate_safe_context_proposal_request,
)
from ultimate_ai_agent.core.file_review.approval_capture import FileReviewApprovalRecord
from ultimate_ai_agent.core.file_review.contracts import FileReviewPacket


def build_safe_context_proposal(
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
    policy: SafeContextProposalPolicy | None = None,
) -> SafeContextProposal:
    reasons = validate_safe_context_proposal_request(
        packet=packet,
        approval_record=approval_record,
        policy=policy or SafeContextProposalPolicy(),
    )
    if reasons:
        raise ValueError(",".join(reasons))
    suffix = context_proposal_suffix(packet.review_packet_ref)
    source_chain_refs = [
        approval_record.approval_ref,
        packet.review_packet_ref,
        packet.source.preview_result_ref,
        packet.redaction_verification.redaction_summary_ref,
        packet.source.file_ref,
        packet.source.safe_path_ref,
    ]
    source = SafeContextProposalSource(
        approval_ref=approval_record.approval_ref,
        approval_record_ref=approval_record.approval_ref,
        review_packet_ref=packet.review_packet_ref,
        preview_result_ref=packet.source.preview_result_ref,
        redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        file_ref=packet.source.file_ref,
        safe_path_ref=packet.source.safe_path_ref,
        actor_ref=packet.source.actor_ref,
        source_chain_refs=source_chain_refs,
    )
    binding = SafeContextProposalBinding(
        approval_ref=approval_record.approval_ref,
        review_packet_ref=packet.review_packet_ref,
        preview_result_ref=packet.source.preview_result_ref,
        redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        file_ref=packet.source.file_ref,
        safe_path_ref=packet.source.safe_path_ref,
        actor_ref=packet.source.actor_ref,
    )
    section = SafeContextProposalSection(
        section_ref=f"safe-context-proposal-section:{suffix}:redacted-preview",
        title="Redacted review excerpt",
        content=_bounded(packet.redacted_preview),
        source_ref=packet.source.preview_result_ref,
    )
    return SafeContextProposal(
        proposal_ref=f"safe-context-proposal:{suffix}",
        source=source,
        binding=binding,
        redaction_verification=SafeContextProposalRedactionVerification(
            verification_ref=f"safe-context-proposal-redaction-verification:{suffix}",
            redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
        ),
        sections=[section],
        safe_summary="Safe context proposal built from an approved redacted review packet. It is proposal-only and non-authoritative.",
        metadata_refs=[approval_record.receipt_plan_ref] if approval_record.receipt_plan_ref else [],
    )


def evaluate_safe_context_proposal_request(
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord | None,
    approval_ref: str | None = None,
    policy: SafeContextProposalPolicy | None = None,
    policy_overrides: dict | None = None,
) -> SafeContextProposalDecision:
    active_policy = policy or build_safe_context_proposal_policy()
    if policy_overrides:
        active_policy = active_policy.model_copy(update=policy_overrides)
    reasons = validate_safe_context_proposal_request(
        packet=packet,
        approval_record=approval_record,
        approval_ref=approval_ref,
        policy=active_policy,
    )
    reasons = _dedupe(reasons)
    if reasons:
        status = SafeContextProposalDecisionStatus.requires_approved_review
        if "missing_approved_review" not in reasons and any(reason != "missing_approved_review" for reason in reasons):
            status = SafeContextProposalDecisionStatus.denied
        return _denied_decision(
            review_packet_ref=getattr(packet, "review_packet_ref", "file-review-packet:invalid"),
            reasons=reasons,
            status=status,
        )
    proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record, policy=active_policy)  # type: ignore[arg-type]
    return evaluate_safe_context_proposal(
        proposal,
        packet=packet,
        approval_record=approval_record,  # type: ignore[arg-type]
        policy=active_policy,
    )


def evaluate_safe_context_proposal(
    proposal: SafeContextProposal,
    *,
    packet: FileReviewPacket,
    approval_record: FileReviewApprovalRecord,
    policy: SafeContextProposalPolicy | None = None,
) -> SafeContextProposalDecision:
    reasons = validate_safe_context_proposal(
        proposal,
        packet=packet,
        approval_record=approval_record,
        policy=policy or SafeContextProposalPolicy(),
    )
    reasons = _dedupe(reasons)
    if reasons:
        return _denied_decision(review_packet_ref=getattr(packet, "review_packet_ref", "file-review-packet:invalid"), reasons=reasons)
    receipt = build_safe_context_proposal_receipt_plan(proposal)
    return SafeContextProposalDecision(
        decision_ref=f"safe-context-proposal-decision:{context_proposal_suffix(proposal.proposal_ref)}",
        status=SafeContextProposalDecisionStatus.proposal_ready,
        proposal_ready=True,
        reason_codes=["proposal_ready"],
        safe_message="Safe context proposal is ready for future review only. No injection, memory, export, model call, or execution authority was granted.",
        proposal=proposal,
        receipt_plan=receipt,
    )


def _denied_decision(
    *,
    review_packet_ref: str,
    reasons: list[str],
    status: SafeContextProposalDecisionStatus = SafeContextProposalDecisionStatus.denied,
) -> SafeContextProposalDecision:
    return SafeContextProposalDecision(
        decision_ref=f"safe-context-proposal-decision:{context_proposal_suffix(review_packet_ref)}",
        status=status,
        proposal_ready=False,
        reason_codes=_dedupe(reasons),
        safe_message="Safe context proposal was denied. No raw content, context injection, OpenWebUI handoff, memory write, export, model call, or execution authority was granted.",
    )


def _bounded(value: str, limit: int = 1200) -> str:
    return value if len(value) <= limit else value[:limit]


def _dedupe(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))
