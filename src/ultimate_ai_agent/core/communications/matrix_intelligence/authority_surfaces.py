from __future__ import annotations

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

from .constants import matrix_intelligence_lane
from .contracts import (
    MatrixIntelligenceCommand,
    matrix_intelligence_exact_resource_refs,
    stable_matrix_intelligence_ref,
)


def build_matrix_intelligence_lease_issue_request(
    command: MatrixIntelligenceCommand,
) -> AuthorityLeaseIssueRequest:
    lane = matrix_intelligence_lane(command.operation)
    resources = list(matrix_intelligence_exact_resource_refs(command))
    return AuthorityLeaseIssueRequest(
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=command.lease_ref,
        requested_domains={
            lane.authority_domain: [lane.authority_capability],
        },
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_intelligence_ref(
                    "authority-constraint-ref:matrix-intelligence:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=resources,
                safe_summary="Restrict one Matrix intelligence operation to an exact account, room, event range, policy, grant, proposal, budget, and local-only disclosure scope.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_intelligence_ref(
                    "authority-constraint-ref:matrix-intelligence:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact human-confirmed Matrix intelligence operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_intelligence_ref(
                    "authority-constraint-ref:matrix-intelligence:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the zero-cost local operation to an explicit ceiling.",
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
            "exact_start_deadline_ref": stable_matrix_intelligence_ref(
                "deadline-ref:matrix-intelligence",
                {"start_deadline": command.start_deadline.isoformat()},
            ),
            "exact_readiness_ref": command.readiness_ref,
            "exact_budget_ref": command.budget_ref,
            "exact_safe_disable_ref": command.safe_disable_ref,
            "exact_rollback_ref": command.rollback_ref,
            "exact_provider_ref": command.provider_ref,
            "exact_runtime_ref": command.runtime_ref,
            "exact_model_destination_ref": command.model_destination_ref,
            "exact_disclosure_ref": command.disclosure_ref,
            "exact_retention_ref": command.retention_ref,
            "exact_redaction_ref": command.redaction_ref,
            "exact_kill_switch_ref": command.kill_switch_ref,
        },
        decision_reason_ref=stable_matrix_intelligence_ref(
            "decision-reason-ref:matrix-intelligence-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        duration_minutes=5,
        safe_summary="Issue one exact session-scoped Matrix intelligence lease.",
    )


def issue_exact_matrix_intelligence_lease(
    command: MatrixIntelligenceCommand,
    *,
    store: AuthorityLeaseStore,
    confirmed: bool,
) -> tuple[AuthorityLease, object]:
    request = build_matrix_intelligence_lease_issue_request(command)
    idempotency_ref = stable_matrix_intelligence_ref(
        "idempotency-ref:matrix-intelligence-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if requirement.approval_required and not confirmed:
        raise ValueError("MATRIX_INTELLIGENCE_LEASE_CONFIRMATION_REQUIRED")
    _requirement, _grant, lease, receipt = (
        issue_authority_lease_with_backend_approval(
            store,
            request,
            idempotency_ref=idempotency_ref,
            approved_by_actor_id="operator-ref:local-user",
        )
    )
    if lease is None or receipt.status not in {"issued", "replayed"}:
        raise ValueError("MATRIX_INTELLIGENCE_EXACT_LEASE_ISSUANCE_DENIED")
    return lease, receipt


def build_matrix_intelligence_authority_action(
    command: MatrixIntelligenceCommand,
) -> AuthorityActionRequest:
    lane = matrix_intelligence_lane(command.operation)
    return AuthorityActionRequest(
        action_ref=stable_matrix_intelligence_ref(
            "authority-action-ref:matrix-intelligence",
            {
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        ),
        domain=lane.authority_domain,
        capability=lane.authority_capability,
        safe_summary=f"Evaluate one exact room-scoped Matrix intelligence {command.operation.value} operation.",
        resource_refs=list(matrix_intelligence_exact_resource_refs(command)),
        route_ref=f"/control-center/communications/matrix-intelligence/{command.operation.value.replace('_', '-')}",
        capability_ref=lane.capability_ref,
        lane_ref=lane.lane_ref,
        adapter_ref=lane.adapter_ref,
        requested_mode=lane.required_mode,
        constraint_claims=[
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.operation_budget, value=1
            ),
            AuthorityConstraintClaim(
                kind=AuthorityConstraintKind.cost_budget_microusd, value=0
            ),
        ],
        constraints={
            "tool_ref": lane.tool_ref,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "mission_ref": command.mission_ref,
            "policy_decision_ref": "policy-decision-ref:matrix-intelligence:pending",
            "start_deadline_ref": stable_matrix_intelligence_ref(
                "deadline-ref:matrix-intelligence",
                {"start_deadline": command.start_deadline.isoformat()},
            ),
            "readiness_ref": command.readiness_ref,
            "budget_ref": command.budget_ref,
            "safe_disable_ref": command.safe_disable_ref,
            "kill_switch_ref": command.kill_switch_ref,
            "disclosure_ref": command.disclosure_ref,
            "retention_ref": command.retention_ref,
            "redaction_ref": command.redaction_ref,
            "max_events": command.max_events,
            "content_unit_budget": command.max_tokens,
            "max_bytes": command.max_bytes,
            "human_confirmed": True,
            "autonomous_action": False,
        },
        rollback_ref=command.rollback_ref,
        safe_disable_ref=command.safe_disable_ref,
    )


def build_matrix_intelligence_approval_request(
    command: MatrixIntelligenceCommand,
) -> ApprovalRequest:
    action = build_matrix_intelligence_authority_action(command)
    lane = matrix_intelligence_lane(command.operation)
    return ApprovalRequest(
        approval_request_id=stable_matrix_intelligence_ref(
            "approval-request-ref:matrix-intelligence",
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
        purpose=f"Approve one exact Matrix intelligence {command.operation.value} operation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="matrix_intelligence_exact_operation",
            requires_redaction=True,
            requires_consent=True,
        ),
        resource_refs=[command.lease_ref, lane.adapter_ref, *action.resource_refs],
        expires_at=command.start_deadline,
    )


def capture_exact_matrix_intelligence_approval(
    command: MatrixIntelligenceCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    if not confirmed:
        raise ValueError("MATRIX_INTELLIGENCE_EXACT_CONFIRMATION_REQUIRED")
    request = approval_authority.create_request(
        build_matrix_intelligence_approval_request(command)
    )
    grant = approval_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        expires_at=command.start_deadline,
        approval_ref=stable_matrix_intelligence_ref(
            "approval-ref:matrix-intelligence",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
    )
    return grant.approval_ref


__all__ = [
    "build_matrix_intelligence_approval_request",
    "build_matrix_intelligence_authority_action",
    "build_matrix_intelligence_lease_issue_request",
    "capture_exact_matrix_intelligence_approval",
    "issue_exact_matrix_intelligence_lease",
]
