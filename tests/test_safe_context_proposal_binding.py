from typing import Any
import pytest

from ultimate_ai_agent.core.context_proposal import (
    SafeContextProposalDecisionStatus,
    build_safe_context_proposal,
    evaluate_safe_context_proposal,
    evaluate_safe_context_proposal_request,
)

from tests.context_proposal_fixtures import (
    approved_context_proposal_record,
    context_proposal_packet,
    denied_context_proposal_record,
)


def test_missing_approved_review_is_denied_and_approval_ref_alone_is_not_authority() -> None:
    packet = context_proposal_packet()
    decision = evaluate_safe_context_proposal_request(
        packet=packet,
        approval_record=None,
        approval_ref="file-review-approval-capture:context-proposal",
    )

    assert decision.status == SafeContextProposalDecisionStatus.requires_approved_review
    assert "approval_ref_not_authority" in decision.reason_codes
    assert "missing_approved_review" in decision.reason_codes
    assert decision.proposal_ready is False
    assert decision.context_injection_authorized is False


def test_denied_review_record_does_not_build_context_proposal() -> None:
    packet = context_proposal_packet()
    approval_record = denied_context_proposal_record(packet)

    decision = evaluate_safe_context_proposal_request(packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert "approval_denied" in decision.reason_codes
    assert decision.proposal is None


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"approval_ref": "approval_test_m38"}, "approval_test_ref_denied"),
        ({"actor_ref": "user:other"}, "actor_ref_mismatch"),
        ({"review_packet_ref": "file-review-packet:other"}, "review_packet_mismatch"),
        ({"preview_result_ref": "redacted-file-preview-output:other"}, "preview_result_mismatch"),
        ({"redaction_summary_ref": "file-review-redaction-summary:other"}, "redaction_summary_mismatch"),
        ({"file_ref": "file-ref:other"}, "file_ref_mismatch"),
        ({"safe_path_ref": "filesystem-preview-path:safe-root_context_proposal/docs/other.md"}, "path_ref_mismatch"),
    ],
)
def test_exact_approval_record_binding_is_enforced(override: Any, reason: str) -> None:
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet).model_copy(update=override)

    decision = evaluate_safe_context_proposal_request(packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.proposal_ready is False


def test_model_copy_mutated_proposal_source_path_ref_is_revalidated() -> None:
    packet = context_proposal_packet()
    approval_record = approved_context_proposal_record(packet)
    proposal = build_safe_context_proposal(packet=packet, approval_record=approval_record)
    mutated = proposal.model_copy(
        update={
            "binding": proposal.binding.model_copy(
                update={"safe_path_ref": "filesystem-preview-path:safe-root_context_proposal/docs/mutated.md"}
            )
        }
    )

    decision = evaluate_safe_context_proposal(mutated, packet=packet, approval_record=approval_record)

    assert decision.status == SafeContextProposalDecisionStatus.denied
    assert "path_ref_mismatch" in decision.reason_codes
    assert decision.execution_authorized is False
