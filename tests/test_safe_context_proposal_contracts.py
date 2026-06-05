from ultimate_ai_agent.core.context_proposal import (
    SafeContextProposalDecisionStatus,
    SafeContextProposalPolicy,
    SafeContextProposalStatus,
    build_safe_context_proposal,
    build_safe_context_proposal_policy,
    evaluate_safe_context_proposal,
)

from tests.context_proposal_fixtures import approved_context_proposal_record, context_proposal_packet


def test_default_context_proposal_policy_is_proposal_only_and_non_authoritative():
    policy = build_safe_context_proposal_policy()

    assert isinstance(policy, SafeContextProposalPolicy)
    assert SafeContextProposalStatus.proposal_ready == SafeContextProposalDecisionStatus.proposal_ready
    assert policy.context_proposal_enabled is True
    assert policy.proposal_only_enabled is True
    assert policy.context_surface_enabled is False
    assert policy.context_handoff_enabled is False
    assert policy.context_injection_enabled is False
    assert policy.openwebui_handoff_enabled is False
    assert policy.model_call_enabled is False
    assert policy.memory_write_enabled is False
    assert policy.export_enabled is False
    assert policy.execution_enabled is False
    assert policy.raw_file_access_enabled is False
    assert policy.raw_content_enabled is False
    assert policy.full_file_read_enabled is False
    assert policy.unredacted_preview_enabled is False
    assert policy.backend_route_enabled is False
    assert policy.control_center_surface_enabled is False


def test_valid_approved_review_builds_non_authoritative_context_proposal():
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)

    proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)
    decision = evaluate_safe_context_proposal(proposal, packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.proposal_ready
    assert decision.proposal_ready is True
    assert decision.proposal is not None
    assert proposal.non_authoritative is True
    assert proposal.proposal_only is True
    assert proposal.no_context_injection is True
    assert proposal.source.approval_ref == approval_record.approval_ref
    assert proposal.binding.review_packet_ref == packet.review_packet_ref
    assert proposal.binding.preview_result_ref == packet.source.preview_result_ref
    assert proposal.binding.redaction_summary_ref == packet.redaction_verification.redaction_summary_ref
    assert proposal.binding.file_ref == packet.source.file_ref
    assert proposal.binding.safe_path_ref == packet.source.safe_path_ref
    assert proposal.binding.actor_ref == packet.source.actor_ref
    assert proposal.redaction_verification.redacted_review_material_only is True
    assert decision.context_injection_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False
