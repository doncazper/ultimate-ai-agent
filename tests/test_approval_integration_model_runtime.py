import pytest

from tests.m7_helpers import cloud_profile, classification, policy, route_request
from tests.m8_helpers import simulated_manifest
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue
from ultimate_ai_agent.core.model_router import ModelRouteStatus, ModelRouter
from ultimate_ai_agent.core.model_runtime import ModelRuntimeRequestFactory


def test_runtime_factory_accepts_selected_route_with_valid_approval_decision() -> None:
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(LocalApprovalAuthority.request_for_model_route(route, resource_refs=["cloud_reasoner"]))
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
    route = route.model_copy(update={"approval_ref": grant.approval_ref})
    decision = ModelRouter(approval_authority=authority).route(route)
    validation = authority.validate_for_request(approval_request, grant.approval_ref)

    runtime_request = ModelRuntimeRequestFactory.from_route_decision(
        decision,
        route,
        simulated_manifest(),
        approval_decision=validation,
    )

    assert decision.status == ModelRouteStatus.selected
    assert runtime_request.approval_ref == grant.approval_ref
    assert runtime_request.safety_mode == "simulated"


def test_runtime_factory_rejects_arbitrary_approval_ref() -> None:
    route = route_request(profiles=[cloud_profile()], approval_ref="human_approved_ref_123")
    decision = ModelRouter().route(route.model_copy(update={"approval_ref": None}))

    with pytest.raises(ValueError, match="validated approval"):
        ModelRuntimeRequestFactory.from_route_decision(decision, route, simulated_manifest())
