from datetime import timedelta

from tests.m9_helpers import approval_for_runtime, local_manifest, local_runtime_request, loopback_endpoint, loopback_policy
from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, LocalApprovalAuthority
from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter
from ultimate_ai_agent.core.time import utc_now


def validate(request, approval_decision):
    return LocalLoopbackModelRuntimeAdapter().validate_execution(
        request,
        local_manifest(),
        loopback_endpoint(),
        loopback_policy(),
        approval_decision,
    )


def test_missing_arbitrary_and_expired_approval_refs_are_denied():
    request = local_runtime_request(approval_ref="human_approved_ref_123")
    missing = validate(local_runtime_request(approval_ref=None), None)
    arbitrary = validate(request, None)

    authority, approval_request, grant, _ = approval_for_runtime(local_runtime_request())
    expired = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="human_reviewer",
        expires_at=utc_now() - timedelta(seconds=1),
    )
    expired_decision = authority.validate_for_request(approval_request, expired.approval_ref)
    expired_result = validate(local_runtime_request(approval_ref=expired.approval_ref), expired_decision)

    assert "APPROVAL_REQUIRED" in missing.reason_codes
    assert "APPROVAL_DECISION_REQUIRED" in arbitrary.reason_codes
    assert "APPROVAL_EXPIRED" in expired_result.reason_codes


def test_wrong_subject_action_resource_and_risk_are_denied():
    request = local_runtime_request()
    authority, approval_request, grant, _ = approval_for_runtime(request)

    wrong_subject = approval_request.model_copy(update={"subject_id": "other_runtime_request"})
    wrong_action = approval_request.model_copy(update={"requested_action": "route_cloud_model"})
    wrong_resource = approval_request.model_copy(update={"resource_refs": ["other_adapter"]})
    wrong_risk = approval_request.model_copy(update={"risk_level": ApprovalRiskLevel.critical})

    decisions = [
        authority.validate_for_request(wrong_subject, grant.approval_ref),
        authority.validate_for_request(wrong_action, grant.approval_ref),
        authority.validate_for_request(wrong_resource, grant.approval_ref),
        authority.validate_for_request(wrong_risk, grant.approval_ref),
    ]

    assert all(validate(request.model_copy(update={"approval_ref": grant.approval_ref}), decision).allowed is False for decision in decisions)


def test_valid_local_authority_grant_allows_execution_decision():
    request = local_runtime_request()
    _, _, grant, approval_decision = approval_for_runtime(request)
    result = validate(request.model_copy(update={"approval_ref": grant.approval_ref}), approval_decision)

    assert result.allowed is True
    assert result.status == "allowed"


def test_unknown_approval_ref_does_not_authorize_authority_validation():
    request = local_runtime_request(approval_ref="human_approved_ref_123")
    approval_request = approval_for_runtime(request)[1]
    decision = LocalApprovalAuthority().validate_for_request(approval_request, request.approval_ref)

    result = validate(request, decision)

    assert result.allowed is False
    assert "APPROVAL_REF_UNKNOWN" in result.reason_codes
