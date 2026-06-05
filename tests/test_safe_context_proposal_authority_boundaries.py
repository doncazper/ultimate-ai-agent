import pytest

from ultimate_ai_agent.core.context_proposal import SafeContextProposalDecisionStatus, evaluate_safe_context_proposal_request

from tests.context_proposal_fixtures import approved_context_proposal_record, context_proposal_packet


@pytest.mark.parametrize(
    "flag,reason",
    [
        ("context_injection_enabled", "context_injection_denied"),
        ("openwebui_handoff_enabled", "openwebui_handoff_denied"),
        ("model_call_enabled", "model_call_denied"),
        ("memory_write_enabled", "memory_write_denied"),
        ("export_enabled", "export_denied"),
        ("execution_enabled", "execution_denied"),
    ],
)
def test_model_copy_mutated_policy_authority_flags_are_denied(flag, reason):
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)

    decision = evaluate_safe_context_proposal_request(
        packet=packet,
        approval_record=approval_record,
        policy_overrides={flag: True},
    )

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.context_injection_authorized is False
    assert decision.openwebui_handoff_authorized is False
    assert decision.memory_write_authorized is False
    assert decision.export_authorized is False
    assert decision.execution_authorized is False
    assert decision.execution_performed is False


@pytest.mark.parametrize(
    "authority_ref",
    [
        "model-output:summary",
        "memory:recall",
        "context-pack:candidate",
        "tool-intent:file-review",
        "approval:file-review",
        "openwebui-output:chat",
    ],
)
def test_external_authority_refs_cannot_authorize_context_proposal(authority_ref):
    packet = context_proposal_packet().model_copy(update={"authority_refs": [authority_ref]})
    approval_record = approved_context_proposal_record(context_proposal_packet())

    decision = evaluate_safe_context_proposal_request(packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert "approval_ref_not_authority" in decision.reason_codes or "future_milestone_required" in decision.reason_codes
    assert decision.proposal_ready is False
