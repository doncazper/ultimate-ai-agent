from datetime import timedelta

import pytest

from ultimate_ai_agent.core.context_handoff import (
    ContextHandoffApprovalDecisionStatus,
    evaluate_context_handoff_approval,
)
from ultimate_ai_agent.core.time import utc_now

from tests.test_context_handoff_approval_contracts import _proposal, _request


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"approval_ref": "approval_test_m40"}, "approval_test_ref_denied"),
        ({"actor_ref": "user:other"}, "actor_ref_mismatch"),
        ({"proposal_ref": "safe-context-proposal:other"}, "proposal_ref_mismatch"),
        ({"approval_record_ref": "file-review-approval-capture:other"}, "approval_record_mismatch"),
        ({"review_packet_ref": "file-review-packet:other"}, "review_packet_mismatch"),
        ({"preview_result_ref": "redacted-file-preview-output:other"}, "preview_result_mismatch"),
        ({"redaction_summary_ref": "file-review-redaction-summary:other"}, "redaction_summary_mismatch"),
        ({"file_ref": "file-ref:other"}, "file_ref_mismatch"),
        ({"safe_path_ref": "filesystem-preview-path:safe-root_context_proposal/docs/other.md"}, "path_ref_mismatch"),
    ],
)
def test_context_handoff_approval_requires_exact_proposal_binding(override, reason):
    proposal = _proposal()
    if str(override.get("approval_ref", "")).startswith("approval_test_"):
        request = _request(proposal).model_copy(update=override)
    else:
        request = _request(proposal, **override)
    decision = evaluate_context_handoff_approval(proposal=proposal, request=request)

    assert decision.status == ContextHandoffApprovalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.handoff_approved_for_review is False
    assert decision.context_injection_authorized is False


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"expires_at": utc_now() - timedelta(seconds=1)}, "approval_expired"),
        ({"revoked_at": utc_now()}, "approval_revoked"),
        (
            {
                "replay_nonce": "context-handoff-replay:m40",
                "used_replay_nonces": ["context-handoff-replay:m40"],
            },
            "approval_replayed",
        ),
    ],
)
def test_expired_revoked_and_replayed_handoff_approvals_are_denied(override, reason):
    proposal = _proposal()
    decision = evaluate_context_handoff_approval(proposal=proposal, request=_request(proposal, **override))

    assert decision.status == ContextHandoffApprovalDecisionStatus.denied
    assert reason in decision.reason_codes
    assert decision.handoff_approved_for_review is False


def test_deny_decision_is_review_only_and_non_authoritative():
    proposal = _proposal()
    request = _request(proposal, decision="deny_handoff_review")
    decision = evaluate_context_handoff_approval(proposal=proposal, request=request)

    assert decision.status == ContextHandoffApprovalDecisionStatus.denied_for_handoff_review
    assert decision.handoff_approved_for_review is False
    assert decision.context_injection_authorized is False
    assert decision.execution_authorized is False
