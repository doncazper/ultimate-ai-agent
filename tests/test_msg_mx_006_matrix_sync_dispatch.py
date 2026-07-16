from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchAtomicStartRecoveryRequired,
)
from ultimate_ai_agent.core.communications.matrix_sync import (
    adapter as matrix_sync_adapter,
)
from ultimate_ai_agent.core.communications.matrix_sync import (
    service as matrix_sync_service,
)
from ultimate_ai_agent.core.communications.matrix_sync import (
    MatrixSyncReadinessStatus,
    MatrixSyncOperation,
    MatrixSyncOperationResult,
    MatrixSyncTransportResult,
    MatrixSyncTransientTarget,
    MatrixSyncTransport,
    MatrixTransientBatchError,
    MatrixTransientBatchRegistry,
    build_matrix_sync_readiness_observation,
    capture_exact_matrix_sync_approval,
    execute_matrix_sync_command,
    issue_exact_matrix_sync_lease,
    operation_result_from_transport,
    bind_matrix_sync_transport_executor,
    stable_matrix_sync_ref,
)
from ultimate_ai_agent.core.time import utc_now

from tests.test_msg_mx_006_matrix_sync_authority import _command


EXECUTOR_RUNTIME_BINDING_REF = "runtime-binding-ref:matrix-sync:test"
_TEST_TRANSPORTS: dict[int, tuple[str, object]] = {}


def _test_transport_binding_ref(transport: MatrixSyncTransport) -> str:
    return _TEST_TRANSPORTS[id(transport)][0]


def _test_transport_execute(
    transport: MatrixSyncTransport,
    command,  # type: ignore[no-untyped-def]
    *,
    target,  # type: ignore[no-untyped-def]
    pseudonymization_salt,  # type: ignore[no-untyped-def]
):  # type: ignore[no-untyped-def]
    del target, pseudonymization_salt
    executor = _TEST_TRANSPORTS[id(transport)][1]
    assert callable(executor)
    return executor(command)


@pytest.fixture(scope="module", autouse=True)
def _exact_transport_executor_test_harness():  # type: ignore[no-untyped-def]
    patcher = pytest.MonkeyPatch()
    patcher.setattr(
        MatrixSyncTransport,
        "binding_ref",
        property(_test_transport_binding_ref),
    )
    patcher.setattr(
        MatrixSyncTransport,
        "execute",
        _test_transport_execute,
    )
    patcher.setattr(
        matrix_sync_service,
        "_transport_result_mapper",
        _identity_result_mapper,
    )
    try:
        yield
    finally:
        _TEST_TRANSPORTS.clear()
        patcher.undo()


def _success(_command_value):  # type: ignore[no-untyped-def]
    return MatrixSyncOperationResult(
        succeeded=True,
        safe_output={
            "batch_ref": "transient-batch-ref:matrix-sync:test",
            "event_count": 1,
            "raw_content_included": False,
            "external_write_performed": False,
        },
        evidence_refs=("evidence-ref:matrix-sync:test",),
        safe_summary="Exact Matrix operation succeeded with content-free evidence.",
        abort_callback=lambda: None,
    )


def _identity_result_mapper(result: object) -> MatrixSyncOperationResult:
    assert isinstance(result, MatrixSyncOperationResult)
    return result


def _bound(executor, *, runtime_binding_ref=EXECUTOR_RUNTIME_BINDING_REF):  # type: ignore[no-untyped-def]
    transport = object.__new__(MatrixSyncTransport)
    _TEST_TRANSPORTS[id(transport)] = (
        stable_matrix_sync_ref(
            "transport-binding-ref:matrix-sync:test",
            {
                "runtime_binding_ref": runtime_binding_ref,
                "test_implementation_ref": (
                    f"test-implementation-ref:matrix-sync:{executor.__name__}"
                ),
            },
        ),
        executor,
    )
    return bind_matrix_sync_transport_executor(
        transport,
        target=MatrixSyncTransientTarget(base_url="http://127.0.0.1:18008"),
        pseudonymization_salt=b"t" * 32,
    )


def _ready(command):  # type: ignore[no-untyped-def]
    now = utc_now()
    return build_matrix_sync_readiness_observation(
        command,
        observed_at=now,
        expires_at=now + timedelta(minutes=1),
    )


def _owned_transient_result(
    command,  # type: ignore[no-untyped-def]
    registry: MatrixTransientBatchRegistry,
):  # type: ignore[no-untyped-def]
    batch = SimpleNamespace(
        next_batch_ref="next-batch-ref:matrix-sync:test",
        events=(SimpleNamespace(event_ref="event-ref:matrix-sync:test"),),
    )
    batch_ref = registry.register(  # type: ignore[arg-type]
        batch,
        request_fingerprint_ref=command.request_fingerprint_ref,
    )
    transport_result = MatrixSyncTransportResult(
        batch_ref=batch_ref,
        event_count=1,
        byte_count=1,
        batch_fingerprint_ref="batch-fingerprint-ref:matrix-sync:test",
        next_batch_ref=batch.next_batch_ref,
        _discard_callback=lambda: registry.discard(
            batch_ref,
            request_fingerprint_ref=command.request_fingerprint_ref,
        ),
    )
    return operation_result_from_transport(result=transport_result), batch_ref, batch


def test_adapter_binding_changes_with_exact_executor_runtime() -> None:
    first = matrix_sync_adapter.MatrixSyncAuthorityDispatchAdapter(
        operation=MatrixSyncOperation.sync_read,
        executor=_bound(
            _success,
            runtime_binding_ref="runtime-binding-ref:matrix-sync:first",
        ),
        authority_leases_provider=tuple,
    )
    second = matrix_sync_adapter.MatrixSyncAuthorityDispatchAdapter(
        operation=MatrixSyncOperation.sync_read,
        executor=_bound(
            _success,
            runtime_binding_ref="runtime-binding-ref:matrix-sync:second",
        ),
        authority_leases_provider=tuple,
    )

    assert first.binding_ref != second.binding_ref


def test_adapter_rejects_unbound_callable() -> None:
    with pytest.raises(TypeError, match="MATRIX_SYNC_BOUND_EXECUTOR_REQUIRED"):
        matrix_sync_adapter.MatrixSyncAuthorityDispatchAdapter(
            operation=MatrixSyncOperation.sync_read,
            executor=_success,  # type: ignore[arg-type]
            authority_leases_provider=tuple,
        )


def test_adapter_rejects_forged_and_unregistered_executors() -> None:
    class ForgedExecutor(matrix_sync_service.MatrixSyncTransportBoundExecutor):
        pass

    for forged in (
        object.__new__(ForgedExecutor),
        object.__new__(matrix_sync_service.MatrixSyncTransportBoundExecutor),
    ):
        with pytest.raises(
            TypeError,
            match="MATRIX_SYNC_BOUND_EXECUTOR_REQUIRED",
        ):
            matrix_sync_adapter.MatrixSyncAuthorityDispatchAdapter(
                operation=MatrixSyncOperation.sync_read,
                executor=forged,
                authority_leases_provider=tuple,
            )
    assert not hasattr(matrix_sync_service, "_BOUND_MATRIX_SYNC_EXECUTORS")
    assert not hasattr(
        matrix_sync_service.MatrixSyncTransportBoundExecutor,
        "_bind",
    )


def test_executor_constructor_rejects_unsealed_owner() -> None:
    with pytest.raises(
        TypeError,
        match="MATRIX_SYNC_EXECUTOR_FACTORY_REQUIRED",
    ):
        matrix_sync_service.MatrixSyncTransportBoundExecutor(
            transport=object(),
        )


def test_executor_factory_rejects_transport_subclass() -> None:
    class ForgedTransport(MatrixSyncTransport):
        pass

    with pytest.raises(
        TypeError,
        match="MATRIX_SYNC_TRANSPORT_OWNER_REQUIRED",
    ):
        bind_matrix_sync_transport_executor(
            object.__new__(ForgedTransport),
            target=MatrixSyncTransientTarget(base_url="http://127.0.0.1:18008"),
            pseudonymization_salt=b"t" * 32,
        )


def test_transport_bound_executor_rejects_forced_target_drift() -> None:
    executor = _bound(_success)
    object.__setattr__(
        executor,
        "_target",
        MatrixSyncTransientTarget(
            base_url="http://127.0.0.1:18008",
            room_ids=("!replacement:example.test",),
        ),
    )

    with pytest.raises(RuntimeError, match="MATRIX_SYNC_TRANSPORT_BINDING_CHANGED"):
        executor(_command())


def test_transport_bound_executor_rejects_forced_salt_drift() -> None:
    executor = _bound(_success)
    object.__setattr__(executor, "_pseudonymization_salt", b"r" * 32)

    with pytest.raises(RuntimeError, match="MATRIX_SYNC_TRANSPORT_BINDING_CHANGED"):
        executor(_command())


def test_successful_batch_result_requires_owned_abort_callback() -> None:
    command = _command(MatrixSyncOperation.sync_read)
    handle = matrix_sync_adapter._ImmediateMatrixSyncHandle(
        command=command,
        execution_ref="execution-ref:matrix-sync:missing-abort-owner",
        commit_validated_at=utc_now(),
    )
    unsafe_result = MatrixSyncOperationResult(
        succeeded=True,
        safe_output={
            "batch_ref": "transient-batch-ref:matrix-sync:unowned",
            "raw_content_included": False,
            "external_write_performed": False,
        },
        evidence_refs=("evidence-ref:matrix-sync:unowned",),
        safe_summary="Unowned transient output must fail closed.",
    )

    with pytest.raises(
        AuthorityDispatchAtomicStartRecoveryRequired,
        match="MATRIX_SYNC_TRANSIENT_BATCH_ABORT_CALLBACK_REQUIRED",
    ):
        handle.bind_result(unsafe_result)

    handle.abort()
    assert handle.settled is True


def test_exact_sync_read_dispatches_once_and_terminal_replay_skips_executor(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSyncOperation.sync_read)
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=False)
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(command_value)

    first = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=store,
        readiness_provider=_ready,
    )
    replay = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=store,
        readiness_provider=_ready,
    )
    assert first.receipt.status == "succeeded"
    assert replay.receipt.status == "succeeded"
    assert replay.replayed is True
    assert calls == 1
    serialized = first.receipt.model_dump_json()
    assert "private" not in serialized
    assert "raw_content" not in serialized


def test_terminal_append_failure_discards_owned_transient_batch_and_denies_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixSyncOperation.sync_read)
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=False)
    registry = MatrixTransientBatchRegistry()
    batch_refs: list[str] = []
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        result, batch_ref, _batch = _owned_transient_result(command_value, registry)
        batch_refs.append(batch_ref)
        return result

    original_append = AuthorityDispatcher._append

    def fail_terminal_append(self, receipt):  # type: ignore[no-untyped-def]
        if receipt.status == "succeeded":
            raise RuntimeError("TEST_TERMINAL_APPEND_FAILURE")
        return original_append(self, receipt)

    monkeypatch.setattr(AuthorityDispatcher, "_append", fail_terminal_append)
    with pytest.raises(RuntimeError, match="TEST_TERMINAL_APPEND_FAILURE"):
        execute_matrix_sync_command(
            command,
            authority_state_dir=tmp_path,
            executor=_bound(executor),
            lease_store=store,
            readiness_provider=_ready,
        )
    monkeypatch.setattr(AuthorityDispatcher, "_append", original_append)

    with pytest.raises(MatrixTransientBatchError, match="EXPIRED"):
        registry.consume(
            batch_refs[0],
            request_fingerprint_ref=command.request_fingerprint_ref,
        )
    replay = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=store,
        readiness_provider=_ready,
    )
    assert replay.receipt.status == "started"
    assert replay.recovery_required is True
    assert calls == 1


def test_atomic_commit_failure_discards_owned_transient_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixSyncOperation.sync_read)
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=False)
    registry = MatrixTransientBatchRegistry()
    batch_refs: list[str] = []

    def executor(command_value):  # type: ignore[no-untyped-def]
        result, batch_ref, _batch = _owned_transient_result(command_value, registry)
        batch_refs.append(batch_ref)
        return result

    handle_type = matrix_sync_adapter._ImmediateMatrixSyncHandle
    original_commit = handle_type.commit

    def fail_commit(_self):  # type: ignore[no-untyped-def]
        raise RuntimeError("TEST_ATOMIC_COMMIT_FAILURE")

    monkeypatch.setattr(handle_type, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="TEST_ATOMIC_COMMIT_FAILURE"):
        execute_matrix_sync_command(
            command,
            authority_state_dir=tmp_path,
            executor=_bound(executor),
            lease_store=store,
            readiness_provider=_ready,
        )
    monkeypatch.setattr(handle_type, "commit", original_commit)

    with pytest.raises(MatrixTransientBatchError, match="EXPIRED"):
        registry.consume(
            batch_refs[0],
            request_fingerprint_ref=command.request_fingerprint_ref,
        )


def test_atomic_settle_failure_preserves_terminal_receipt_and_transient_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command(MatrixSyncOperation.sync_read)
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=False)
    registry = MatrixTransientBatchRegistry()
    batch_refs: list[str] = []
    batches: list[object] = []
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        result, batch_ref, batch = _owned_transient_result(command_value, registry)
        batch_refs.append(batch_ref)
        batches.append(batch)
        return result

    handle_type = matrix_sync_adapter._ImmediateMatrixSyncHandle
    original_settle = handle_type.settle

    def fail_settle(_self):  # type: ignore[no-untyped-def]
        raise RuntimeError("TEST_ATOMIC_SETTLE_FAILURE")

    monkeypatch.setattr(handle_type, "settle", fail_settle)
    with pytest.raises(RuntimeError, match="TEST_ATOMIC_SETTLE_FAILURE"):
        execute_matrix_sync_command(
            command,
            authority_state_dir=tmp_path,
            executor=_bound(executor),
            lease_store=store,
            readiness_provider=_ready,
        )
    monkeypatch.setattr(handle_type, "settle", original_settle)

    replay = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=store,
        readiness_provider=_ready,
    )
    assert replay.receipt.status == "succeeded"
    assert replay.replayed is True
    assert calls == 1
    assert (
        registry.consume(
            batch_refs[0],
            request_fingerprint_ref=command.request_fingerprint_ref,
        )
        is batches[0]
    )


def test_missing_exact_lease_denies_before_executor(tmp_path: Path) -> None:
    command = _command(MatrixSyncOperation.sync_read)
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(command_value)

    result = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=AuthorityLeaseStore(tmp_path),
        readiness_provider=_ready,
    )
    assert result.receipt.status == "denied"
    assert calls == 0


def test_unknown_readiness_denies_inside_atomic_prestart_boundary(
    tmp_path: Path,
) -> None:
    command = _command(
        MatrixSyncOperation.sync_read,
        readiness_ref="readiness-ref:matrix-sync:unknown",
    )
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=False)
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(command_value)

    def unknown_readiness(command_value):  # type: ignore[no-untyped-def]
        now = utc_now()
        return build_matrix_sync_readiness_observation(
            command_value,
            observed_at=now,
            expires_at=now + timedelta(minutes=1),
            status=MatrixSyncReadinessStatus.unknown,
            reason_refs=("reason-ref:matrix-sync:unknown",),
        )

    result = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=store,
        readiness_provider=unknown_readiness,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert calls == 0
    assert "reason-ref:matrix-sync:readiness-fail-closed" in result.receipt.reason_refs


def test_future_or_overlong_readiness_evidence_is_rejected() -> None:
    command = _command(MatrixSyncOperation.sync_read)
    now = utc_now()
    with pytest.raises(ValueError, match="MATRIX_SYNC_READINESS_OBSERVED_IN_FUTURE"):
        build_matrix_sync_readiness_observation(
            command,
            observed_at=now + timedelta(minutes=1),
            expires_at=now + timedelta(minutes=2),
        )
    with pytest.raises(ValueError, match="MATRIX_SYNC_READINESS_LIFETIME_EXCEEDED"):
        build_matrix_sync_readiness_observation(
            command,
            observed_at=now,
            expires_at=now + timedelta(minutes=3),
        )


def test_missing_or_request_mismatched_readiness_observation_fails_closed(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSyncOperation.sync_read)
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=False)
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(command_value)

    missing = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(executor),
        lease_store=store,
    )
    assert missing.receipt.status == "cancelled_before_start"
    assert "reason-ref:matrix-sync:readiness-observation-required" in (
        missing.receipt.reason_refs
    )

    other = _command(
        MatrixSyncOperation.sync_read,
        request_ref="request-ref:msg-mx-006:other",
    )
    mismatch_state = tmp_path / "mismatch"
    mismatch_store = AuthorityLeaseStore(mismatch_state)
    issue_exact_matrix_sync_lease(command, store=mismatch_store, confirmed=False)
    mismatch = execute_matrix_sync_command(
        command,
        authority_state_dir=mismatch_state,
        executor=_bound(executor),
        lease_store=mismatch_store,
        readiness_provider=lambda _command_value: _ready(other),
    )
    assert mismatch.receipt.status == "cancelled_before_start"
    assert "reason-ref:matrix-sync:readiness-request-mismatch" in (
        mismatch.receipt.reason_refs
    )
    assert calls == 0


def test_cache_write_requires_exact_approval_and_still_fails_closed_uncomposed(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSyncOperation.cache_write)
    store = AuthorityLeaseStore(tmp_path)
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_sync_lease(command, store=store, confirmed=True)
    without_approval = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(_success),
        lease_store=store,
        approval_authority=approvals,
        readiness_provider=_ready,
    )
    assert without_approval.receipt.status == "denied"

    approved_state = tmp_path / "approved"
    approved_store = AuthorityLeaseStore(approved_state)
    approved_authority = LocalApprovalAuthority()
    issue_exact_matrix_sync_lease(command, store=approved_store, confirmed=True)
    approval_ref = capture_exact_matrix_sync_approval(
        command,
        approval_authority=approved_authority,
        confirmed=True,
    )
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(command_value)

    approved = execute_matrix_sync_command(
        command,
        authority_state_dir=approved_state,
        executor=_bound(executor),
        approval_ref=approval_ref,
        lease_store=approved_store,
        approval_authority=approved_authority,
        readiness_provider=_ready,
    )
    assert approved.receipt.status == "cancelled_before_start"
    assert "reason-ref:matrix-sync:canonical-executor-uncomposed" in (
        approved.receipt.reason_refs
    )
    assert calls == 0


@pytest.mark.parametrize(
    "operation",
    sorted(
        set(MatrixSyncOperation)
        - {
            MatrixSyncOperation.sync_read,
            MatrixSyncOperation.timeline_paginate_read,
        },
        key=lambda item: item.value,
    ),
)
def test_every_uncomposed_operation_blocks_before_supplied_executor(
    tmp_path: Path,
    operation: MatrixSyncOperation,
) -> None:
    command = _command(operation)
    state = tmp_path / operation.value
    store = AuthorityLeaseStore(state)
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_sync_lease(
        command,
        store=store,
        confirmed=True,
    )
    approval_ref = None
    if operation not in {
        MatrixSyncOperation.room_state_read,
        MatrixSyncOperation.receipt_project_read,
        MatrixSyncOperation.typing_project_read,
        MatrixSyncOperation.cache_read,
    }:
        approval_ref = capture_exact_matrix_sync_approval(
            command,
            approval_authority=approvals,
            confirmed=True,
        )
    calls = 0

    def executor(command_value):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(command_value)

    result = execute_matrix_sync_command(
        command,
        authority_state_dir=state,
        executor=_bound(executor),
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=approvals,
        readiness_provider=_ready,
    )
    assert result.receipt.status == "cancelled_before_start"
    assert "reason-ref:matrix-sync:canonical-executor-uncomposed" in (
        result.receipt.reason_refs
    )
    assert calls == 0


def test_approval_identifier_from_another_authority_cannot_grant_execution(
    tmp_path: Path,
) -> None:
    command = _command(MatrixSyncOperation.cache_write)
    store = AuthorityLeaseStore(tmp_path)
    issue_exact_matrix_sync_lease(command, store=store, confirmed=True)
    foreign = LocalApprovalAuthority()
    approval_ref = capture_exact_matrix_sync_approval(
        command,
        approval_authority=foreign,
        confirmed=True,
    )
    result = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=_bound(_success),
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=LocalApprovalAuthority(),
        readiness_provider=_ready,
    )
    assert result.receipt.status == "denied"
