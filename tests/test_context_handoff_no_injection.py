import pytest

from ultimate_ai_agent.core.context_handoff import (
    ContextHandoffApprovalDecisionStatus,
    evaluate_context_handoff_approval,
)

from tests.test_context_handoff_approval_contracts import _proposal, _request


@pytest.mark.parametrize(
    "field,reason",
    [
        ("context_handoff_enabled", "handoff_execution_denied"),
        ("context_injection_enabled", "context_injection_denied"),
        ("openwebui_handoff_enabled", "openwebui_handoff_denied"),
        ("model_call_enabled", "model_call_denied"),
        ("memory_write_enabled", "memory_write_denied"),
        ("export_enabled", "export_denied"),
        ("execution_enabled", "execution_denied"),
        ("raw_file_access_enabled", "raw_content_present"),
        ("raw_content_stored", "raw_content_present"),
        ("full_file_content_stored", "full_file_content_present"),
        ("unredacted_preview_stored", "unredacted_preview_present"),
    ],
)
def test_model_copy_mutated_proposal_safety_fields_are_revalidated(field, reason):
    proposal = _proposal()
    mutated = proposal.model_copy(update={field: True})

    decision = evaluate_context_handoff_approval(proposal=mutated, request=_request(proposal))

    assert decision.status == ContextHandoffApprovalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.handoff_approved_for_review is False
    assert decision.context_injection_authorized is False
    assert decision.openwebui_handoff_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


@pytest.mark.parametrize(
    "field,reason",
    [
        ("context_injection_enabled", "context_injection_denied"),
        ("openwebui_handoff_execution_enabled", "openwebui_handoff_denied"),
        ("model_call_enabled", "model_call_denied"),
        ("memory_write_enabled", "memory_write_denied"),
        ("export_enabled", "export_denied"),
        ("execution_enabled", "execution_denied"),
        ("raw_file_access_enabled", "raw_content_present"),
        ("backend_route_enabled", "future_milestone_required"),
    ],
)
def test_model_copy_mutated_request_authority_flags_are_revalidated(field, reason):
    proposal = _proposal()
    request = _request(proposal).model_copy(update={field: True})

    decision = evaluate_context_handoff_approval(proposal=proposal, request=request)

    assert decision.status == ContextHandoffApprovalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.handoff_approved_for_review is False
    assert decision.context_injection_authorized is False
    assert decision.openwebui_handoff_authorized is False
    assert decision.execution_authorized is False
