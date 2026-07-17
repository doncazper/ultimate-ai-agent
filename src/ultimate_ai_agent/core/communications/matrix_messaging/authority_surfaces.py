from __future__ import annotations

from datetime import datetime

from ultimate_ai_agent.core.approvals import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStatus,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    build_authority_lease_operator_approval_grant,
    validate_authority_lease_approval,
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

from .constants import matrix_messaging_lane
from .contracts import (
    MatrixMessagingCommand,
    matrix_messaging_exact_resource_refs,
    matrix_messaging_start_deadline_ref,
    stable_matrix_messaging_ref,
)


def build_matrix_messaging_lease_issue_request(
    command: MatrixMessagingCommand,
) -> AuthorityLeaseIssueRequest:
    lane = matrix_messaging_lane(command.operation)
    return AuthorityLeaseIssueRequest(
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=command.lease_ref,
        requested_domains={lane.authority_domain: [lane.authority_capability]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_messaging_ref(
                    "authority-constraint-ref:matrix-messaging:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=list(matrix_messaging_exact_resource_refs(command)),
                safe_summary="Restrict this message operation to one exact account, room, event, content, and outbox scope.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_messaging_ref(
                    "authority-constraint-ref:matrix-messaging:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact human-commanded Matrix messaging operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_messaging_ref(
                    "authority-constraint-ref:matrix-messaging:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the zero-cost operation to an explicit budget ceiling.",
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
            "exact_start_deadline_ref": matrix_messaging_start_deadline_ref(
                command.start_deadline
            ),
            "exact_readiness_ref": command.readiness_ref,
            "exact_budget_ref": command.budget_ref,
            "exact_safe_disable_ref": command.safe_disable_ref,
            "exact_rollback_ref": command.rollback_ref,
            "exact_provider_ref": command.provider_ref,
            "exact_runtime_ref": command.runtime_ref,
            "exact_outbox_schema_ref": command.outbox_schema_ref,
            "exact_outbox_key_item_ref": command.outbox_key_item_ref,
            "exact_outbox_key_version_ref": command.outbox_key_version_ref,
            "exact_kill_switch_ref": command.kill_switch_ref,
        },
        decision_reason_ref=stable_matrix_messaging_ref(
            "decision-reason-ref:matrix-messaging-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        duration_minutes=5,
        safe_summary="Issue one exact session-scoped human-commanded Matrix messaging lease.",
    )


def issue_exact_matrix_messaging_lease(
    command: MatrixMessagingCommand,
    *,
    store: AuthorityLeaseStore,
    confirmed: bool,
) -> tuple[AuthorityLease, object]:
    request = build_matrix_messaging_lease_issue_request(command)
    idempotency_ref = stable_matrix_messaging_ref(
        "idempotency-ref:matrix-messaging-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement, grant = build_authority_lease_operator_approval_grant(
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:local-user",
    )
    if requirement.approval_required:
        if not confirmed or grant is None:
            raise ValueError("MATRIX_MESSAGING_LEASE_CONFIRMATION_REQUIRED")
        request = request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "approval_grants": [grant.model_dump(mode="json")],
            }
        )
    lease, receipt = store.issue_lease(
        request,
        idempotency_ref=idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
    if lease is None or receipt.status not in {"issued", "replayed"}:
        raise ValueError("MATRIX_MESSAGING_EXACT_LEASE_ISSUANCE_DENIED")
    return lease, receipt


def build_exact_matrix_messaging_lease(
    command: MatrixMessagingCommand,
    *,
    issued_at: datetime,
    expires_at: datetime,
) -> AuthorityLease:
    lane = matrix_messaging_lane(command.operation)
    issue = build_matrix_messaging_lease_issue_request(command)
    return AuthorityLease(
        lease_ref=command.lease_ref,
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        status=AuthorityLeaseStatus.active,
        domains={lane.authority_domain: [lane.authority_capability]},
        authority_constraints=issue.authority_constraints,
        constraints=issue.constraints,
        issued_at=issued_at,
        expires_at=expires_at,
        safe_disable_ref=command.safe_disable_ref,
        rollback_ref=command.rollback_ref,
        safe_summary="Exact request-scoped Matrix messaging lease.",
    )


def build_matrix_messaging_authority_action(
    command: MatrixMessagingCommand,
) -> AuthorityActionRequest:
    lane = matrix_messaging_lane(command.operation)
    return AuthorityActionRequest(
        action_ref=stable_matrix_messaging_ref(
            "authority-action-ref:matrix-messaging",
            {
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        ),
        domain=lane.authority_domain,
        capability=lane.authority_capability,
        safe_summary=f"Evaluate one exact human-commanded Matrix {command.operation.value} operation.",
        resource_refs=list(matrix_messaging_exact_resource_refs(command)),
        route_ref=(
            "/control-center/communications/matrix-messaging/"
            f"{command.operation.value.replace('_', '-')}"
        ),
        capability_ref=lane.capability_ref,
        lane_ref=lane.lane_ref,
        adapter_ref=lane.adapter_ref,
        requested_mode=lane.required_mode,
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget,
                value=1,
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd,
                value=0,
            ),
        ],
        constraints={
            "tool_ref": lane.tool_ref,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "mission_ref": command.mission_ref,
            "policy_decision_ref": "policy-decision-ref:matrix-messaging:pending",
            "start_deadline_ref": matrix_messaging_start_deadline_ref(
                command.start_deadline
            ),
            "readiness_ref": command.readiness_ref,
            "budget_ref": command.budget_ref,
            "safe_disable_ref": command.safe_disable_ref,
            "kill_switch_ref": command.kill_switch_ref,
            "human_commanded": True,
            "autonomous_send": False,
        },
        rollback_ref=command.rollback_ref,
        safe_disable_ref=command.safe_disable_ref,
    )


def build_matrix_messaging_approval_request(
    command: MatrixMessagingCommand,
) -> ApprovalRequest:
    lane = matrix_messaging_lane(command.operation)
    action = build_matrix_messaging_authority_action(command)
    return ApprovalRequest(
        approval_request_id=stable_matrix_messaging_ref(
            "approval-request-ref:matrix-messaging",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        run_id=command.run_ref,
        subject_type=ApprovalSubjectType.tool_request,
        subject_id=action.action_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
            created_at=command.request_created_at,
        ),
        requested_action=action.action_ref,
        purpose=f"Approve one exact human-commanded Matrix {command.operation.value} operation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="matrix_messaging_exact_operation",
            requires_redaction=True,
            requires_consent=True,
        ),
        resource_refs=[command.lease_ref, lane.adapter_ref, *action.resource_refs],
        expires_at=command.start_deadline,
    )


def capture_exact_matrix_messaging_approval(
    command: MatrixMessagingCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    if not confirmed:
        raise ValueError("MATRIX_MESSAGING_EXACT_CONFIRMATION_REQUIRED")
    request = approval_authority.create_request(
        build_matrix_messaging_approval_request(command)
    )
    grant = approval_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        expires_at=command.start_deadline,
        approval_ref=stable_matrix_messaging_ref(
            "approval-ref:matrix-messaging",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
    )
    return grant.approval_ref


__all__ = [
    "build_exact_matrix_messaging_lease",
    "build_matrix_messaging_approval_request",
    "build_matrix_messaging_authority_action",
    "build_matrix_messaging_lease_issue_request",
    "capture_exact_matrix_messaging_approval",
    "issue_exact_matrix_messaging_lease",
]
