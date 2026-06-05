from ultimate_ai_agent.core.context_proposal import (
    build_safe_context_proposal,
    build_safe_context_proposal_receipt_plan,
)

from tests.context_proposal_fixtures import approved_context_proposal_record, context_proposal_packet


def test_context_proposal_receipt_plan_stores_refs_only_and_no_raw_content():
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)
    proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)

    receipt = build_safe_context_proposal_receipt_plan(proposal)

    assert receipt.proposal_ref == proposal.proposal_ref
    assert receipt.approval_ref == approval_record.approval_ref
    assert receipt.review_packet_ref == packet.review_packet_ref
    assert receipt.raw_content_stored is False
    assert receipt.full_file_content_stored is False
    assert receipt.unredacted_preview_stored is False
    assert receipt.context_injection_performed is False
    assert receipt.memory_write_performed is False
    assert receipt.export_performed is False
    assert receipt.execution_performed is False
    dumped = receipt.model_dump(mode="json")
    assert "Redacted preview only for context proposal." not in str(dumped)
    assert "abc123supersecret" not in str(dumped)
