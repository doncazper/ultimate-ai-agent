from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
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
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .adapter import MatrixSyncAuthorityDispatchAdapter, MatrixSyncOperationResult
from .authority_surfaces import (
    build_matrix_sync_approval_request,
    build_matrix_sync_authority_action,
)
from .constants import matrix_sync_lane
from .contracts import (
    MatrixSyncCommand,
    MatrixSyncDispatchMetadata,
    MatrixSyncReadinessObservation,
    matrix_sync_start_deadline_ref,
    stable_matrix_sync_ref,
)


def build_matrix_sync_dispatch_request(
    command: MatrixSyncCommand,
    *,
    adapter: MatrixSyncAuthorityDispatchAdapter,
) -> AuthorityDispatchRequest:
    lane = matrix_sync_lane(command.operation)
    action = build_matrix_sync_authority_action(command)
    metadata = MatrixSyncDispatchMetadata(
        command=command,
        start_deadline_ref=matrix_sync_start_deadline_ref(command.start_deadline),
    )
    tool_request = ToolInvocationRequest(
        invocation_id=command.dispatch_ref,
        tool_ref=lane.tool_ref,
        tool_name=lane.tool_name,
        invocation_kind=ToolInvocationKind.matrix_sync,
        replay_key=command.idempotency_ref,
        safe_summary=f"Execute one exact Matrix {command.operation.value} lane.",
        input_refs=[command.request_ref],
        metadata_refs=[
            command.homeserver_ref,
            command.account_ref,
            command.cache_ref,
            command.cache_generation_ref,
            command.readiness_ref,
        ],
        metadata=metadata.model_dump(mode="json"),
    )
    estimate = CostEstimate(
        estimate_id=stable_matrix_sync_ref(
            "cost-estimate-ref:matrix-sync",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
        estimated_runtime_seconds=max(1, command.max_duration_ms // 1000),
        estimated_memory_gb=0.25,
        created_at=command.request_created_at,
    )
    budgets = [
        CostBudget(
            budget_id=stable_matrix_sync_ref(
                "cost-budget-ref:matrix-sync", {"run_ref": command.run_ref}
            ),
            scope=BudgetScope.run,
            scope_id=command.run_ref,
            max_cost_usd=0,
            max_runtime_seconds=max(1, command.max_duration_ms // 1000),
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
        safe_summary="Run one exact governed Matrix read or protected-cache operation.",
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


def attach_exact_matrix_sync_approval(
    request: AuthorityDispatchRequest,
    command: MatrixSyncCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str,
) -> AuthorityDispatchRequest:
    approval_request = approval_authority.create_request(
        build_matrix_sync_approval_request(command)
    )
    return request.model_copy(
        update={
            "approval_validation_request": approval_request.to_validation_request(
                approval_ref
            )
        }
    )


def execute_matrix_sync_command(
    command: MatrixSyncCommand,
    *,
    authority_state_dir: Path,
    executor: Callable[[MatrixSyncCommand], MatrixSyncOperationResult],
    approval_ref: str | None = None,
    lease_store: AuthorityLeaseStore | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    readiness_provider: (
        Callable[[MatrixSyncCommand], MatrixSyncReadinessObservation] | None
    ) = None,
) -> AuthorityDispatchResult:
    store = lease_store or AuthorityLeaseStore(authority_state_dir)
    approvals = approval_authority or LocalApprovalAuthority()
    adapter = MatrixSyncAuthorityDispatchAdapter(
        operation=command.operation,
        executor=executor,
        authority_leases_provider=lambda: store.list_leases(active_only=False),
        readiness_provider=readiness_provider,
    )
    request = build_matrix_sync_dispatch_request(command, adapter=adapter)
    if adapter.descriptor.approval_required and approval_ref is not None:
        request = attach_exact_matrix_sync_approval(
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
    return dispatcher.dispatch(request)


def blocked_matrix_sync_executor(command: MatrixSyncCommand) -> MatrixSyncOperationResult:
    return MatrixSyncOperationResult(
        succeeded=False,
        safe_output={
            "runtime_status": "configuration_required",
            "operation": command.operation.value,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "external_write_performed": False,
            "raw_content_included": False,
        },
        evidence_refs=(
            "evidence-ref:matrix-sync:credential-broker-not-enrolled",
        ),
        safe_summary="Matrix sync remains configuration-required until credential enrollment is proven.",
    )


def operation_result_from_transport(
    *,
    batch_ref: str,
    batch_fingerprint_ref: str,
    next_batch_ref: str,
    event_count: int,
    byte_count: int,
) -> MatrixSyncOperationResult:
    return MatrixSyncOperationResult(
        succeeded=True,
        safe_output={
            "batch_ref": batch_ref,
            "batch_fingerprint_ref": batch_fingerprint_ref,
            "next_batch_ref": next_batch_ref,
            "event_count": event_count,
            "byte_count": byte_count,
            "content_untrusted": True,
            "not_instruction_authority": True,
            "external_write_performed": False,
            "raw_content_included": False,
        },
        evidence_refs=(batch_fingerprint_ref, next_batch_ref),
        safe_summary="Matrix read completed with a one-use private batch and content-free evidence.",
    )
