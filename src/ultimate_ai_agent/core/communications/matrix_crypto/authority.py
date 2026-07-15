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
    build_authority_lease_approval_request,
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

from .constants import matrix_crypto_lane
from .contracts import (
    MatrixCryptoCommand,
    matrix_crypto_exact_resource_refs,
    matrix_crypto_start_deadline_ref,
    stable_matrix_crypto_ref,
)


def build_matrix_crypto_lease_issue_request(
    command: MatrixCryptoCommand,
) -> AuthorityLeaseIssueRequest:
    lane = matrix_crypto_lane(command.operation)
    return AuthorityLeaseIssueRequest(
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=command.lease_ref,
        requested_domains={lane.authority_domain: [lane.authority_capability]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_crypto_ref(
                    "authority-constraint-ref:matrix-crypto:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=list(matrix_crypto_exact_resource_refs(command)),
                safe_summary=(
                    "Restrict this Matrix crypto request to exact account, device, "
                    "store, key, backup, recovery, and generation references."
                ),
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_crypto_ref(
                    "authority-constraint-ref:matrix-crypto:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit at most one exact Matrix crypto operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_crypto_ref(
                    "authority-constraint-ref:matrix-crypto:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary=(
                    "Bind this zero-cost operation to a positive fail-closed ceiling."
                ),
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
            "exact_start_deadline_ref": matrix_crypto_start_deadline_ref(
                command.start_deadline
            ),
            "exact_readiness_ref": command.readiness_ref,
            "exact_budget_ref": command.budget_ref,
            "exact_kill_switch_ref": command.kill_switch_ref,
            "exact_safe_disable_ref": command.safe_disable_ref,
            "exact_rollback_ref": command.rollback_ref,
            "exact_store_backend_ref": command.store_backend_ref,
            "exact_key_backend_ref": command.key_backend_ref,
            "exact_backup_backend_ref": command.backup_backend_ref,
        },
        decision_reason_ref=stable_matrix_crypto_ref(
            "decision-reason-ref:matrix-crypto-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        duration_minutes=5,
        safe_summary="Issue one exact session-scoped Matrix crypto lease.",
    )


def issue_exact_matrix_crypto_lease(
    command: MatrixCryptoCommand,
    *,
    store: AuthorityLeaseStore,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str | None,
) -> tuple[AuthorityLease, object]:
    """Issue a command-bound lease only from an exact stored approval grant."""

    request = build_matrix_crypto_lease_issue_request(command)
    idempotency_ref = stable_matrix_crypto_ref(
        "idempotency-ref:matrix-crypto-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if requirement.approval_required:
        if approval_ref is None:
            raise ValueError("MATRIX_CRYPTO_LEASE_APPROVAL_REQUIRED")
        approval_request = build_authority_lease_approval_request(requirement)
        decision = approval_authority.validate_for_request(
            approval_request,
            approval_ref,
        )
        grant = approval_authority.get_grant(approval_ref)
        if not decision.allowed or grant is None:
            raise ValueError("MATRIX_CRYPTO_LEASE_APPROVAL_INVALID")
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
        raise ValueError("MATRIX_CRYPTO_EXACT_LEASE_ISSUANCE_DENIED")
    return lease, receipt


def capture_exact_matrix_crypto_lease_approval(
    command: MatrixCryptoCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    """Capture the operator's exact lease approval in LocalApprovalAuthority."""

    if not confirmed:
        raise ValueError("MATRIX_CRYPTO_LEASE_CONFIRMATION_REQUIRED")
    request = build_matrix_crypto_lease_issue_request(command)
    idempotency_ref = stable_matrix_crypto_ref(
        "idempotency-ref:matrix-crypto-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if not requirement.approval_required:
        raise ValueError("MATRIX_CRYPTO_LEASE_APPROVAL_NOT_REQUIRED")
    approval_request = approval_authority.create_request(
        build_authority_lease_approval_request(requirement)
    )
    grant = approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        approval_ref=stable_matrix_crypto_ref(
            "approval-ref:matrix-crypto-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
    )
    return grant.approval_ref


def build_matrix_crypto_authority_action(
    command: MatrixCryptoCommand,
) -> AuthorityActionRequest:
    lane = matrix_crypto_lane(command.operation)
    return AuthorityActionRequest(
        action_ref=stable_matrix_crypto_ref(
            "authority-action-ref:matrix-crypto",
            {
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        ),
        domain=lane.authority_domain,
        capability=lane.authority_capability,
        safe_summary=f"Evaluate one exact Matrix {command.operation.value} request.",
        resource_refs=list(matrix_crypto_exact_resource_refs(command)),
        route_ref="/control-center/communications/matrix-crypto/proposal",
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
            "policy_decision_ref": "policy-decision-ref:matrix-crypto:pending",
            "start_deadline_ref": matrix_crypto_start_deadline_ref(
                command.start_deadline
            ),
            "readiness_ref": command.readiness_ref,
            "budget_ref": command.budget_ref,
            "kill_switch_ref": command.kill_switch_ref,
            "safe_disable_ref": command.safe_disable_ref,
        },
        unsupported_adapter=True,
        rollback_ref=command.rollback_ref,
        safe_disable_ref=command.safe_disable_ref,
    )


def build_matrix_crypto_approval_request(
    command: MatrixCryptoCommand,
) -> ApprovalRequest:
    lane = matrix_crypto_lane(command.operation)
    if not lane.approval_required:
        raise ValueError("MATRIX_CRYPTO_READ_APPROVAL_FORBIDDEN")
    action = build_matrix_crypto_authority_action(command)
    risk = ApprovalRiskLevel.critical if lane.destructive else ApprovalRiskLevel.high
    return ApprovalRequest(
        approval_request_id=stable_matrix_crypto_ref(
            "approval-request-ref:matrix-crypto",
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
        purpose=f"Approve one exact Matrix {command.operation.value} request.",
        risk_level=risk,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="matrix_crypto_exact_operation",
            requires_redaction=True,
            requires_consent=True,
        ),
        resource_refs=[command.lease_ref, lane.adapter_ref, *action.resource_refs],
        expires_at=command.start_deadline,
    )


def capture_exact_matrix_crypto_approval(
    command: MatrixCryptoCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    if not matrix_crypto_lane(command.operation).approval_required:
        raise ValueError("MATRIX_CRYPTO_READ_APPROVAL_FORBIDDEN")
    if not confirmed:
        raise ValueError("MATRIX_CRYPTO_EXACT_CONFIRMATION_REQUIRED")
    request = approval_authority.create_request(
        build_matrix_crypto_approval_request(command)
    )
    grant = approval_authority.grant(
        request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        expires_at=command.start_deadline,
        approval_ref=stable_matrix_crypto_ref(
            "approval-ref:matrix-crypto",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
    )
    return grant.approval_ref
