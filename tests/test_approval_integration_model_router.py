from tests.m7_helpers import classification, cloud_profile, policy, route_request
from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter


def test_router_uses_local_approval_authority_for_sensitive_cloud_route():
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )
    approval_request = LocalApprovalAuthority.request_for_model_route(
        route,
        subject_type=ApprovalSubjectType.model_route,
        subject_id=route.request_id,
        requested_action="route_cloud_model",
        resource_refs=["cloud_reasoner"],
        risk_level=ApprovalRiskLevel.high,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")

    decision = ModelRouter(approval_authority=authority).route(route.model_copy(update={"approval_ref": grant.approval_ref}))

    assert decision.status == ModelRouteStatus.selected
    assert decision.selected_profile_id == "cloud_reasoner"
    assert "APPROVAL_VALIDATED" in decision.reason_codes


def test_router_rejects_expired_authority_grant():
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )
    authority = LocalApprovalAuthority()
    request = authority.create_request(LocalApprovalAuthority.request_for_model_route(route, resource_refs=["cloud_reasoner"]))
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")
    authority.revoke(grant.approval_ref, reason="test revoke")

    decision = ModelRouter(approval_authority=authority).route(route.model_copy(update={"approval_ref": grant.approval_ref}))

    assert decision.status == ModelRouteStatus.approval_required
    assert "APPROVAL_REVOKED" in decision.reason_codes


def test_router_keeps_test_approval_compatibility_without_authority():
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
        approval_ref="approval_test_cloud_ok",
    )

    decision = ModelRouter().route(route)

    assert decision.status == ModelRouteStatus.selected
