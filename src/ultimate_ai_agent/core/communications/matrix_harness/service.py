from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ultimate_ai_agent.core.approvals import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStatus,
    AuthorityLeaseStore,
    TrustMode,
    authority_lease_kill_switch_engaged,
    build_authority_lease_approval_requirement_for_request,
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

from .adapter import MatrixHarnessAuthorityDispatchAdapter
from .backend import (
    DockerMatrixHarnessBackend,
    default_matrix_harness_backend_config,
)
from .constants import (
    MATRIX_HARNESS_CONFIG_REF,
    MATRIX_HARNESS_FIXTURE_PLAN_REF,
    MATRIX_HARNESS_IMAGE_REF,
    MATRIX_HARNESS_LIMITS_REF,
    MATRIX_HARNESS_PORT_REF,
    MATRIX_HARNESS_PROJECT_REF,
    MATRIX_HARNESS_PROVIDER_REF,
    MATRIX_HARNESS_STATE_SCOPE_REF,
    MATRIX_HARNESS_TARGET_REF,
    MatrixHarnessOperation,
    matrix_harness_lane,
)
from .contracts import (
    MatrixHarnessCommand,
    MatrixHarnessDispatchMetadata,
    matrix_harness_exact_resource_refs,
    matrix_harness_start_deadline_ref,
    stable_matrix_harness_ref,
)


def build_exact_matrix_harness_lease(
    command: MatrixHarnessCommand,
    *,
    issued_at: datetime,
    expires_at: datetime,
) -> AuthorityLease:
    lane = matrix_harness_lane(command.operation)
    resources = list(matrix_harness_exact_resource_refs(command))
    return AuthorityLease(
        lease_ref=command.lease_ref,
        mode=(
            TrustMode.read_only
            if not lane.approval_required
            else TrustMode.approved_safe_local_work_session
        ),
        scope=AuthorityLeaseScope.mission,
        status=AuthorityLeaseStatus.active,
        mission_ref=command.mission_ref,
        domains={AuthorityDomain.messages: [lane.authority_capability]},
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_harness_ref(
                    "authority-constraint-ref:matrix-harness:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=resources,
                safe_summary="Restrict the Matrix harness lease to one exact request resource set.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_harness_ref(
                    "authority-constraint-ref:matrix-harness:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact Matrix harness lifecycle operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_harness_ref(
                    "authority-constraint-ref:matrix-harness:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the zero-cost harness operation to an explicit budget.",
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
        },
        issued_at=issued_at,
        expires_at=expires_at,
        safe_disable_ref="safe-disable-ref:communications:matrix-harness-local",
        rollback_ref=f"rollback-ref:matrix-harness:{command.operation.value}",
        safe_summary="Exact mission-scoped lease for one disposable Matrix harness operation.",
    )


def build_matrix_harness_lease_issue_request(
    command: MatrixHarnessCommand,
) -> AuthorityLeaseIssueRequest:
    """Build the supported exact issue request for one harness command."""
    lane = matrix_harness_lane(command.operation)
    resources = list(matrix_harness_exact_resource_refs(command))
    return AuthorityLeaseIssueRequest(
        mode=(
            TrustMode.read_only
            if not lane.approval_required
            else TrustMode.approved_safe_local_work_session
        ),
        scope=AuthorityLeaseScope.mission,
        mission_ref=command.mission_ref,
        requested_lease_ref=command.lease_ref,
        requested_domains={
            AuthorityDomain.messages: [lane.authority_capability],
        },
        authority_constraints=[
            AuthorityConstraint(
                constraint_ref=stable_matrix_harness_ref(
                    "authority-constraint-ref:matrix-harness:resources",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.resource_refs,
                allowed_refs=resources,
                safe_summary="Restrict the Matrix harness lease to one exact request resource set.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_harness_ref(
                    "authority-constraint-ref:matrix-harness:operations",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.operation_budget,
                maximum=1,
                safe_summary="Permit one exact Matrix harness lifecycle operation.",
            ),
            AuthorityConstraint(
                constraint_ref=stable_matrix_harness_ref(
                    "authority-constraint-ref:matrix-harness:cost",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                ),
                kind=AuthorityConstraintKind.cost_budget_microusd,
                maximum=1,
                safe_summary="Bind the zero-cost harness operation to an explicit budget.",
            ),
        ],
        constraints={
            "exact_lane_ref": lane.lane_ref,
            "exact_capability_ref": lane.capability_ref,
            "exact_adapter_ref": lane.adapter_ref,
            "exact_tool_ref": lane.tool_ref,
            "exact_request_fingerprint_ref": command.request_fingerprint_ref,
        },
        decision_reason_ref=stable_matrix_harness_ref(
            "decision-reason-ref:matrix-harness-lease",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        duration_minutes=5,
        safe_summary="Issue one exact mission-scoped disposable Matrix harness lease.",
    )


def issue_exact_matrix_harness_lease(
    command: MatrixHarnessCommand,
    *,
    store: AuthorityLeaseStore,
    confirmed: bool,
) -> tuple[AuthorityLease, object]:
    """Issue one exact command-bound lease through the canonical store."""
    request = build_matrix_harness_lease_issue_request(command)
    issue_idempotency_ref = stable_matrix_harness_ref(
        "idempotency-ref:matrix-harness-lease-issue",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=issue_idempotency_ref,
    )
    if requirement.approval_required and not confirmed:
        raise ValueError("MATRIX_HARNESS_LEASE_CONFIRMATION_REQUIRED")
    _requirement, _grant, lease, receipt = (
        issue_authority_lease_with_backend_approval(
            store,
            request,
            idempotency_ref=issue_idempotency_ref,
            approved_by_actor_id="operator-ref:local-user",
        )
    )
    if lease is None or receipt.status not in {"issued", "replayed"}:
        raise ValueError("MATRIX_HARNESS_EXACT_LEASE_ISSUANCE_DENIED")
    return lease, receipt


def build_matrix_harness_dispatch_request(
    command: MatrixHarnessCommand,
    *,
    adapter: MatrixHarnessAuthorityDispatchAdapter,
) -> AuthorityDispatchRequest:
    lane = matrix_harness_lane(command.operation)
    metadata = MatrixHarnessDispatchMetadata(
        operation=command.operation,
        request_ref=command.request_ref,
        task_ref=command.task_ref,
        mission_ref=command.mission_ref,
        run_ref=command.run_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
        lifecycle_generation_ref=command.lifecycle_generation_ref,
        expected_state_ref=command.expected_state_ref,
        start_deadline_ref=matrix_harness_start_deadline_ref(command.start_deadline),
        fixture_plan_ref=(
            MATRIX_HARNESS_FIXTURE_PLAN_REF
            if command.operation == MatrixHarnessOperation.fixture_seed
            else None
        ),
        state_scope_ref=(
            MATRIX_HARNESS_STATE_SCOPE_REF
            if command.operation == MatrixHarnessOperation.reset
            else None
        ),
    )
    resource_refs = list(matrix_harness_exact_resource_refs(command))
    action = AuthorityActionRequest(
        action_ref=stable_matrix_harness_ref(
            "authority-action-ref:matrix-harness",
            {
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            },
        ),
        domain=AuthorityDomain.messages,
        capability=lane.authority_capability,
        safe_summary=f"Evaluate one exact Matrix harness {command.operation.value} operation.",
        resource_refs=resource_refs,
        route_ref=(
            f"POST /control-center/communications/harness/{command.operation.value.replace('_', '-')}"
        ),
        capability_ref=lane.capability_ref,
        lane_ref=lane.lane_ref,
        adapter_ref=lane.adapter_ref,
        requested_mode=(
            TrustMode.read_only
            if not lane.approval_required
            else TrustMode.approved_safe_local_work_session
        ),
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
            "mission_ref": command.mission_ref,
            "policy_decision_ref": "policy-decision-ref:matrix-harness:pending",
            "tool_ref": lane.tool_ref,
            "request_fingerprint_ref": command.request_fingerprint_ref,
        },
        rollback_ref=adapter.descriptor.rollback_ref,
        safe_disable_ref=adapter.descriptor.safe_disable_ref,
    )
    tool_request = ToolInvocationRequest(
        invocation_id=command.dispatch_ref,
        tool_ref=lane.tool_ref,
        tool_name=lane.tool_name,
        invocation_kind=ToolInvocationKind.matrix_harness,
        replay_key=command.idempotency_ref,
        safe_summary=f"Execute the exact Matrix harness {command.operation.value} lane.",
        input_refs=[command.request_ref],
        metadata_refs=[
            MATRIX_HARNESS_PROVIDER_REF,
            MATRIX_HARNESS_TARGET_REF,
            MATRIX_HARNESS_PROJECT_REF,
            MATRIX_HARNESS_PORT_REF,
            MATRIX_HARNESS_CONFIG_REF,
            MATRIX_HARNESS_LIMITS_REF,
            stable_matrix_harness_ref(
                "image-ref:matrix-harness", {"image": MATRIX_HARNESS_IMAGE_REF}
            ),
        ],
        metadata=metadata.model_dump(mode="json"),
    )
    estimate = CostEstimate(
        estimate_id=stable_matrix_harness_ref(
            "cost-estimate-ref:matrix-harness",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
        estimated_runtime_seconds=120,
        estimated_memory_gb=1,
    )
    budgets = [
        CostBudget(
            budget_id=stable_matrix_harness_ref(
                "cost-budget-ref:matrix-harness",
                {"run_ref": command.run_ref},
            ),
            scope=BudgetScope.run,
            scope_id=command.run_ref,
            max_cost_usd=0,
            max_runtime_seconds=120,
            max_local_memory_gb=1,
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
            estimate,
            budgets,
        ),
        cost_governor_allowed=True,
        start_deadline=command.start_deadline,
        safe_summary="Run one exact governed disposable Matrix harness operation.",
    )
    policy_ref = adapter.policy_decision_ref(pending)
    action = action.model_copy(
        update={
            "constraints": {
                "mission_ref": command.mission_ref,
                "policy_decision_ref": policy_ref,
                "tool_ref": lane.tool_ref,
                "request_fingerprint_ref": command.request_fingerprint_ref,
            }
        }
    )
    return pending.model_copy(update={"action_request": action})


def build_matrix_harness_approval_request(
    request: AuthorityDispatchRequest,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=stable_matrix_harness_ref(
            "approval-request-ref:matrix-harness",
            {"dispatch_ref": request.dispatch_ref},
        ),
        run_id=request.run_ref,
        subject_type=ApprovalSubjectType.tool_request,
        subject_id=request.action_request.action_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=request.action_request.action_ref,
        purpose="Approve one exact disposable Matrix harness lifecycle operation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.system_internal,
            source="matrix_harness_exact_operation",
            requires_redaction=True,
        ),
        resource_refs=[
            request.lease_ref,
            request.adapter_ref,
            *request.action_request.resource_refs,
        ],
        expires_at=request.start_deadline,
    )


def capture_exact_matrix_harness_approval(
    request: AuthorityDispatchRequest,
    *,
    approval_authority: LocalApprovalAuthority,
    confirmed: bool,
) -> str:
    if not confirmed:
        raise ValueError("MATRIX_HARNESS_EXACT_CONFIRMATION_REQUIRED")
    approval_request = approval_authority.create_request(
        build_matrix_harness_approval_request(request)
    )
    grant = approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="operator-ref:local-user",
        expires_at=request.start_deadline,
        approval_ref=stable_matrix_harness_ref(
            "approval-ref:matrix-harness",
            {"dispatch_ref": request.dispatch_ref},
        ),
    )
    return grant.approval_ref


def attach_exact_matrix_harness_approval(
    request: AuthorityDispatchRequest,
    *,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str,
) -> AuthorityDispatchRequest:
    approval_request = approval_authority.create_request(
        build_matrix_harness_approval_request(request)
    )
    return request.model_copy(
        update={
            "approval_validation_request": approval_request.to_validation_request(
                approval_ref
            )
        }
    )


def execute_matrix_harness_command(
    command: MatrixHarnessCommand,
    *,
    repo_root: Path,
    authority_state_dir: Path,
    approval_ref: str | None = None,
    backend: DockerMatrixHarnessBackend | None = None,
    lease_store: AuthorityLeaseStore | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
) -> AuthorityDispatchResult:
    store = lease_store or AuthorityLeaseStore(authority_state_dir)
    approvals = approval_authority or LocalApprovalAuthority()
    selected_backend = backend or DockerMatrixHarnessBackend(
        default_matrix_harness_backend_config(repo_root),
        kill_switch_engaged=authority_lease_kill_switch_engaged,
    )
    adapter = MatrixHarnessAuthorityDispatchAdapter(
        operation=command.operation,
        backend=selected_backend,
        authority_leases_provider=lambda: store.list_leases(active_only=False),
    )
    request = build_matrix_harness_dispatch_request(command, adapter=adapter)
    if adapter.descriptor.approval_required and approval_ref is not None:
        request = attach_exact_matrix_harness_approval(
            request,
            approval_authority=approvals,
            approval_ref=approval_ref,
        )
    dispatcher = AuthorityDispatcher(
        authority_state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approvals,
    )
    return dispatcher.dispatch(request)
