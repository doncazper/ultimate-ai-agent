import pytest
from pydantic import ValidationError

from tests.m7_helpers import classification, cloud_profile, policy, route_request
from ultimate_ai_agent.core.approvals import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue
from ultimate_ai_agent.core.model_router import (
    ModelRouteDecision,
    ModelRouteStatus,
    ModelRouter,
)


def test_router_uses_local_approval_authority_for_sensitive_cloud_route() -> None:
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
    grant = authority.grant(
        approval_request.approval_request_id, approved_by_actor_id="human_reviewer"
    )

    decision = ModelRouter(approval_authority=authority).route(
        route.model_copy(update={"approval_ref": grant.approval_ref})
    )

    assert decision.status == ModelRouteStatus.selected
    assert decision.selected_profile_id == "cloud_reasoner"
    assert "APPROVAL_VALIDATED" in decision.reason_codes


def test_router_rejects_expired_authority_grant() -> None:
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )
    authority = LocalApprovalAuthority()
    request = authority.create_request(
        LocalApprovalAuthority.request_for_model_route(
            route, resource_refs=["cloud_reasoner"]
        )
    )
    grant = authority.grant(
        request.approval_request_id, approved_by_actor_id="human_reviewer"
    )
    authority.revoke(grant.approval_ref, reason="test revoke")

    decision = ModelRouter(approval_authority=authority).route(
        route.model_copy(update={"approval_ref": grant.approval_ref})
    )

    assert decision.status == ModelRouteStatus.approval_required
    assert "APPROVAL_REVOKED" in decision.reason_codes


def test_router_rejects_test_shaped_approval_without_authority() -> None:
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
        approval_ref="approval_test_cloud_ok",
    )

    decision = ModelRouter().route(route)

    assert decision.status == ModelRouteStatus.approval_required
    assert decision.selected_profile_id is None
    assert "APPROVAL_TEST_REF_DENIED" in decision.reason_codes


def test_router_rejects_authority_backed_test_shaped_approval() -> None:
    route = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        LocalApprovalAuthority.request_for_model_route(
            route,
            resource_refs=["cloud_reasoner"],
        )
    )
    grant = authority.create_test_grant(
        approval_request.approval_request_id,
        approval_ref="approval_test_cloud_bound",
    )

    decision = ModelRouter(approval_authority=authority).route(
        route.model_copy(update={"approval_ref": grant.approval_ref})
    )

    assert decision.status == ModelRouteStatus.approval_required
    assert decision.approval_validation_decision_ref is None
    assert "APPROVAL_TEST_REF_DENIED" in decision.reason_codes


def test_router_does_not_claim_unused_approval_was_validated() -> None:
    route = route_request(
        profiles=[cloud_profile()],
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        LocalApprovalAuthority.request_for_model_route(
            route,
            resource_refs=["cloud_reasoner"],
        )
    )
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="human_reviewer",
    )

    decision = ModelRouter(approval_authority=authority).route(
        route.model_copy(update={"approval_ref": grant.approval_ref})
    )

    assert decision.status == ModelRouteStatus.selected
    assert "APPROVAL_VALIDATED" not in decision.reason_codes
    assert decision.approval_validation_decision_ref is None


def test_route_decision_requires_relational_approval_evidence() -> None:
    decision = ModelRouter().route(route_request(profiles=[cloud_profile()]))
    payload = decision.model_dump(mode="python")
    payload["reason_codes"] = [*payload["reason_codes"], "APPROVAL_VALIDATED"]
    with pytest.raises(ValidationError, match="APPROVAL_EVIDENCE_DRIFT"):
        ModelRouteDecision.model_validate(payload)

    payload = decision.model_dump(mode="python")
    payload["approval_validation_decision_ref"] = (
        f"approval-validation-decision-ref:sha256:{'0' * 64}"
    )
    with pytest.raises(ValidationError, match="APPROVAL_EVIDENCE_DRIFT"):
        ModelRouteDecision.model_validate(payload)


def test_approval_evidence_ref_binds_exact_selected_profile_scope() -> None:
    first_profile = cloud_profile(
        profile_id="cloud_first",
        cost_per_1k_input_tokens=0.001,
        cost_per_1k_output_tokens=0.001,
    )
    second_profile = cloud_profile(
        profile_id="cloud_second",
        cost_per_1k_input_tokens=0.02,
        cost_per_1k_output_tokens=0.02,
    )
    route = route_request(
        profiles=[first_profile, second_profile],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(
            require_human_approval_for_cloud=True,
            allow_cloud=True,
        ),
    )
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        LocalApprovalAuthority.request_for_model_route(
            route,
            resource_refs=["cloud_first", "cloud_second"],
        )
    )
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="human_reviewer",
    )
    approved_route = route.model_copy(update={"approval_ref": grant.approval_ref})
    first_decision = ModelRouter(approval_authority=authority).route(approved_route)

    second_cheaper_route = approved_route.model_copy(
        update={
            "available_profiles": [
                first_profile.model_copy(
                    update={
                        "cost_per_1k_input_tokens": 0.03,
                        "cost_per_1k_output_tokens": 0.03,
                    }
                ),
                second_profile.model_copy(
                    update={
                        "cost_per_1k_input_tokens": 0.001,
                        "cost_per_1k_output_tokens": 0.001,
                    }
                ),
            ]
        }
    )
    second_decision = ModelRouter(approval_authority=authority).route(
        second_cheaper_route
    )

    assert first_decision.selected_profile_id == "cloud_first"
    assert second_decision.selected_profile_id == "cloud_second"
    assert first_decision.approval_validation_decision_ref is not None
    assert second_decision.approval_validation_decision_ref is not None
    assert first_decision.approval_validation_decision_ref != (
        second_decision.approval_validation_decision_ref
    )
