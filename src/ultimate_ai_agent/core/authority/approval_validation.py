from __future__ import annotations

from datetime import timedelta
from typing import Any

from ultimate_ai_agent.core.approvals import (
    ApprovalGrant,
    ApprovalRequest,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityLeaseApprovalRequirement,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    build_authority_lease_approval_requirement_for_request,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now


def build_authority_lease_approval_request(
    requirement: AuthorityLeaseApprovalRequirement,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=requirement.approval_request_ref,
        run_id=requirement.run_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=requirement.subject_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id=requirement.operator_ref,
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=requirement.requested_action,
        purpose=requirement.purpose,
        risk_level=ApprovalRiskLevel(requirement.risk_level),
        data_classification=DataClassification(
            classification=ClassificationValue.system_internal,
            source="authority_lease_approval",
            requires_redaction=True,
        ),
        resource_refs=list(requirement.resource_refs),
        event_ref=requirement.approval_scope_ref,
        trace_id=requirement.approval_scope_ref,
        expires_at=utc_now() + timedelta(hours=1),
        metadata={
            "approval_scope_ref": requirement.approval_scope_ref,
            "authority_lease_approval_required": requirement.approval_required,
        },
    )


def validate_authority_lease_approval(
    request: AuthorityLeaseIssueRequest,
    requirement: AuthorityLeaseApprovalRequirement,
) -> Any | None:
    if not requirement.approval_required or not request.approval_ref:
        return None
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        build_authority_lease_approval_request(requirement)
    )
    for grant_payload in request.approval_grants:
        authority.load_grant_for_validation(ApprovalGrant(**grant_payload))
    return authority.validate_for_request(approval_request, request.approval_ref)


def build_authority_lease_test_grant(
    requirement: AuthorityLeaseApprovalRequirement,
    *,
    approval_ref: str,
    approved_by_actor_id: str = "operator-ref:test-approver",
) -> ApprovalGrant:
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        build_authority_lease_approval_request(requirement)
    )
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id=approved_by_actor_id,
        approval_ref=approval_ref,
    )


def issue_authority_lease_with_test_approval(
    store: AuthorityLeaseStore,
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
    approval_ref: str | None = None,
) -> tuple[Any, Any]:
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if requirement.approval_required:
        grant = build_authority_lease_test_grant(
            requirement,
            approval_ref=(
                approval_ref
                or f"approval-ref:test-authority-lease:{idempotency_ref.rsplit(':', 1)[-1]}"
            ),
        )
        request = request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "approval_grants": [grant.model_dump(mode="json")],
            }
        )
    return store.issue_lease(
        request,
        idempotency_ref=idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
