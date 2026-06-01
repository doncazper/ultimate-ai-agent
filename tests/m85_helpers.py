from datetime import UTC, datetime, timedelta

from tests.m7_helpers import actor, classification
from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue


def approval_request(
    *,
    subject_type: ApprovalSubjectType = ApprovalSubjectType.model_route,
    subject_id: str = "route_req_1",
    requested_action: str = "route_cloud_model",
    resource_refs: list[str] | None = None,
    risk_level: ApprovalRiskLevel = ApprovalRiskLevel.high,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"areq_{subject_id}",
        run_id="run_m85",
        subject_type=subject_type,
        subject_id=subject_id,
        actor_context=actor(),
        requested_action=requested_action,
        purpose="M8.5 approval test.",
        risk_level=risk_level,
        data_classification=classification(ClassificationValue.sensitive_personal),
        resource_refs=resource_refs or ["cloud_reasoner"],
        consent_refs=["consent_m85"],
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )


def granted_authority(request: ApprovalRequest | None = None) -> tuple[LocalApprovalAuthority, str]:
    authority = LocalApprovalAuthority()
    approval = authority.create_request(request or approval_request())
    grant = authority.grant(approval.approval_request_id, approved_by_actor_id="human_reviewer")
    return authority, grant.approval_ref
