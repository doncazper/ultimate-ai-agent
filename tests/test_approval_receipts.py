from tests.m85_helpers import approval_request
from ultimate_ai_agent.core.approvals import ApprovalReceipt, LocalApprovalAuthority


def test_approval_receipt_is_redacted_and_user_safe() -> None:
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request())
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")

    receipt = ApprovalReceipt.from_grant(grant, reason_codes=["APPROVAL_GRANTED"])
    dumped = receipt.model_dump(mode="json")

    assert dumped["approval_ref"] == grant.approval_ref
    assert dumped["reason_codes"] == ["APPROVAL_GRANTED"]
    assert "secret" not in str(dumped).lower()
