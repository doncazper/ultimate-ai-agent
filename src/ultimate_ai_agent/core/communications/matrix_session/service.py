from __future__ import annotations

from datetime import datetime
from pathlib import Path

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
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.enums import BudgetScope
from ultimate_ai_agent.core.costs.estimates import CostEstimate
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
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .constants import matrix_session_lane
from .contracts import (
    MatrixSessionCommand,
    MatrixSessionDispatchMetadata,
    matrix_session_exact_resource_refs,
    matrix_session_rollback_ref,
    matrix_session_start_deadline_ref,
    stable_matrix_session_ref,
)
from .adapter import MatrixSessionAuthorityDispatchAdapter
from .backend import (
    MatrixSessionBackend,
    MatrixSessionTransientInput,
    default_matrix_session_backend_config,
)
from .constants import MatrixSessionOperation
from .observations import MatrixDiscoveryObservationStore
from .target_policy import matrix_discovery_freshness_ref


def _record_discovery_receipt_observation(
    *,
    result: AuthorityDispatchResult,
    command: MatrixSessionCommand,
    observations: MatrixDiscoveryObservationStore,
) -> None:
    observation_refs = tuple(
        ref
        for ref in result.receipt.evidence_refs
        if ref.startswith("observation-ref:matrix-homeserver:")
    )
    freshness_refs = tuple(
        ref
        for ref in result.receipt.evidence_refs
        if ref.startswith("freshness-ref:matrix-discovery:")
    )
    if len(observation_refs) != 1 or len(freshness_refs) != 1:
        raise RuntimeError("MATRIX_DISCOVERY_EVIDENCE_INCOMPLETE")
    observation_ref = observation_refs[0]
    freshness_ref = freshness_refs[0]
    if freshness_ref != matrix_discovery_freshness_ref(observation_ref):
        raise RuntimeError("MATRIX_DISCOVERY_EVIDENCE_BINDING_INVALID")
    observations.record_success(
        observation_ref=observation_ref,
        freshness_ref=freshness_ref,
        source_discovery_origin_ref=command.homeserver_ref,
        dispatch_receipt_ref=result.receipt.receipt_ref,
        checked_at=result.receipt.created_at,
    )


def build_matrix_session_lease_issue_request(
    command: MatrixSessionCommand,
) -> AuthorityLeaseIssueRequest:
    lane = matrix_session_lane(command.operation)
    resources = list(matrix_session_exact_resource_refs(command))
    return AuthorityLeaseIssueRequest(
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        requested_lease_ref=command.lease_ref,
        requested_domains={lane.authority_domain: [lane.authority_capability]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_session_ref(
                    "authority-constraint-ref:matrix-session:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=resources,
                safe_summary="Restrict the Matrix session lease to one exact request resource set.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_session_ref(
                    "authority-constraint-ref:matrix-session:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact Matrix discovery or session operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_session_ref(
                    "authority-constraint-ref:matrix-session:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the zero-cost Matrix operation to an explicit budget.",
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
            "exact_start_deadline_ref": matrix_session_start_deadline_ref(
                command.start_deadline
            ),
            "exact_readiness_ref": command.readiness_ref,
            "exact_budget_ref": command.budget_ref,
            "exact_safe_disable_ref": command.safe_disable_ref,
            "exact_rollback_ref": matrix_session_rollback_ref(command.operation),
        },
        decision_reason_ref=stable_matrix_session_ref(
            "decision-reason-ref:matrix-session-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        duration_minutes=5,
        safe_summary="Issue one exact session-scoped Matrix discovery or account-session lease.",
    )


def issue_exact_matrix_session_lease(
    command: MatrixSessionCommand,
    *,
    store: AuthorityLeaseStore,
    confirmed: bool,
) -> tuple[AuthorityLease, object]:
    request = build_matrix_session_lease_issue_request(command)
    issue_idempotency_ref = stable_matrix_session_ref(
        "idempotency-ref:matrix-session-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement, grant = build_authority_lease_operator_approval_grant(
        request,
        idempotency_ref=issue_idempotency_ref,
        approved_by_actor_id="operator-ref:local-user",
    )
    if requirement.approval_required:
        if not confirmed or grant is None:
            raise ValueError("MATRIX_SESSION_LEASE_CONFIRMATION_REQUIRED")
        request = request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "approval_grants": [grant.model_dump(mode="json")],
            }
        )
    lease, receipt = store.issue_lease(
        request,
        idempotency_ref=issue_idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
    if lease is None or receipt.status not in {"issued", "replayed"}:
        raise ValueError("MATRIX_SESSION_EXACT_LEASE_ISSUANCE_DENIED")
    return lease, receipt


def build_exact_matrix_session_lease(
    command: MatrixSessionCommand,
    *,
    issued_at: datetime,
    expires_at: datetime,
) -> AuthorityLease:
    lane = matrix_session_lane(command.operation)
    request = build_matrix_session_lease_issue_request(command)
    return AuthorityLease(
        lease_ref=command.lease_ref,
        mode=lane.required_mode,
        scope=AuthorityLeaseScope.session,
        status=AuthorityLeaseStatus.active,
        domains={lane.authority_domain: [lane.authority_capability]},
        authority_constraints=request.authority_constraints,
        constraints=request.constraints,
        issued_at=issued_at,
        expires_at=expires_at,
        safe_disable_ref=command.safe_disable_ref,
        rollback_ref=matrix_session_rollback_ref(command.operation),
        safe_summary="Exact session-scoped lease for one Matrix discovery or account-session operation.",
    )


def build_matrix_session_authority_action(
    command: MatrixSessionCommand,
) -> AuthorityActionRequest:
    lane = matrix_session_lane(command.operation)
    return AuthorityActionRequest(
        action_ref=stable_matrix_session_ref(
            "authority-action-ref:matrix-session",
            {
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        ),
        domain=lane.authority_domain,
        capability=lane.authority_capability,
        safe_summary=f"Evaluate one exact Matrix {command.operation.value} operation.",
        resource_refs=list(matrix_session_exact_resource_refs(command)),
        route_ref=f"POST /control-center/communications/matrix/{command.operation.value.replace('_', '-')}",
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
            "policy_decision_ref": "policy-decision-ref:matrix-session:pending",
            "start_deadline_ref": matrix_session_start_deadline_ref(
                command.start_deadline
            ),
            "readiness_ref": command.readiness_ref,
            "budget_ref": command.budget_ref,
            "safe_disable_ref": command.safe_disable_ref,
        },
        rollback_ref=matrix_session_rollback_ref(command.operation),
        safe_disable_ref=command.safe_disable_ref,
    )


def build_matrix_session_approval_request(
    command: MatrixSessionCommand,
) -> ApprovalRequest:
    lane = matrix_session_lane(command.operation)
    action = build_matrix_session_authority_action(command)
    return ApprovalRequest(
        approval_request_id=stable_matrix_session_ref(
            "approval-request-ref:matrix-session",
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
            source="matrix_session_exact_operation",
            requires_redaction=True,
            requires_consent=True,
        ),
        resource_refs=[command.lease_ref, lane.adapter_ref, *action.resource_refs],
        expires_at=command.start_deadline,
    )


def capture_exact_matrix_session_approval(
    command: MatrixSessionCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    lane = matrix_session_lane(command.operation)
    if not lane.approval_required:
        raise ValueError("MATRIX_SESSION_READ_APPROVAL_FORBIDDEN")
    if not confirmed:
        raise ValueError("MATRIX_SESSION_EXACT_CONFIRMATION_REQUIRED")
    approval_request = approval_authority.create_request(
        build_matrix_session_approval_request(command)
    )
    grant = approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        expires_at=command.start_deadline,
        approval_ref=stable_matrix_session_ref(
            "approval-ref:matrix-session",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
    )
    return grant.approval_ref


def build_matrix_session_dispatch_request(
    command: MatrixSessionCommand,
    *,
    adapter: MatrixSessionAuthorityDispatchAdapter,
) -> AuthorityDispatchRequest:
    lane = matrix_session_lane(command.operation)
    action = build_matrix_session_authority_action(command)
    metadata = MatrixSessionDispatchMetadata(
        command=command,
        start_deadline_ref=matrix_session_start_deadline_ref(command.start_deadline),
    )
    tool_request = ToolInvocationRequest(
        invocation_id=command.dispatch_ref,
        tool_ref=lane.tool_ref,
        tool_name=lane.tool_name,
        invocation_kind=ToolInvocationKind.matrix_session,
        replay_key=command.idempotency_ref,
        safe_summary=f"Execute one exact Matrix session {command.operation.value} lane.",
        input_refs=[command.request_ref],
        metadata_refs=[
            command.homeserver_ref,
            command.discovery_observation_ref,
            command.discovery_freshness_ref,
            command.readiness_ref,
        ],
        metadata=metadata.model_dump(mode="json"),
    )
    estimate = CostEstimate(
        estimate_id=stable_matrix_session_ref(
            "cost-estimate-ref:matrix-session",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
        estimated_runtime_seconds=30,
        estimated_memory_gb=0.25,
        created_at=command.request_created_at,
    )
    budgets = [
        CostBudget(
            budget_id=stable_matrix_session_ref(
                "cost-budget-ref:matrix-session",
                {"run_ref": command.run_ref},
            ),
            scope=BudgetScope.run,
            scope_id=command.run_ref,
            max_cost_usd=0,
            max_runtime_seconds=30,
            max_local_memory_gb=0.25,
            created_at=command.request_created_at,
        )
    ]
    pending = AuthorityDispatchRequest(
        dispatch_ref=command.dispatch_ref,
        run_ref=command.run_ref,
        idempotency_ref=command.idempotency_ref,
        lease_ref=command.lease_ref,
        adapter_ref=lane.adapter_ref,
        action_request=action,
        tool_invocation_request=tool_request.model_dump(mode="json"),
        operation_count=1,
        estimated_cost_microusd=0,
        cost_estimate=estimate,
        cost_budgets=budgets,
        cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(estimate),
        cost_governor_decision_ref=build_authority_dispatch_cost_governor_decision_ref(
            estimate, budgets
        ),
        cost_governor_allowed=True,
        start_deadline=command.start_deadline,
        safe_summary="Run one exact governed Matrix discovery or session operation.",
    )
    policy_ref = adapter.policy_decision_ref(pending)
    action = action.model_copy(
        update={
            "constraints": {
                **action.constraints,
                "policy_decision_ref": policy_ref,
            }
        }
    )
    return pending.model_copy(update={"action_request": action})


def attach_exact_matrix_session_approval(
    request: AuthorityDispatchRequest,
    command: MatrixSessionCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str,
) -> AuthorityDispatchRequest:
    approval_request = approval_authority.create_request(
        build_matrix_session_approval_request(command)
    )
    return request.model_copy(
        update={
            "approval_validation_request": approval_request.to_validation_request(
                approval_ref
            )
        }
    )


def execute_matrix_session_command(
    command: MatrixSessionCommand,
    *,
    repo_root: Path,
    authority_state_dir: Path,
    transient_input: MatrixSessionTransientInput,
    approval_ref: str | None = None,
    backend: MatrixSessionBackend | None = None,
    lease_store: AuthorityLeaseStore | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
) -> AuthorityDispatchResult:
    store = lease_store or AuthorityLeaseStore(authority_state_dir)
    approvals = approval_authority or LocalApprovalAuthority()
    selected_backend = backend or MatrixSessionBackend(
        default_matrix_session_backend_config(repo_root),
        kill_switch_engaged=authority_lease_kill_switch_engaged,
        lifecycle_lock_dir=authority_state_dir / "matrix_session_locks",
    )
    selected_backend.bind_transient(command.dispatch_ref, transient_input)
    selected_backend.validate_transient_target(command)
    observations = MatrixDiscoveryObservationStore(
        authority_state_dir / "matrix_session_observations"
    )

    def observation_readiness(candidate: MatrixSessionCommand) -> list[str]:
        if candidate.operation == MatrixSessionOperation.discovery_read:
            try:
                return observations.prepare_for_discovery()
            except ValueError:
                return ["reason-ref:matrix-session:discovery-evidence-invalid"]
        if candidate.operation != MatrixSessionOperation.auth_methods_read:
            return []
        if transient_input.endpoint_url is None:
            return ["reason-ref:matrix-session:discovery-evidence-missing"]
        try:
            return observations.validate_current(
                observation_ref=candidate.discovery_observation_ref,
                freshness_ref=candidate.discovery_freshness_ref,
                endpoint_url=transient_input.endpoint_url,
                dispatch_receipts=dispatch_receipts,
            )
        except ValueError:
            return ["reason-ref:matrix-session:discovery-evidence-invalid"]

    adapter = MatrixSessionAuthorityDispatchAdapter(
        operation=command.operation,
        backend=selected_backend,
        authority_leases_provider=lambda: store.list_leases(active_only=False),
        readiness_provider=observation_readiness,
    )
    request = build_matrix_session_dispatch_request(command, adapter=adapter)
    if adapter.descriptor.approval_required and approval_ref is not None:
        request = attach_exact_matrix_session_approval(
            request,
            command,
            approval_authority=approvals,
            approval_ref=approval_ref,
        )
    dispatcher = AuthorityDispatcher(
        authority_state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approvals,
    )
    dispatch_receipts = dispatcher.list_receipts()
    result = dispatcher.dispatch(request)
    if (
        command.operation == MatrixSessionOperation.discovery_read
        and result.receipt.status == "succeeded"
    ):
        _record_discovery_receipt_observation(
            result=result,
            command=command,
            observations=observations,
        )
    return result
