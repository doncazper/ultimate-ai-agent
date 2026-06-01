from tests.m85_helpers import approval_request
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority


def test_local_approval_authority_grant_validates():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")

    decision = authority.validate_for_request(request, grant.approval_ref)

    assert decision.allowed is True
    assert decision.status == ApprovalDecisionStatus.approved
    assert decision.matched_grant_ref == grant.approval_ref


def test_unknown_approval_ref_is_invalid():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())

    decision = authority.validate_for_request(request, "human_approved_ref_123")

    assert decision.allowed is False
    assert decision.status == ApprovalDecisionStatus.invalid
    assert "APPROVAL_REF_UNKNOWN" in decision.reason_codes


def test_test_approval_ref_requires_local_authority_fixture():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.create_test_grant(request.approval_request_id, approval_ref="approval_test_fixture")

    decision = authority.validate_for_request(request, grant.approval_ref)

    assert decision.allowed is True
    assert decision.matched_grant_ref == "approval_test_fixture"
