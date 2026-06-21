from typing import Any
import pytest

from ultimate_ai_agent.core.context_proposal import (
    SafeContextProposalDecisionStatus,
    build_safe_context_proposal,
    evaluate_safe_context_proposal,
    evaluate_safe_context_proposal_request,
)

from tests.context_proposal_fixtures import approved_context_proposal_record, context_proposal_packet


@pytest.mark.parametrize(
    "extra_field,reason",
    [
        ("raw_content", "raw_content_present"),
        ("full_file_content", "full_file_content_present"),
        ("unredacted_preview", "unredacted_preview_present"),
    ],
)
def test_model_copy_mutated_raw_or_unredacted_proposal_fields_are_denied(extra_field: Any, reason: str) -> None:
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)
    proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)
    mutated = proposal.model_copy(update={extra_field: "do not expose this raw material"})

    decision = evaluate_safe_context_proposal(mutated, packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert "do not expose" not in decision.safe_message
    assert "do not expose" not in str(decision.model_dump(mode="json"))


def test_secret_like_proposal_section_content_is_denied_without_echoing_secret() -> None:
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)
    proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)
    bad_section = proposal.sections[0].model_copy(update={"content": "api_key='abc123supersecret'"})
    mutated = proposal.model_copy(update={"sections": [bad_section]})

    decision = evaluate_safe_context_proposal(mutated, packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert "unsafe_section_content" in decision.reason_codes
    assert "abc123supersecret" not in decision.safe_message
    assert "abc123supersecret" not in str(decision.model_dump(mode="json"))


def test_raw_review_packet_material_is_denied_before_proposal_build() -> None:
    packet = context_proposal_packet().model_copy(update={"raw_content": "raw file body"})
    approval_record = approved_context_proposal_record(context_proposal_packet())

    decision = evaluate_safe_context_proposal_request(packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert "raw_content_present" in decision.reason_codes
    assert decision.proposal is None
