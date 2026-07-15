from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.communications.matrix_sync import (
    MATRIX_SYNC_LANES,
    MatrixSyncCommand,
    MatrixSyncFreshness,
    MatrixSyncOperation,
    MatrixSyncPosture,
    MatrixSyncReceipt,
    MatrixSyncRuntimeStatus,
    build_default_matrix_sync_posture,
    build_matrix_sync_capability_manifest,
    build_matrix_sync_approval_request,
    build_matrix_sync_authority_action,
    build_matrix_sync_lease_issue_request,
    capture_exact_matrix_sync_approval,
    issue_exact_matrix_sync_lease,
    matrix_sync_request_fingerprint_ref,
)
from ultimate_ai_agent.core.time import utc_now


def _command(
    operation: MatrixSyncOperation = MatrixSyncOperation.sync_read,
    **overrides: object,
) -> MatrixSyncCommand:
    now = utc_now()
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": "request-ref:msg-mx-006:test",
        "task_ref": "task-ref:msg-mx-006:test",
        "mission_ref": "mission-ref:msg-mx-006:test",
        "run_ref": "run-ref:msg-mx-006:test",
        "dispatch_ref": f"dispatch-ref:msg-mx-006:{operation.value}",
        "idempotency_ref": f"idempotency-ref:msg-mx-006:{operation.value}",
        "lease_ref": f"authority-lease-ref:msg-mx-006:{operation.value}",
        "homeserver_ref": "homeserver-ref:matrix:loopback-test",
        "endpoint_class_ref": "endpoint-class-ref:matrix:local-harness",
        "account_ref": "account-ref:matrix:test",
        "device_ref": "device-ref:matrix:test",
        "session_ref": "session-ref:matrix:test",
        "session_generation_ref": "session-generation-ref:matrix:test:1",
        "credential_item_ref": "credential-item-ref:matrix:test",
        "credential_version_ref": "credential-version-ref:matrix:test:1",
        "room_refs": ("room-ref:matrix:test:one",),
        "event_class_refs": (
            "event-class-ref:matrix:message",
            "event-class-ref:matrix:encrypted-placeholder",
        ),
        "sync_cursor_ref": "sync-cursor-ref:matrix:test:initial",
        "cache_ref": "cache-ref:matrix:test",
        "cache_generation_ref": "cache-generation-ref:matrix:test:1",
        "cache_key_item_ref": "cache-key-item-ref:matrix:test",
        "cache_key_version_ref": "cache-key-version-ref:matrix:test:1",
        "readiness_ref": "readiness-ref:matrix-sync:test",
        "rollback_ref": f"rollback-ref:matrix-sync:{operation.value}",
        "request_created_at": now,
        "start_deadline": now + timedelta(minutes=2),
    }
    if operation == MatrixSyncOperation.timeline_paginate_read:
        values["pagination_cursor_ref"] = "pagination-cursor-ref:matrix:test:1"
    if operation == MatrixSyncOperation.cache_key_rotate:
        values["next_cache_key_version_ref"] = "cache-key-version-ref:matrix:test:2"
    values.update(overrides)
    values["request_fingerprint_ref"] = matrix_sync_request_fingerprint_ref(**values)
    return MatrixSyncCommand(**values)


def test_all_exact_lanes_are_declared_without_connector_write_scope() -> None:
    assert set(MATRIX_SYNC_LANES) == set(MatrixSyncOperation)
    network_lanes = {
        operation for operation, lane in MATRIX_SYNC_LANES.items() if lane.network_read
    }
    assert network_lanes == {
        MatrixSyncOperation.sync_read,
        MatrixSyncOperation.timeline_paginate_read,
        MatrixSyncOperation.room_state_read,
    }
    assert all(
        lane.authority_capability.value not in {"execute", "commit"}
        for lane in MATRIX_SYNC_LANES.values()
    )
    assert all(
        "connector" not in lane.side_effect_class for lane in MATRIX_SYNC_LANES.values()
    )


def test_cache_mutations_do_not_claim_rollback_support() -> None:
    for operation in MatrixSyncOperation:
        manifest = build_matrix_sync_capability_manifest(operation)
        assert manifest.rollback_supported is (
            operation
            in {
                MatrixSyncOperation.sync_read,
                MatrixSyncOperation.timeline_paginate_read,
            }
        )


@pytest.mark.parametrize("operation", list(MatrixSyncOperation))
def test_each_lane_issues_only_an_exact_session_lease(
    tmp_path: Path,
    operation: MatrixSyncOperation,
) -> None:
    command = _command(operation)
    request = build_matrix_sync_lease_issue_request(command)
    lane = MATRIX_SYNC_LANES[operation]
    assert request.scope == "session"
    assert request.requested_domains == {
        lane.authority_domain: [lane.authority_capability]
    }
    assert (
        request.constraints["exact_request_fingerprint_ref"]
        == command.request_fingerprint_ref
    )
    lease, receipt = issue_exact_matrix_sync_lease(
        command,
        store=AuthorityLeaseStore(tmp_path),
        confirmed=lane.approval_required,
    )
    assert receipt.status == "issued"
    assert lease.lease_ref == command.lease_ref
    assert lease.constraints["exact_lane_ref"] == lane.lane_ref


def test_cross_account_or_room_substitution_changes_the_fingerprint() -> None:
    command = _command()
    for update in (
        {"account_ref": "account-ref:matrix:other"},
        {"room_refs": ("room-ref:matrix:other",)},
        {"session_generation_ref": "session-generation-ref:matrix:test:2"},
        {"cache_generation_ref": "cache-generation-ref:matrix:test:2"},
    ):
        payload = command.model_dump(mode="python")
        payload.update(update)
        payload["request_fingerprint_ref"] = command.request_fingerprint_ref
        with pytest.raises(
            ValidationError, match="MATRIX_SYNC_REQUEST_FINGERPRINT_MISMATCH"
        ):
            MatrixSyncCommand(**payload)


def test_pagination_is_bound_to_one_room_and_one_cursor() -> None:
    with pytest.raises(
        ValidationError, match="MATRIX_SYNC_EXACT_PAGINATION_SCOPE_REQUIRED"
    ):
        _command(
            MatrixSyncOperation.timeline_paginate_read,
            room_refs=("room-ref:matrix:test:one", "room-ref:matrix:test:two"),
        )
    with pytest.raises(ValidationError, match="MATRIX_SYNC_PAGINATION_SCOPE_FORBIDDEN"):
        _command(
            MatrixSyncOperation.sync_read,
            pagination_cursor_ref="pagination-cursor-ref:matrix:test:unexpected",
        )


def test_key_rotation_requires_a_distinct_next_key_version() -> None:
    with pytest.raises(ValidationError, match="MATRIX_SYNC_NEXT_KEY_VERSION_REQUIRED"):
        _command(MatrixSyncOperation.cache_key_rotate, next_cache_key_version_ref=None)
    with pytest.raises(ValidationError, match="MATRIX_SYNC_KEY_VERSION_REUSE_DENIED"):
        _command(
            MatrixSyncOperation.cache_key_rotate,
            next_cache_key_version_ref="cache-key-version-ref:matrix:test:1",
        )


def test_read_lanes_cannot_capture_approval_identifiers() -> None:
    command = _command(MatrixSyncOperation.sync_read)
    authority = LocalApprovalAuthority()
    with pytest.raises(ValueError, match="MATRIX_SYNC_READ_APPROVAL_FORBIDDEN"):
        capture_exact_matrix_sync_approval(
            command,
            approval_authority=authority,
            confirmed=True,
        )


def test_cache_mutation_approval_binds_exact_action_and_resources() -> None:
    command = _command(MatrixSyncOperation.cache_write)
    action = build_matrix_sync_authority_action(command)
    request = build_matrix_sync_approval_request(command)
    assert action.resource_refs == list(
        build_matrix_sync_lease_issue_request(command)
        .authority_constraints[0]
        .allowed_refs
    )
    assert request.subject_id == action.action_ref
    assert request.resource_refs[0] == command.lease_ref
    assert command.account_ref in request.resource_refs
    assert command.cache_generation_ref in request.resource_refs


def test_unknown_readiness_and_stale_deadline_remain_exactly_bound() -> None:
    command = _command(readiness_ref="readiness-ref:matrix-sync:unknown")
    issue = build_matrix_sync_lease_issue_request(command)
    assert (
        issue.constraints["exact_readiness_ref"] == "readiness-ref:matrix-sync:unknown"
    )
    payload = command.model_dump(mode="python")
    payload["start_deadline"] = payload["request_created_at"] - timedelta(seconds=1)
    payload["request_fingerprint_ref"] = matrix_sync_request_fingerprint_ref(
        **{
            key: value
            for key, value in payload.items()
            if key != "request_fingerprint_ref"
        }
    )
    with pytest.raises(ValidationError, match="MATRIX_SYNC_DEADLINE_ORDER_INVALID"):
        MatrixSyncCommand(**payload)


def test_posture_cannot_claim_ready_with_stale_evidence_or_blockers() -> None:
    default = build_default_matrix_sync_posture()
    assert default.runtime_status == MatrixSyncRuntimeStatus.configuration_required
    assert default.sync_enabled is False
    assert len(default.authority_lane_refs) == 12
    assert len(default.concrete_transport_operation_refs) == 2
    assert len(default.uncomposed_executor_operation_refs) == 10
    payload = default.model_dump(mode="python")
    payload.update(
        {
            "runtime_status": MatrixSyncRuntimeStatus.ready,
            "sync_enabled": True,
            "freshness": MatrixSyncFreshness.stale,
        }
    )
    with pytest.raises(ValidationError, match="MATRIX_SYNC_READY_TRUTH_INVALID"):
        MatrixSyncPosture(**payload)


def test_success_receipt_cache_mutation_posture_is_exact() -> None:
    now = utc_now()
    common = {
        "receipt_ref": "receipt-ref:matrix-sync:test",
        "request_fingerprint_ref": "request-fingerprint-ref:matrix-sync:test",
        "account_ref": "account-ref:matrix:test",
        "cache_ref": "cache-ref:matrix:test",
        "status": "succeeded",
        "freshness": MatrixSyncFreshness.current,
        "created_at": now,
    }
    MatrixSyncReceipt(
        **common,
        operation=MatrixSyncOperation.sync_read,
        network_read_performed=True,
        local_cache_mutated=False,
    )
    MatrixSyncReceipt(
        **common,
        operation=MatrixSyncOperation.cache_write,
        network_read_performed=False,
        local_cache_mutated=True,
    )
    with pytest.raises(ValidationError, match="MATRIX_SYNC_CACHE_RECEIPT_MISMATCH"):
        MatrixSyncReceipt(
            **common,
            operation=MatrixSyncOperation.sync_read,
            network_read_performed=True,
            local_cache_mutated=True,
        )
    with pytest.raises(ValidationError, match="MATRIX_SYNC_CACHE_RECEIPT_MISMATCH"):
        MatrixSyncReceipt(
            **common,
            operation=MatrixSyncOperation.cache_write,
            network_read_performed=False,
            local_cache_mutated=False,
        )
