from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.communications.matrix_sync import (
    MatrixSyncReadinessStatus,
    MatrixSyncOperation,
    MatrixSyncOperationResult,
    build_matrix_sync_readiness_observation,
    capture_exact_matrix_sync_approval,
    execute_matrix_sync_command,
    issue_exact_matrix_sync_lease,
)
from ultimate_ai_agent.core.time import utc_now

from tests.test_msg_mx_006_matrix_sync_authority import _command


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
    )


def _ready(command):  # type: ignore[no-untyped-def]
    now = utc_now()
    return build_matrix_sync_readiness_observation(
        command,
        observed_at=now,
        expires_at=now + timedelta(minutes=1),
    )


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
        executor=executor,
        lease_store=store,
        readiness_provider=_ready,
    )
    replay = execute_matrix_sync_command(
        command,
        authority_state_dir=tmp_path,
        executor=executor,
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
        executor=executor,
        lease_store=AuthorityLeaseStore(tmp_path),
        readiness_provider=_ready,
    )
    assert result.receipt.status == "denied"
    assert calls == 0


def test_unknown_readiness_denies_inside_atomic_prestart_boundary(tmp_path: Path) -> None:
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
        executor=executor,
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
        executor=executor,
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
        executor=executor,
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
        executor=_success,
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
        executor=executor,
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
        executor=executor,
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
        executor=_success,
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=LocalApprovalAuthority(),
        readiness_provider=_ready,
    )
    assert result.receipt.status == "denied"
