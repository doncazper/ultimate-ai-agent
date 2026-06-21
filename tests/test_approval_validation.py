from tests.m85_helpers import approval_request, granted_authority
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, ApprovalRiskLevel, ApprovalValidationRequest


def test_validation_denies_wrong_actor() -> None:
    authority, approval_ref = granted_authority()
    request = approval_request()
    validation = ApprovalValidationRequest.from_approval_request(request, approval_ref).model_copy(
        update={"actor_context": request.actor_context.model_copy(update={"actor_id": "other_actor"})}
    )

    decision = authority.validate(validation)

    assert decision.allowed is False
    assert decision.status == ApprovalDecisionStatus.out_of_scope
    assert "APPROVAL_ACTOR_MISMATCH" in decision.reason_codes


def test_validation_denies_wrong_subject_action_resource_and_risk() -> None:
    authority, approval_ref = granted_authority()
    base = ApprovalValidationRequest.from_approval_request(approval_request(), approval_ref)

    for update, reason in [
        ({"subject_id": "other_subject"}, "APPROVAL_SUBJECT_MISMATCH"),
        ({"requested_action": "other_action"}, "APPROVAL_ACTION_NOT_GRANTED"),
        ({"resource_refs": ["other_resource"]}, "APPROVAL_RESOURCE_NOT_GRANTED"),
        ({"risk_level": ApprovalRiskLevel.critical}, "APPROVAL_RISK_MISMATCH"),
    ]:
        decision = authority.validate(base.model_copy(update=update))
        assert decision.allowed is False
        assert decision.status == ApprovalDecisionStatus.out_of_scope
        assert reason in decision.reason_codes
