from tests.m85_helpers import approval_request
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, LocalApprovalAuthority


def test_grant_cannot_approve_broader_scope_than_request():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request(resource_refs=["cloud_reasoner"]))

    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="human_reviewer",
        approved_actions=["route_cloud_model", "delete"],
        approved_resource_refs=["cloud_reasoner", "other_resource"],
    )

    assert grant.approved_actions == ["route_cloud_model"]
    assert grant.approved_resource_refs == ["cloud_reasoner"]


def test_validation_rejects_ungranted_extra_resource():
    authority = LocalApprovalAuthority()
    request = authority.create_request(approval_request(resource_refs=["cloud_reasoner"]))
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")

    validation = request.to_validation_request(grant.approval_ref).model_copy(
        update={"resource_refs": ["cloud_reasoner", "other_resource"]}
    )
    decision = authority.validate(validation)

    assert decision.allowed is False
    assert decision.status == ApprovalDecisionStatus.out_of_scope
    assert "APPROVAL_RESOURCE_NOT_GRANTED" in decision.reason_codes
