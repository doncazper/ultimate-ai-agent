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
    build_authority_lease_approval_requirement_for_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_backend_approval,
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

from .constants import matrix_sync_lane
from .contracts import (
    MatrixSyncCommand,
    matrix_sync_exact_resource_refs,
    matrix_sync_start_deadline_ref,
    stable_matrix_sync_ref,
)


def build_matrix_sync_lease_issue_request(
    command: MatrixSyncCommand,
) -> AuthorityLeaseIssueRequest:
    lane = matrix_sync_lane(command.operation)
    return AuthorityLeaseIssueRequest(
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=command.lease_ref,
        requested_domains={lane.authority_domain: [lane.authority_capability]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_sync_ref(
                    "authority-constraint-ref:matrix-sync:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=list(matrix_sync_exact_resource_refs(command)),
                safe_summary="Restrict this Matrix operation to one exact account and cache scope.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_sync_ref(
                    "authority-constraint-ref:matrix-sync:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact Matrix read or protected-cache operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_sync_ref(
                    "authority-constraint-ref:matrix-sync:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind this zero-cost operation to an explicit budget ceiling.",
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
            "exact_start_deadline_ref": matrix_sync_start_deadline_ref(
                command.start_deadline
            ),
            "exact_readiness_ref": command.readiness_ref,
            "exact_budget_ref": command.budget_ref,
            "exact_safe_disable_ref": command.safe_disable_ref,
            "exact_rollback_ref": command.rollback_ref,
            "exact_cache_backend_ref": command.cache_backend_ref,
            "exact_cache_schema_ref": command.cache_schema_ref,
            "exact_retention_ref": command.retention_ref,
            "exact_backup_posture_ref": command.backup_posture_ref,
        },
        decision_reason_ref=stable_matrix_sync_ref(
            "decision-reason-ref:matrix-sync-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        duration_minutes=5,
        safe_summary="Issue one exact session-scoped Matrix read or protected-cache lease.",
    )


def issue_exact_matrix_sync_lease(
    command: MatrixSyncCommand,
    *,
    store: AuthorityLeaseStore,
    confirmed: bool,
) -> tuple[AuthorityLease, object]:
    request = build_matrix_sync_lease_issue_request(command)
    issue_idempotency_ref = stable_matrix_sync_ref(
        "idempotency-ref:matrix-sync-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=issue_idempotency_ref,
    )
    if requirement.approval_required and not confirmed:
        raise ValueError("MATRIX_SYNC_LEASE_CONFIRMATION_REQUIRED")
    _requirement, _grant, lease, receipt = (
        issue_authority_lease_with_backend_approval(
            store,
            request,
            idempotency_ref=issue_idempotency_ref,
            approved_by_actor_id="operator-ref:local-user",
        )
    )
    if lease is None or receipt.status not in {"issued", "replayed"}:
        raise ValueError("MATRIX_SYNC_EXACT_LEASE_ISSUANCE_DENIED")
    return lease, receipt


def build_exact_matrix_sync_lease(
    command: MatrixSyncCommand,
    *,
    issued_at: datetime,
    expires_at: datetime,
) -> AuthorityLease:
    lane = matrix_sync_lane(command.operation)
    issue = build_matrix_sync_lease_issue_request(command)
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
        safe_summary="Exact session-scoped Matrix read or protected-cache lease.",
    )


def build_matrix_sync_authority_action(
    command: MatrixSyncCommand,
) -> AuthorityActionRequest:
    lane = matrix_sync_lane(command.operation)
    return AuthorityActionRequest(
        action_ref=stable_matrix_sync_ref(
            "authority-action-ref:matrix-sync",
            {
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        ),
        domain=lane.authority_domain,
        capability=lane.authority_capability,
        safe_summary=f"Evaluate one exact Matrix {command.operation.value} operation.",
        resource_refs=list(matrix_sync_exact_resource_refs(command)),
        route_ref=(
            "/control-center/communications/matrix-sync/"
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
            "policy_decision_ref": "policy-decision-ref:matrix-sync:pending",
            "start_deadline_ref": matrix_sync_start_deadline_ref(
                command.start_deadline
            ),
            "readiness_ref": command.readiness_ref,
            "budget_ref": command.budget_ref,
            "safe_disable_ref": command.safe_disable_ref,
        },
        rollback_ref=command.rollback_ref,
        safe_disable_ref=command.safe_disable_ref,
    )


def build_matrix_sync_approval_request(
    command: MatrixSyncCommand,
) -> ApprovalRequest:
    lane = matrix_sync_lane(command.operation)
    if not lane.approval_required:
        raise ValueError("MATRIX_SYNC_READ_APPROVAL_FORBIDDEN")
    action = build_matrix_sync_authority_action(command)
    return ApprovalRequest(
        approval_request_id=stable_matrix_sync_ref(
            "approval-request-ref:matrix-sync",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        run_id=command.run_ref,
        subject_type=ApprovalSubjectType.tool_request,
        subject_id=action.action_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=action.action_ref,
        purpose=f"Approve one exact Matrix {command.operation.value} operation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="matrix_sync_exact_operation",
            requires_redaction=True,
            requires_consent=True,
        ),
        resource_refs=[command.lease_ref, lane.adapter_ref, *action.resource_refs],
        expires_at=command.start_deadline,
    )


def capture_exact_matrix_sync_approval(
    command: MatrixSyncCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    lane = matrix_sync_lane(command.operation)
    if not lane.approval_required:
        raise ValueError("MATRIX_SYNC_READ_APPROVAL_FORBIDDEN")
    if not confirmed:
        raise ValueError("MATRIX_SYNC_EXACT_CONFIRMATION_REQUIRED")
    request = approval_authority.create_request(
        build_matrix_sync_approval_request(command)
    )
    grant = approval_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        expires_at=command.start_deadline,
        approval_ref=stable_matrix_sync_ref(
            "approval-ref:matrix-sync",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
    )
    return grant.approval_ref
