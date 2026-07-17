from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
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
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync import matrix_sync_private_ref
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.enums import BudgetScope
from ultimate_ai_agent.core.costs.estimates import CostEstimate
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .adapter import (
    MatrixMessagingAuthorityDispatchAdapter,
    MatrixMessagingOperationResult,
)
from .broker import (
    MatrixBrokerClient,
    MatrixBrokerError,
    MatrixBrokerInvocation,
    MatrixBrokerTransientInput,
)
from .authority_surfaces import (
    build_matrix_messaging_approval_request,
    build_matrix_messaging_authority_action,
)
from .constants import NETWORK_OPERATIONS, MatrixMessagingOperation, matrix_messaging_lane
from .contracts import (
    MatrixMessagingCommand,
    MatrixMessagingDispatchMetadata,
    MatrixMessagingReadiness,
    MatrixOutboxState,
    matrix_messaging_start_deadline_ref,
    stable_matrix_messaging_ref,
)
from .outbox import MatrixEncryptedOutbox, MatrixOutboxError, MatrixOutboxRecord
from .notifier import MatrixDesktopNotificationError, MatrixDesktopNotifier


@dataclass(frozen=True, repr=False)
class MatrixMessagingRuntimeInput:
    homeserver_url: str | None = None
    pseudonymization_salt: bytes | None = None
    direct_transient: MatrixBrokerTransientInput | None = None
    outbox_record: MatrixOutboxRecord | None = None

    def __repr__(self) -> str:
        return "MatrixMessagingRuntimeInput(<redacted>)"


class MatrixMessagingRuntime:
    """Sealed operation owner; the blocked constructor grants no execution."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("MATRIX_MESSAGING_RUNTIME_FACTORY_REQUIRED")

    @classmethod
    def blocked(cls) -> MatrixMessagingRuntime:
        runtime = object.__new__(cls)
        runtime._mode = "blocked"
        runtime.binding_ref = stable_matrix_messaging_ref(
            "runtime-binding-ref:matrix-messaging",
            {"mode": "blocked", "external_write": False},
        )
        return runtime

    @classmethod
    def live(
        cls,
        *,
        broker_client: MatrixBrokerClient,
        outbox: MatrixEncryptedOutbox,
        runtime_input: MatrixMessagingRuntimeInput,
        notifier: MatrixDesktopNotifier | None = None,
    ) -> MatrixMessagingRuntime:
        if type(broker_client) is not MatrixBrokerClient:
            raise TypeError("MATRIX_MESSAGING_BROKER_OWNER_REQUIRED")
        if type(outbox) is not MatrixEncryptedOutbox:
            raise TypeError("MATRIX_MESSAGING_OUTBOX_OWNER_REQUIRED")
        if type(runtime_input) is not MatrixMessagingRuntimeInput:
            raise TypeError("MATRIX_MESSAGING_RUNTIME_INPUT_REQUIRED")
        runtime = object.__new__(cls)
        runtime._mode = "live"
        runtime._broker_client = broker_client
        runtime._outbox = outbox
        runtime._runtime_input = runtime_input
        runtime._notifier = notifier
        runtime.binding_ref = stable_matrix_messaging_ref(
            "runtime-binding-ref:matrix-messaging",
            {
                "mode": "live",
                "broker_binding_ref": broker_client.binding_ref,
                "outbox_binding_ref": outbox.binding_ref,
                "notifier_binding_ref": (
                    notifier.binding_ref if notifier is not None else "unbound"
                ),
            },
        )
        return runtime

    def execute(
        self,
        command: MatrixMessagingCommand,
        approval_ref: str,
    ) -> MatrixMessagingOperationResult:
        if self._mode == "blocked":
            return MatrixMessagingOperationResult(
                succeeded=False,
                safe_output={
                    "runtime_status": "configuration_required",
                    "operation": command.operation.value,
                    "request_fingerprint_ref": command.request_fingerprint_ref,
                    "approval_ref": approval_ref,
                    "external_write_performed": False,
                    "raw_content_included": False,
                },
                evidence_refs=("evidence-ref:matrix-messaging:runtime-not-bound",),
                safe_summary="Matrix messaging remained blocked because no exact native runtime was bound.",
            )
        if self._mode != "live":
            raise RuntimeError("MATRIX_MESSAGING_RUNTIME_BINDING_INVALID")
        return self._execute_live(command, approval_ref)

    def _execute_live(
        self,
        command: MatrixMessagingCommand,
        approval_ref: str,
    ) -> MatrixMessagingOperationResult:
        if command.operation in {
            MatrixMessagingOperation.draft_write,
            MatrixMessagingOperation.outbox_enqueue,
        }:
            return self._write_outbox(command)
        if command.operation in {
            MatrixMessagingOperation.draft_read,
            MatrixMessagingOperation.outbox_read,
        }:
            record = self._read_exact_outbox(command)
            return _local_success(
                command,
                outcome=record.state.value,
                evidence_ref=stable_matrix_messaging_ref(
                    "evidence-ref:matrix-outbox:read",
                    {
                        "outbox_ref": record.outbox_ref,
                        "generation_ref": record.generation_ref,
                        "state": record.state.value,
                    },
                ),
            )
        if command.operation == MatrixMessagingOperation.outbox_transition:
            return self._transition_outbox(command)
        if command.operation == MatrixMessagingOperation.outbox_discard:
            self._read_exact_outbox(command)
            assert command.outbox_ref is not None
            receipt_ref = self._outbox.discard(outbox_ref=command.outbox_ref)
            return _local_success(
                command, outcome="discarded", evidence_ref=receipt_ref
            )
        if command.operation == MatrixMessagingOperation.desktop_notify:
            if self._notifier is None:
                return MatrixMessagingOperationResult(
                    succeeded=False,
                    safe_output={
                        "runtime_status": "configuration_required",
                        "operation": command.operation.value,
                        "notification_performed": False,
                        "raw_content_included": False,
                    },
                    evidence_refs=(
                        "evidence-ref:matrix-messaging:desktop-notifier-not-bound",
                    ),
                    safe_summary="Desktop notification remained blocked because no exact native notifier was bound.",
                )
            try:
                receipt = self._notifier.notify(command)
            except MatrixDesktopNotificationError:
                return MatrixMessagingOperationResult(
                    succeeded=False,
                    safe_output={
                        "runtime_status": "blocked",
                        "operation": command.operation.value,
                        "notification_performed": False,
                        "raw_content_included": False,
                    },
                    evidence_refs=(
                        "evidence-ref:matrix-messaging:desktop-notification-blocked",
                    ),
                    safe_summary="The exact content-free desktop notification did not complete.",
                )
            return MatrixMessagingOperationResult(
                succeeded=True,
                safe_output={
                    "runtime_status": "displayed",
                    "operation": command.operation.value,
                    "notification_performed": receipt.displayed,
                    "raw_content_included": receipt.content_included,
                },
                evidence_refs=(receipt.receipt_ref,),
                safe_summary="The exact generic desktop notification displayed without message content.",
            )
        if command.operation in NETWORK_OPERATIONS:
            return self._execute_network(command, approval_ref)
        raise RuntimeError("MATRIX_MESSAGING_OPERATION_UNSUPPORTED")

    def _write_outbox(
        self, command: MatrixMessagingCommand
    ) -> MatrixMessagingOperationResult:
        record = self._runtime_input.outbox_record
        if record is None:
            raise MatrixOutboxError("MATRIX_OUTBOX_RECORD_REQUIRED")
        expected_state = (
            MatrixOutboxState.draft
            if command.operation == MatrixMessagingOperation.draft_write
            else MatrixOutboxState.queued
        )
        _validate_record_binding(command, record, expected_state=expected_state)
        receipt_ref = self._outbox.write(record)
        return _local_success(
            command, outcome=record.state.value, evidence_ref=receipt_ref
        )

    def _read_exact_outbox(
        self, command: MatrixMessagingCommand
    ) -> MatrixOutboxRecord:
        if command.outbox_ref is None or command.room_ref is None:
            raise MatrixOutboxError("MATRIX_OUTBOX_COMMAND_SCOPE_REQUIRED")
        record = self._outbox.read(
            outbox_ref=command.outbox_ref,
            account_ref=command.account_ref,
            room_ref=command.room_ref,
        )
        if command.expected_outbox_state is None:
            raise MatrixOutboxError("MATRIX_OUTBOX_EXPECTED_STATE_REQUIRED")
        _validate_record_binding(
            command, record, expected_state=command.expected_outbox_state
        )
        return record

    def _transition_outbox(
        self, command: MatrixMessagingCommand
    ) -> MatrixMessagingOperationResult:
        record = self._read_exact_outbox(command)
        assert command.expected_outbox_state is not None
        assert command.next_outbox_state is not None
        assert command.next_outbox_generation_ref is not None
        updated, receipt_ref = self._outbox.transition(
            record=record,
            expected_state=command.expected_outbox_state,
            next_state=command.next_outbox_state,
            next_generation_ref=command.next_outbox_generation_ref,
        )
        return _local_success(
            command, outcome=updated.state.value, evidence_ref=receipt_ref
        )

    def _execute_network(
        self,
        command: MatrixMessagingCommand,
        approval_ref: str,
    ) -> MatrixMessagingOperationResult:
        record: MatrixOutboxRecord | None = None
        transient = self._runtime_input.direct_transient
        if command.operation in {
            MatrixMessagingOperation.send,
            MatrixMessagingOperation.reply,
            MatrixMessagingOperation.thread,
            MatrixMessagingOperation.reaction,
            MatrixMessagingOperation.edit,
            MatrixMessagingOperation.redaction,
        }:
            record = self._read_exact_outbox(command)
            relation_event_id = (
                record.event_id
                if command.operation
                in {
                    MatrixMessagingOperation.reply,
                    MatrixMessagingOperation.thread,
                    MatrixMessagingOperation.reaction,
                    MatrixMessagingOperation.edit,
                }
                else None
            )
            message_content_operation = command.operation in {
                MatrixMessagingOperation.send,
                MatrixMessagingOperation.reply,
                MatrixMessagingOperation.thread,
                MatrixMessagingOperation.edit,
            }
            transient = MatrixBrokerTransientInput(
                homeserver_url=self._runtime_input.homeserver_url,
                room_id=record.room_id,
                event_id=record.event_id,
                transaction_id=record.transaction_id,
                body=record.body if message_content_operation else None,
                formatted_body=(
                    record.formatted_body if message_content_operation else None
                ),
                mention_user_ids=(
                    record.mention_user_ids
                    if message_content_operation and record.mention_user_ids
                    else None
                ),
                relation_event_id=relation_event_id,
                reaction_key=(
                    record.reaction_key
                    if command.operation == MatrixMessagingOperation.reaction
                    else None
                ),
            )
        elif transient is None:
            raise RuntimeError("MATRIX_MESSAGING_TRANSIENT_INPUT_REQUIRED")
        if transient.homeserver_url is None:
            transient = replace(
                transient,
                homeserver_url=self._runtime_input.homeserver_url,
            )
        _validate_transient_binding(
            command,
            transient,
            pseudonymization_salt=self._runtime_input.pseudonymization_salt,
        )
        if record is not None:
            sending_generation = stable_matrix_messaging_ref(
                "outbox-generation-ref:matrix:sending",
                {
                    "request_fingerprint_ref": command.request_fingerprint_ref,
                    "attempt": record.attempt_count + 1,
                },
            )
            record, _ = self._outbox.transition(
                record=record,
                expected_state=record.state,
                next_state=MatrixOutboxState.sending,
                next_generation_ref=sending_generation,
            )
        invocation = MatrixBrokerInvocation(
            operation=command.operation.value,
            request_ref=command.request_ref,
            request_fingerprint_ref=command.request_fingerprint_ref,
            nonce=secrets.token_hex(32),
            issued_at=datetime.now(UTC),
            deadline=command.start_deadline,
            account_ref=command.account_ref,
            homeserver_ref=command.homeserver_ref,
            device_ref=command.device_ref,
            room_ref=command.room_ref,
            event_ref=command.event_ref,
            transaction_ref=command.transaction_ref,
            approval_ref=approval_ref,
            lease_ref=command.lease_ref,
            idempotency_ref=command.idempotency_ref,
            budget_ref=command.budget_ref,
            readiness_ref=command.readiness_ref,
        )
        try:
            response = self._broker_client.execute(invocation, transient=transient)
        except MatrixBrokerError:
            if record is not None:
                self._mark_network_result(
                    command,
                    record,
                    state=MatrixOutboxState.outcome_uncertain,
                    remote_event_ref=None,
                )
            return _network_failure(command, "outcome_uncertain")
        reconciliation_failure_ref: str | None = None
        if record is not None:
            state = (
                MatrixOutboxState.server_acknowledged
                if response.ok
                else MatrixOutboxState.outcome_uncertain
                if response.outcome == "outcome_uncertain"
                else MatrixOutboxState.failed
            )
            try:
                self._mark_network_result(
                    command,
                    record,
                    state=state,
                    remote_event_ref=response.event_ref,
                )
            except Exception:
                if not response.ok:
                    return _network_failure(command, response.outcome)
                reconciliation_failure_ref = stable_matrix_messaging_ref(
                    "evidence-ref:matrix-messaging:outbox-reconciliation-required",
                    {"request_fingerprint_ref": command.request_fingerprint_ref},
                )
        if not response.ok:
            return _network_failure(command, response.outcome)
        reconciliation_required = reconciliation_failure_ref is not None
        return MatrixMessagingOperationResult(
            succeeded=True,
            safe_output={
                "runtime_status": "server_acknowledged",
                "operation": command.operation.value,
                "request_fingerprint_ref": command.request_fingerprint_ref,
                "receipt_ref": response.receipt_ref,
                "event_ref": response.event_ref,
                "transaction_ref": response.transaction_ref,
                "external_write_performed": True,
                "automatic_retry_permitted": False,
                "outbox_reconciliation_required": reconciliation_required,
                "raw_content_included": False,
            },
            evidence_refs=(
                response.receipt_ref,
                *(tuple([response.event_ref]) if response.event_ref else ()),
                *(
                    tuple([reconciliation_failure_ref])
                    if reconciliation_failure_ref
                    else ()
                ),
            ),
            safe_summary=(
                "The exact human-commanded Matrix operation received bound adapter evidence; local outbox reconciliation remains required."
                if reconciliation_required
                else "The exact human-commanded Matrix operation received bound adapter evidence."
            ),
        )

    def _mark_network_result(
        self,
        command: MatrixMessagingCommand,
        record: MatrixOutboxRecord,
        *,
        state: MatrixOutboxState,
        remote_event_ref: str | None,
    ) -> None:
        generation_ref = stable_matrix_messaging_ref(
            f"outbox-generation-ref:matrix:{state.value}",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        )
        failure_ref = (
            stable_matrix_messaging_ref(
                f"reason-ref:matrix-messaging:{state.value}",
                {"request_fingerprint_ref": command.request_fingerprint_ref},
            )
            if state in {MatrixOutboxState.failed, MatrixOutboxState.outcome_uncertain}
            else None
        )
        self._outbox.transition(
            record=record,
            expected_state=MatrixOutboxState.sending,
            next_state=state,
            next_generation_ref=generation_ref,
            failure_reason_ref=failure_ref,
            remote_event_ref=remote_event_ref,
        )


def _validate_record_binding(
    command: MatrixMessagingCommand,
    record: MatrixOutboxRecord,
    *,
    expected_state: MatrixOutboxState,
) -> None:
    if (
        command.outbox_ref != record.outbox_ref
        or command.outbox_generation_ref != record.generation_ref
        or command.account_ref != record.account_ref
        or command.room_ref != record.room_ref
        or command.event_ref != record.event_ref
        or command.transaction_ref != record.transaction_ref
        or record.state != expected_state
    ):
        raise MatrixOutboxError("MATRIX_OUTBOX_COMMAND_BINDING_MISMATCH")
    if (
        command.content_fingerprint_ref is not None
        and command.content_fingerprint_ref != record.content_fingerprint_ref
    ):
        raise MatrixOutboxError("MATRIX_OUTBOX_CONTENT_BINDING_MISMATCH")
    if (
        command.operation in NETWORK_OPERATIONS
        and command.operation != record.operation
    ):
        raise MatrixOutboxError("MATRIX_OUTBOX_OPERATION_BINDING_MISMATCH")
    if (
        command.outbox_message_operation is not None
        and command.outbox_message_operation != record.operation
    ):
        raise MatrixOutboxError("MATRIX_OUTBOX_OPERATION_BINDING_MISMATCH")


def _validate_transient_binding(
    command: MatrixMessagingCommand,
    transient: MatrixBrokerTransientInput,
    *,
    pseudonymization_salt: bytes | None,
) -> None:
    if pseudonymization_salt is None:
        raise MatrixBrokerError("MATRIX_MESSAGING_PSEUDONYMIZATION_SALT_REQUIRED")
    try:
        homeserver_ref = (
            matrix_homeserver_ref(transient.homeserver_url)
            if transient.homeserver_url is not None
            else None
        )
        derived_refs = (
            (
                command.room_ref,
                matrix_sync_private_ref(
                    "room-ref:matrix", pseudonymization_salt, transient.room_id
                )
                if transient.room_id is not None
                else None,
            ),
            (
                command.event_ref,
                matrix_sync_private_ref(
                    "event-ref:matrix", pseudonymization_salt, transient.event_id
                )
                if transient.event_id is not None
                else None,
            ),
            (
                command.transaction_ref,
                matrix_sync_private_ref(
                    "transaction-ref:matrix",
                    pseudonymization_salt,
                    transient.transaction_id,
                )
                if transient.transaction_id is not None
                else None,
            ),
        )
    except ValueError as exc:
        raise MatrixBrokerError("MATRIX_MESSAGING_TRANSIENT_BINDING_INVALID") from exc
    if homeserver_ref != command.homeserver_ref or any(
        expected_ref != derived_ref for expected_ref, derived_ref in derived_refs
    ):
        raise MatrixBrokerError("MATRIX_MESSAGING_TRANSIENT_BINDING_MISMATCH")
    if (
        transient.relation_event_id is not None
        and transient.relation_event_id != transient.event_id
    ):
        raise MatrixBrokerError("MATRIX_MESSAGING_RELATION_BINDING_MISMATCH")


def _local_success(
    command: MatrixMessagingCommand,
    *,
    outcome: str,
    evidence_ref: str,
) -> MatrixMessagingOperationResult:
    return MatrixMessagingOperationResult(
        succeeded=True,
        safe_output={
            "runtime_status": outcome,
            "operation": command.operation.value,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "external_write_performed": False,
            "raw_content_included": False,
        },
        evidence_refs=(evidence_ref,),
        safe_summary="The exact encrypted Matrix outbox operation completed with content-free evidence.",
    )


def _network_failure(
    command: MatrixMessagingCommand, outcome: str
) -> MatrixMessagingOperationResult:
    evidence_ref = stable_matrix_messaging_ref(
        f"evidence-ref:matrix-messaging:{outcome}",
        {"request_fingerprint_ref": command.request_fingerprint_ref},
    )
    return MatrixMessagingOperationResult(
        succeeded=False,
        safe_output={
            "runtime_status": outcome,
            "operation": command.operation.value,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "external_write_performed": outcome == "outcome_uncertain",
            "outcome_uncertain": outcome == "outcome_uncertain",
            "automatic_retry_permitted": False,
            "raw_content_included": False,
        },
        evidence_refs=(evidence_ref,),
        safe_summary="The Matrix operation did not produce confirmed success and automatic retry remains blocked.",
    )


def build_matrix_messaging_dispatch_request(
    command: MatrixMessagingCommand,
    *,
    adapter: MatrixMessagingAuthorityDispatchAdapter,
) -> AuthorityDispatchRequest:
    lane = matrix_messaging_lane(command.operation)
    action = build_matrix_messaging_authority_action(command)
    metadata = MatrixMessagingDispatchMetadata(
        command=command,
        start_deadline_ref=matrix_messaging_start_deadline_ref(
            command.start_deadline
        ),
    )
    tool_request = ToolInvocationRequest(
        invocation_id=command.dispatch_ref,
        tool_ref=lane.tool_ref,
        tool_name=lane.tool_name,
        invocation_kind=ToolInvocationKind.matrix_messaging,
        replay_key=command.idempotency_ref,
        safe_summary=f"Execute one exact human-commanded Matrix {command.operation.value} lane.",
        input_refs=[command.request_ref],
        metadata_refs=[
            command.homeserver_ref,
            command.account_ref,
            command.device_ref,
            command.readiness_ref,
            command.request_fingerprint_ref,
        ],
        metadata=metadata.model_dump(mode="json"),
    )
    estimate = CostEstimate(
        estimate_id=stable_matrix_messaging_ref(
            "cost-estimate-ref:matrix-messaging",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
        estimated_runtime_seconds=max(1, command.max_duration_ms // 1000),
        estimated_memory_gb=0.5,
        created_at=command.request_created_at,
    )
    budgets = [
        CostBudget(
            budget_id=stable_matrix_messaging_ref(
                "cost-budget-ref:matrix-messaging", {"run_ref": command.run_ref}
            ),
            scope=BudgetScope.run,
            scope_id=command.run_ref,
            max_cost_usd=0,
            max_runtime_seconds=max(1, command.max_duration_ms // 1000),
            max_local_memory_gb=0.5,
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
        safe_summary="Run one exact approved human-commanded Matrix messaging operation.",
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


def attach_exact_matrix_messaging_approval(
    request: AuthorityDispatchRequest,
    command: MatrixMessagingCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str,
) -> AuthorityDispatchRequest:
    approval_request = approval_authority.create_request(
        build_matrix_messaging_approval_request(command)
    )
    return request.model_copy(
        update={
            "approval_validation_request": approval_request.to_validation_request(
                approval_ref
            )
        }
    )


def execute_matrix_messaging_command(
    command: MatrixMessagingCommand,
    *,
    authority_state_dir: Path,
    runtime: MatrixMessagingRuntime,
    readiness_provider: Callable[
        [MatrixMessagingCommand], MatrixMessagingReadiness
    ],
    approval_ref: str | None = None,
    lease_store: AuthorityLeaseStore | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
) -> AuthorityDispatchResult:
    if type(runtime) is not MatrixMessagingRuntime:
        raise TypeError("MATRIX_MESSAGING_RUNTIME_OWNER_REQUIRED")
    store = lease_store or AuthorityLeaseStore(authority_state_dir)
    approvals = approval_authority or LocalApprovalAuthority()
    adapter = MatrixMessagingAuthorityDispatchAdapter(
        operation=command.operation,
        executor=runtime.execute,
        executor_binding_ref=runtime.binding_ref,
        authority_leases_provider=lambda: store.list_leases(active_only=False),
        readiness_provider=readiness_provider,
    )
    request = build_matrix_messaging_dispatch_request(command, adapter=adapter)
    if approval_ref is not None:
        request = attach_exact_matrix_messaging_approval(
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


__all__ = [
    "MatrixMessagingRuntime",
    "MatrixMessagingRuntimeInput",
    "attach_exact_matrix_messaging_approval",
    "build_matrix_messaging_dispatch_request",
    "execute_matrix_messaging_command",
]
