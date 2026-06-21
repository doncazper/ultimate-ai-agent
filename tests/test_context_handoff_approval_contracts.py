from typing import Any
from ultimate_ai_agent.core.context_handoff import (
    ContextHandoffApprovalDecisionStatus,
    ContextHandoffApprovalKind,
    ContextHandoffApprovalPolicy,
    ContextHandoffApprovalRequest,
    build_context_handoff_approval_policy,
    evaluate_context_handoff_approval,
)

from tests.context_proposal_fixtures import (
    approved_context_proposal_record,
    context_proposal_packet,
)


def _proposal() -> Any:
    from ultimate_ai_agent.core.context_proposal import build_safe_context_proposal

    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)
    return build_safe_context_proposal(packet=packet, approval_record=approval_record)


def _request(proposal: Any | None = None, **overrides: Any) -> Any:
    active = proposal or _proposal()
    data = {
        "approval_ref": "context-handoff-approval:m40",
        "actor_ref": active.binding.actor_ref,
        "proposal_ref": active.proposal_ref,
        "approval_record_ref": active.source.approval_record_ref,
        "review_packet_ref": active.binding.review_packet_ref,
        "preview_result_ref": active.binding.preview_result_ref,
        "redaction_summary_ref": active.binding.redaction_summary_ref,
        "file_ref": active.binding.file_ref,
        "safe_path_ref": active.binding.safe_path_ref,
        "decision": ContextHandoffApprovalKind.approve_handoff_review_only,
        "idempotency_key": "context-handoff-idempotency:m40",
        "safe_reason": "Approve the safe context proposal for future handoff review only.",
    }
    data.update(overrides)
    return ContextHandoffApprovalRequest(**data)


def test_default_handoff_policy_is_contract_only_and_no_injection() -> None:
    policy = build_context_handoff_approval_policy()

    assert isinstance(policy, ContextHandoffApprovalPolicy)
    assert policy.context_handoff_approval_enabled is True
    assert policy.exact_proposal_binding_required is True
    assert policy.no_injection_required is True
    assert policy.context_injection_enabled is False
    assert policy.openwebui_handoff_execution_enabled is False
    assert policy.model_call_enabled is False
    assert policy.memory_write_enabled is False
    assert policy.export_enabled is False
    assert policy.execution_enabled is False
    assert policy.backend_route_enabled is False
    assert policy.production_authority_enabled is False


def test_valid_handoff_approval_is_review_only_and_performs_no_handoff_or_injection() -> None:
    proposal = _proposal()
    decision = evaluate_context_handoff_approval(proposal=proposal, request=_request(proposal))

    assert decision.status == ContextHandoffApprovalDecisionStatus.approved_for_handoff_review_only
    assert decision.handoff_approved_for_review is True
    assert decision.handoff_execution_authorized is False
    assert decision.context_injection_authorized is False
    assert decision.openwebui_handoff_authorized is False
    assert decision.model_call_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.context_injection_performed is False
    assert decision.openwebui_handoff_performed is False
    assert decision.execution_performed is False
    assert decision.receipt_plan is not None
    assert decision.receipt_plan.raw_content_stored is False
    assert decision.receipt_plan.context_injection_performed is False
    assert decision.receipt_plan.openwebui_handoff_performed is False


def test_approval_ref_alone_cannot_authorize_handoff() -> None:
    decision = evaluate_context_handoff_approval(
        proposal=None,
        request_ref="context-handoff-approval:m40",
    )

    assert decision.status == ContextHandoffApprovalDecisionStatus.requires_context_proposal
    assert "proposal_required" in decision.reason_codes
    assert "approval_ref_not_authority" in decision.reason_codes
    assert decision.handoff_approved_for_review is False
    assert decision.context_injection_authorized is False
