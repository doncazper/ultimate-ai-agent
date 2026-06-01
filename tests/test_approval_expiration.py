from datetime import UTC, datetime, timedelta

from tests.m85_helpers import approval_request
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority


def test_expired_approval_grant_is_denied():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="human_reviewer",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    decision = authority.validate_for_request(request, grant.approval_ref)

    assert decision.allowed is False
    assert decision.status == ApprovalDecisionStatus.expired
    assert "APPROVAL_EXPIRED" in decision.reason_codes


def test_revoked_approval_grant_is_denied():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")
    authority.revoke(grant.approval_ref, reason="test revoke")

    decision = authority.validate_for_request(request, grant.approval_ref)

    assert decision.allowed is False
    assert decision.status == ApprovalDecisionStatus.revoked
    assert "APPROVAL_REVOKED" in decision.reason_codes
