from ultimate_ai_agent.core.context_handoff import (
    ContextHandoffApprovalKind,
    ContextHandoffApprovalRequest,
    build_context_handoff_approval_receipt_plan,
    evaluate_context_handoff_approval,
)
from ultimate_ai_agent.core.context_proposal import build_safe_context_proposal

from tests.context_proposal_fixtures import (
    approved_context_proposal_record,
    context_proposal_packet,
)


def _proposal():
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)
    return build_safe_context_proposal(packet=packet, approval_record=approval_record)


def _request(proposal):
    return ContextHandoffApprovalRequest(
        approval_ref="context-handoff-approval:receipt",
        actor_ref=proposal.binding.actor_ref,
        proposal_ref=proposal.proposal_ref,
        approval_record_ref=proposal.source.approval_record_ref,
        review_packet_ref=proposal.binding.review_packet_ref,
        preview_result_ref=proposal.binding.preview_result_ref,
        redaction_summary_ref=proposal.binding.redaction_summary_ref,
        file_ref=proposal.binding.file_ref,
        safe_path_ref=proposal.binding.safe_path_ref,
        decision=ContextHandoffApprovalKind.approve_handoff_review_only,
        idempotency_key="context-handoff-idempotency:receipt",
        safe_reason="Approve the safe context proposal for future handoff review only.",
    )


def test_handoff_receipt_plan_stores_only_safe_refs_and_no_authority() -> None:
    proposal = _proposal()
    request = _request(proposal)

    receipt = build_context_handoff_approval_receipt_plan(proposal=proposal, request=request)

    assert receipt.approval_ref == request.approval_ref
    assert receipt.proposal_ref == proposal.proposal_ref
    assert receipt.review_packet_ref == proposal.binding.review_packet_ref
    assert receipt.preview_result_ref == proposal.binding.preview_result_ref
    assert receipt.redaction_summary_ref == proposal.binding.redaction_summary_ref
    assert receipt.file_ref == proposal.binding.file_ref
    assert receipt.safe_path_ref == proposal.binding.safe_path_ref
    assert receipt.receipt_is_authority is False
    assert receipt.raw_content_stored is False
    assert receipt.full_file_content_stored is False
    assert receipt.unredacted_preview_stored is False
    assert receipt.raw_absolute_path_stored is False
    assert receipt.context_injection_performed is False
    assert receipt.openwebui_handoff_performed is False
    assert receipt.model_call_performed is False
    assert receipt.memory_write_performed is False
    assert receipt.export_performed is False
    assert receipt.execution_performed is False


def test_approved_handoff_decision_embeds_non_authoritative_receipt_plan() -> None:
    proposal = _proposal()
    decision = evaluate_context_handoff_approval(proposal=proposal, request=_request(proposal))

    assert decision.receipt_plan is not None
    assert decision.receipt_plan.receipt_is_authority is False
    assert decision.receipt_plan.context_injection_performed is False
    assert decision.receipt_plan.openwebui_handoff_performed is False
    assert decision.receipt_plan.memory_write_performed is False
    assert decision.receipt_plan.export_performed is False
    assert decision.receipt_plan.execution_performed is False
