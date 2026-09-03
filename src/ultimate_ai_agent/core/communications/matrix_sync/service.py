from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from weakref import WeakSet

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
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .adapter import (
    MatrixSyncAuthorityDispatchAdapter,
    MatrixSyncOperationResult,
)
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
from .normalization import matrix_sync_private_ref
from .implementation import matrix_sync_implementation_ref
from .transport import (
    MatrixSyncTransientTarget,
    MatrixSyncTransport,
    MatrixSyncTransportResult,
)


class _WeakrefableSlots:
    """Supply a Python 3.10-compatible weak-reference slot."""

    __slots__ = ("__weakref__",)


def _transport_result_mapper(result: object) -> MatrixSyncOperationResult:
    if not isinstance(result, MatrixSyncTransportResult):
        raise TypeError("MATRIX_SYNC_TRANSPORT_RESULT_REQUIRED")
    return operation_result_from_transport(result=result)


@dataclass(
    frozen=True,
    repr=False,
    slots=True,
    init=False,
    eq=False,
)
class MatrixSyncTransportBoundExecutor(_WeakrefableSlots):
    _transport: MatrixSyncTransport = field(repr=False, compare=False)
    _target: MatrixSyncTransientTarget = field(repr=False, compare=False)
    _pseudonymization_salt: bytes = field(repr=False, compare=False)
    _transport_binding_ref: str = field(init=False, repr=False)
    _binding_ref: str = field(init=False, repr=False)
    _result_mapper_ref: str = field(init=False, repr=False)
    target_scope_ref: str = field(init=False)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("MATRIX_SYNC_EXECUTOR_FACTORY_REQUIRED")

    @property
    def binding_ref(self) -> str:
        return self._binding_ref

    def __call__(self, command: MatrixSyncCommand) -> MatrixSyncOperationResult:
        live_target_scope_ref = _matrix_sync_transient_target_scope_ref(
            self._target,
            pseudonymization_salt=self._pseudonymization_salt,
        )
        if (
            self._transport.binding_ref != self._transport_binding_ref
            or matrix_sync_implementation_ref(_transport_result_mapper)
            != self._result_mapper_ref
            or live_target_scope_ref != self.target_scope_ref
            or self._binding_ref
            != _matrix_sync_executor_binding_ref(
                transport_binding_ref=self._transport_binding_ref,
                result_mapper_ref=self._result_mapper_ref,
                target_scope_ref=live_target_scope_ref,
            )
        ):
            raise RuntimeError("MATRIX_SYNC_TRANSPORT_BINDING_CHANGED")
        return _transport_result_mapper(
            MatrixSyncTransport.execute(
                self._transport,
                command,
                target=self._target,
                pseudonymization_salt=self._pseudonymization_salt,
            )
        )


def _matrix_sync_transient_target_scope_ref(
    target: MatrixSyncTransientTarget,
    *,
    pseudonymization_salt: bytes,
) -> str:
    return stable_matrix_sync_ref(
        "transient-target-scope-ref:matrix-sync",
        {
            "homeserver_ref": matrix_homeserver_ref(target.base_url),
            "pseudonymization_salt_ref": stable_matrix_sync_ref(
                "pseudonymization-salt-ref:matrix-sync",
                {"sha256": hashlib.sha256(pseudonymization_salt).hexdigest()},
            ),
            "pagination_cursor_ref": (
                None
                if target.pagination_token is None
                else matrix_sync_private_ref(
                    "pagination-cursor-ref:matrix",
                    pseudonymization_salt,
                    target.pagination_token,
                )
            ),
            "room_ref": (
                None
                if target.room_id is None
                else matrix_sync_private_ref(
                    "room-ref:matrix",
                    pseudonymization_salt,
                    target.room_id,
                )
            ),
            "room_refs": sorted(
                matrix_sync_private_ref(
                    "room-ref:matrix",
                    pseudonymization_salt,
                    room_id,
                )
                for room_id in target.room_ids
            ),
            "sync_cursor_ref": (
                "sync-cursor-ref:matrix:initial"
                if target.since_token is None
                else matrix_sync_private_ref(
                    "sync-cursor-ref:matrix",
                    pseudonymization_salt,
                    target.since_token,
                )
            ),
        },
    )


def _matrix_sync_executor_binding_ref(
    *,
    transport_binding_ref: str,
    result_mapper_ref: str,
    target_scope_ref: str,
) -> str:
    return stable_matrix_sync_ref(
        "executor-binding-ref:matrix-sync",
        {
            "implementation_ref": (
                matrix_sync_implementation_ref(
                    MatrixSyncTransportBoundExecutor.__call__
                )
            ),
            "result_mapper_ref": result_mapper_ref,
            "target_scope_ref": target_scope_ref,
            "transport_binding_ref": transport_binding_ref,
        },
    )


def _build_matrix_sync_executor_factory():  # type: ignore[no-untyped-def]
    registered: WeakSet[MatrixSyncTransportBoundExecutor] = WeakSet()

    def create(
        transport: MatrixSyncTransport,
        *,
        target: MatrixSyncTransientTarget,
        pseudonymization_salt: bytes,
    ) -> MatrixSyncTransportBoundExecutor:
        if type(transport) is not MatrixSyncTransport:
            raise TypeError("MATRIX_SYNC_TRANSPORT_OWNER_REQUIRED")
        if len(pseudonymization_salt) != 32:
            raise ValueError("MATRIX_SYNC_PSEUDONYMIZATION_SALT_INVALID")
        executor = object.__new__(MatrixSyncTransportBoundExecutor)
        object.__setattr__(executor, "_transport", transport)
        object.__setattr__(executor, "_target", target)
        object.__setattr__(
            executor,
            "_pseudonymization_salt",
            bytes(pseudonymization_salt),
        )
        transport_binding_ref = transport.binding_ref
        validate_execution_ref(
            transport_binding_ref,
            "matrix_sync_transport_binding_ref",
        )
        target_scope_ref = _matrix_sync_transient_target_scope_ref(
            target,
            pseudonymization_salt=pseudonymization_salt,
        )
        result_mapper_ref = matrix_sync_implementation_ref(_transport_result_mapper)
        object.__setattr__(
            executor,
            "_transport_binding_ref",
            transport_binding_ref,
        )
        object.__setattr__(
            executor,
            "_result_mapper_ref",
            result_mapper_ref,
        )
        object.__setattr__(
            executor,
            "target_scope_ref",
            target_scope_ref,
        )
        object.__setattr__(
            executor,
            "_binding_ref",
            _matrix_sync_executor_binding_ref(
                transport_binding_ref=transport_binding_ref,
                result_mapper_ref=result_mapper_ref,
                target_scope_ref=target_scope_ref,
            ),
        )
        registered.add(executor)
        return executor

    def contains(executor: object) -> bool:
        return (
            type(executor) is MatrixSyncTransportBoundExecutor
            and executor in registered
        )

    return create, contains


(
    _create_matrix_sync_transport_executor,
    _contains_matrix_sync_transport_executor,
) = _build_matrix_sync_executor_factory()
del _build_matrix_sync_executor_factory


def is_sealed_matrix_sync_transport_executor(
    executor: object,
) -> bool:
    return bool(_contains_matrix_sync_transport_executor(executor))


def bind_matrix_sync_transport_executor(
    transport: MatrixSyncTransport,
    *,
    target: MatrixSyncTransientTarget,
    pseudonymization_salt: bytes,
) -> MatrixSyncTransportBoundExecutor:
    if type(transport) is not MatrixSyncTransport:
        raise TypeError("MATRIX_SYNC_TRANSPORT_OWNER_REQUIRED")
    return _create_matrix_sync_transport_executor(
        transport=transport,
        target=target,
        pseudonymization_salt=pseudonymization_salt,
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
    executor: MatrixSyncTransportBoundExecutor,
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


def blocked_matrix_sync_executor(
    command: MatrixSyncCommand,
) -> MatrixSyncOperationResult:
    return MatrixSyncOperationResult(
        succeeded=False,
        safe_output={
            "runtime_status": "configuration_required",
            "operation": command.operation.value,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "external_write_performed": False,
            "raw_content_included": False,
        },
        evidence_refs=("evidence-ref:matrix-sync:credential-broker-not-enrolled",),
        safe_summary="Matrix sync remains configuration-required until credential enrollment is proven.",
    )


def operation_result_from_transport(
    *,
    result: MatrixSyncTransportResult,
) -> MatrixSyncOperationResult:
    return MatrixSyncOperationResult(
        succeeded=True,
        safe_output={
            "batch_ref": result.batch_ref,
            "batch_fingerprint_ref": result.batch_fingerprint_ref,
            "next_batch_ref": result.next_batch_ref,
            "event_count": result.event_count,
            "byte_count": result.byte_count,
            "content_untrusted": True,
            "not_instruction_authority": True,
            "external_write_performed": False,
            "raw_content_included": False,
        },
        evidence_refs=(result.batch_fingerprint_ref, result.next_batch_ref),
        safe_summary="Matrix read completed with a one-use private batch and content-free evidence.",
        abort_callback=result.discard,
    )
