from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.communications.matrix_messaging.constants import (
    MATRIX_MESSAGING_LANES,
    MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF,
    MATRIX_MESSAGING_NOTIFICATION_POLICY_REF,
    MATRIX_MESSAGING_NOTIFICATION_TARGET_REF,
    MatrixMessagingOperation,
    matrix_messaging_lane,
    matrix_messaging_rollback_ref,
)
from ultimate_ai_agent.core.communications.matrix_messaging.authority_surfaces import (
    build_matrix_messaging_approval_request,
    build_matrix_messaging_lease_issue_request,
    issue_exact_matrix_messaging_lease,
    capture_exact_matrix_messaging_approval,
)
from ultimate_ai_agent.core.communications.matrix_messaging.contracts import (
    MatrixMessagingCommand,
    MatrixMessagingReadiness,
    MatrixOutboxState,
    build_matrix_messaging_command,
    matrix_messaging_exact_resource_refs,
)
from ultimate_ai_agent.core.communications.matrix_messaging.outbox import (
    MatrixEncryptedOutbox,
    MatrixOutboxError,
    MatrixOutboxRecord,
    matrix_outbox_content_fingerprint_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync.cache import (
    InMemoryMatrixCacheCryptoBackend,
    MatrixCacheKeyUnavailable,
)
from ultimate_ai_agent.core.authority import (
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.communications.matrix_messaging.service import (
    MatrixMessagingRuntime,
    MatrixMessagingRuntimeInput,
    execute_matrix_messaging_command,
)
from ultimate_ai_agent.core.communications.matrix_messaging.broker import (
    MatrixBrokerClient,
    MatrixBrokerConfig,
    MatrixBrokerError,
    MatrixBrokerInvocation,
    MatrixBrokerResponse,
    MatrixBrokerTransientInput,
)
from ultimate_ai_agent.core.communications.matrix_messaging import broker as broker_module
from ultimate_ai_agent.core.communications.matrix_messaging.notifier import (
    MatrixDesktopNotificationError,
    MatrixDesktopNotifier,
)
from ultimate_ai_agent.core.communications.matrix_messaging.static_safety import (
    MATRIX_MESSAGING_BROKER_REL,
    MATRIX_MESSAGING_NOTIFIER_REL,
    is_exact_matrix_messaging_broker_subprocess_site,
    is_exact_matrix_messaging_notifier_subprocess_site,
)


def _command(
    operation: MatrixMessagingOperation = MatrixMessagingOperation.send,
    **updates: object,
) -> MatrixMessagingCommand:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "operation": operation,
        "request_ref": "request-ref:matrix-messaging:exact-v1",
        "task_ref": "task-ref:matrix-messaging:exact-v1",
        "mission_ref": "mission-ref:matrix-messaging:exact-v1",
        "run_ref": "run-ref:matrix-messaging:exact-v1",
        "dispatch_ref": "dispatch-ref:matrix-messaging:exact-v1",
        "idempotency_ref": "idempotency-ref:matrix-messaging:exact-v1",
        "lease_ref": "authority-lease-ref:matrix-messaging:exact-v1",
        "account_ref": "account-ref:matrix:exact-v1",
        "homeserver_ref": "homeserver-ref:matrix:exact-v1",
        "device_ref": "device-ref:matrix:exact-v1",
        "room_ref": "room-ref:matrix:exact-v1",
        "event_ref": None,
        "transaction_ref": "transaction-ref:matrix:exact-v1",
        "content_fingerprint_ref": "content-fingerprint-ref:matrix:exact-v1",
        "outbox_ref": "outbox-ref:matrix:exact-v1",
        "outbox_generation_ref": "outbox-generation-ref:matrix:exact-v1",
        "expected_outbox_state": MatrixOutboxState.queued,
        "next_outbox_state": None,
        "notification_target_ref": None,
        "readiness_ref": "readiness-ref:matrix-messaging:exact-v1",
        "rollback_ref": matrix_messaging_rollback_ref(operation),
        "request_created_at": now,
        "start_deadline": now + timedelta(seconds=30),
    }
    payload.update(updates)
    return build_matrix_messaging_command(**payload)


def _record(*, state: MatrixOutboxState = MatrixOutboxState.queued) -> MatrixOutboxRecord:
    now = datetime.now(UTC)
    operation = MatrixMessagingOperation.send
    fingerprint = matrix_outbox_content_fingerprint_ref(
        operation=operation,
        room_id="!room:localhost",
        event_id=None,
        transaction_id="transaction-exact-v1",
        body="transient-content-marker-v1",
        formatted_body=None,
        mention_user_ids=(),
        reaction_key=None,
    )
    return MatrixOutboxRecord(
        outbox_ref="outbox-ref:matrix:exact-v1",
        generation_ref="outbox-generation-ref:matrix:exact-v1",
        account_ref="account-ref:matrix:exact-v1",
        room_ref="room-ref:matrix:exact-v1",
        transaction_ref="transaction-ref:matrix:exact-v1",
        operation=operation,
        content_fingerprint_ref=fingerprint,
        state=state,
        created_at=now,
        expires_at=now + timedelta(minutes=15),
        room_id="!room:localhost",
        transaction_id="transaction-exact-v1",
        body="transient-content-marker-v1",
    )


def _outbox(tmp_path: Path) -> tuple[MatrixEncryptedOutbox, InMemoryMatrixCacheCryptoBackend]:
    backend = InMemoryMatrixCacheCryptoBackend()
    outbox = MatrixEncryptedOutbox(
        root=(tmp_path / "outbox").resolve(),
        crypto_backend=backend,
        key_item_ref="key-item-ref:matrix-outbox:dedicated-v1",
        key_version_ref="key-version-ref:matrix-outbox:v1",
    )
    outbox.create_key()
    return outbox, backend


def test_all_exact_lanes_require_fresh_approval() -> None:
    assert len(MATRIX_MESSAGING_LANES) == 15
    assert all(lane.approval_required for lane in MATRIX_MESSAGING_LANES.values())
    assert all(lane.required_mode.value != "read_only" for lane in MATRIX_MESSAGING_LANES.values())


def test_command_binds_content_room_transaction_and_outbox() -> None:
    command = _command()
    resources = set(matrix_messaging_exact_resource_refs(command))
    assert command.content_fingerprint_ref in resources
    assert command.room_ref in resources
    assert command.transaction_ref in resources
    assert command.outbox_ref in resources
    assert command.outbox_generation_ref in resources


def test_exact_lease_and_approval_bind_every_resource(tmp_path: Path) -> None:
    command = _command()
    issue = build_matrix_messaging_lease_issue_request(command)
    approval = build_matrix_messaging_approval_request(command)
    expected = set(matrix_messaging_exact_resource_refs(command))
    assert set(issue.authority_constraints[0].allowed_refs) == expected
    assert expected <= set(approval.resource_refs)
    with pytest.raises(ValueError, match="LEASE_CONFIRMATION_REQUIRED"):
        issue_exact_matrix_messaging_lease(
            command,
            store=AuthorityLeaseStore((tmp_path / "denied").resolve()),
            confirmed=False,
        )
    lease, receipt = issue_exact_matrix_messaging_lease(
        command,
        store=AuthorityLeaseStore((tmp_path / "accepted").resolve()),
        confirmed=True,
    )
    assert lease.lease_ref == command.lease_ref
    assert receipt.status == "issued"


def test_dispatcher_requires_current_exact_approval_lease_and_readiness(
    tmp_path: Path,
) -> None:
    command = _command()
    state_dir = (tmp_path / "authority").resolve()
    store = AuthorityLeaseStore(state_dir)
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_messaging_lease(command, store=store, confirmed=True)

    def readiness(_command: MatrixMessagingCommand) -> MatrixMessagingReadiness:
        observed = datetime.now(UTC)
        return MatrixMessagingReadiness(
            readiness_ref=command.readiness_ref,
            request_fingerprint_ref=command.request_fingerprint_ref,
            adapter_ref=matrix_messaging_lane(command.operation).adapter_ref,
            status="ready",
            observed_at=observed,
            expires_at=observed + timedelta(seconds=10),
            kill_switch_engaged=False,
            safe_disable_active=False,
            broker_integrity_verified=True,
            keychain_available=True,
            crypto_store_available=True,
        )

    denied = execute_matrix_messaging_command(
        command,
        authority_state_dir=state_dir,
        runtime=MatrixMessagingRuntime.blocked(),
        readiness_provider=readiness,
        lease_store=store,
        approval_authority=approvals,
    )
    assert denied.receipt.status == "denied"
    approval_ref = capture_exact_matrix_messaging_approval(
        command,
        approval_authority=approvals,
        confirmed=True,
    )
    approved_state_dir = (tmp_path / "approved-authority").resolve()
    approved_store = AuthorityLeaseStore(approved_state_dir)
    issue_exact_matrix_messaging_lease(
        command, store=approved_store, confirmed=True
    )
    attempted = execute_matrix_messaging_command(
        command,
        authority_state_dir=approved_state_dir,
        runtime=MatrixMessagingRuntime.blocked(),
        readiness_provider=readiness,
        approval_ref=approval_ref,
        lease_store=approved_store,
        approval_authority=approvals,
    )
    assert attempted.receipt.status == "failed"
    assert attempted.adapter_result is not None
    assert attempted.adapter_result.safe_output["external_write_performed"] is False


def test_terminal_replay_is_stable_and_does_not_reinvoke_runtime(tmp_path: Path) -> None:
    command = _command()
    state_dir = (tmp_path / "authority").resolve()
    store = AuthorityLeaseStore(state_dir)
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_messaging_lease(command, store=store, confirmed=True)
    approval_ref = capture_exact_matrix_messaging_approval(
        command,
        approval_authority=approvals,
        confirmed=True,
    )

    def readiness(exact: MatrixMessagingCommand) -> MatrixMessagingReadiness:
        return MatrixMessagingReadiness(
            readiness_ref=exact.readiness_ref,
            request_fingerprint_ref=exact.request_fingerprint_ref,
            adapter_ref=matrix_messaging_lane(exact.operation).adapter_ref,
            status="ready",
            observed_at=exact.request_created_at,
            expires_at=exact.start_deadline,
            kill_switch_engaged=False,
            safe_disable_active=False,
            broker_integrity_verified=True,
            keychain_available=True,
            crypto_store_available=True,
        )

    runtime = MatrixMessagingRuntime.blocked()
    first = execute_matrix_messaging_command(
        command,
        authority_state_dir=state_dir,
        runtime=runtime,
        readiness_provider=readiness,
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=approvals,
    )
    replay = execute_matrix_messaging_command(
        command,
        authority_state_dir=state_dir,
        runtime=runtime,
        readiness_provider=readiness,
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=approvals,
    )
    assert first.receipt.status == "failed"
    assert replay.replayed is True
    assert replay.receipt.receipt_ref == first.receipt.receipt_ref


def test_revoked_approval_fails_closed_before_runtime(tmp_path: Path) -> None:
    command = _command()
    state_dir = (tmp_path / "authority").resolve()
    store = AuthorityLeaseStore(state_dir)
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_messaging_lease(command, store=store, confirmed=True)
    approval_ref = capture_exact_matrix_messaging_approval(
        command,
        approval_authority=approvals,
        confirmed=True,
    )
    approvals.revoke(approval_ref, "reason-ref:matrix-messaging:test-revoked")

    def readiness(exact: MatrixMessagingCommand) -> MatrixMessagingReadiness:
        return MatrixMessagingReadiness(
            readiness_ref=exact.readiness_ref,
            request_fingerprint_ref=exact.request_fingerprint_ref,
            adapter_ref=matrix_messaging_lane(exact.operation).adapter_ref,
            status="ready",
            observed_at=exact.request_created_at,
            expires_at=exact.start_deadline,
            kill_switch_engaged=False,
            safe_disable_active=False,
            broker_integrity_verified=True,
            keychain_available=True,
            crypto_store_available=True,
        )

    result = execute_matrix_messaging_command(
        command,
        authority_state_dir=state_dir,
        runtime=MatrixMessagingRuntime.blocked(),
        readiness_provider=readiness,
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=approvals,
    )
    assert result.receipt.status == "denied"
    assert result.receipt.execution_started is False


def test_expired_approval_and_revoked_lease_fail_closed_before_runtime(
    tmp_path: Path,
) -> None:
    command = _command()

    def readiness(exact: MatrixMessagingCommand) -> MatrixMessagingReadiness:
        return MatrixMessagingReadiness(
            readiness_ref=exact.readiness_ref,
            request_fingerprint_ref=exact.request_fingerprint_ref,
            adapter_ref=matrix_messaging_lane(exact.operation).adapter_ref,
            status="ready",
            observed_at=exact.request_created_at,
            expires_at=exact.start_deadline,
            kill_switch_engaged=False,
            safe_disable_active=False,
            broker_integrity_verified=True,
            keychain_available=True,
            crypto_store_available=True,
        )

    expired_state_dir = (tmp_path / "expired-authority").resolve()
    expired_store = AuthorityLeaseStore(expired_state_dir)
    expired_approvals = LocalApprovalAuthority()
    issue_exact_matrix_messaging_lease(
        command, store=expired_store, confirmed=True
    )
    approval_request = expired_approvals.create_request(
        build_matrix_messaging_approval_request(command)
    )
    expired_grant = expired_approvals.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:matrix-messaging:test",
        expires_at=command.request_created_at - timedelta(seconds=1),
        approval_ref="approval-ref:matrix-messaging:expired-test-v1",
    )
    expired = execute_matrix_messaging_command(
        command,
        authority_state_dir=expired_state_dir,
        runtime=MatrixMessagingRuntime.blocked(),
        readiness_provider=readiness,
        approval_ref=expired_grant.approval_ref,
        lease_store=expired_store,
        approval_authority=expired_approvals,
    )
    assert expired.receipt.status == "denied"
    assert expired.receipt.execution_started is False

    revoked_state_dir = (tmp_path / "revoked-authority").resolve()
    revoked_store = AuthorityLeaseStore(revoked_state_dir)
    revoked_approvals = LocalApprovalAuthority()
    issue_exact_matrix_messaging_lease(
        command, store=revoked_store, confirmed=True
    )
    approval_ref = capture_exact_matrix_messaging_approval(
        command,
        approval_authority=revoked_approvals,
        confirmed=True,
    )
    lease_revoked = False

    def revoke_during_prestart(
        exact: MatrixMessagingCommand,
    ) -> MatrixMessagingReadiness:
        nonlocal lease_revoked
        if not lease_revoked:
            revoked_store.revoke_lease(
                AuthorityLeaseRevokeRequest(
                    lease_ref=command.lease_ref,
                    decision_reason_ref=(
                        "reason-ref:matrix-messaging:test-lease-revoked"
                    ),
                    safe_summary="Revoke the exact messaging lease before start.",
                ),
                idempotency_ref=(
                    "idempotency-ref:matrix-messaging:test-lease-revoke"
                ),
            )
            lease_revoked = True
        return readiness(exact)

    revoked = execute_matrix_messaging_command(
        command,
        authority_state_dir=revoked_state_dir,
        runtime=MatrixMessagingRuntime.blocked(),
        readiness_provider=revoke_during_prestart,
        approval_ref=approval_ref,
        lease_store=revoked_store,
        approval_authority=revoked_approvals,
    )
    assert revoked.receipt.status == "cancelled_before_start"
    assert revoked.receipt.execution_started is False


def test_changed_content_ref_invalidates_request_fingerprint() -> None:
    command = _command()
    with pytest.raises(ValidationError, match="REQUEST_FINGERPRINT_MISMATCH"):
        MatrixMessagingCommand.model_validate(
            {
                **command.model_dump(mode="python"),
                "content_fingerprint_ref": "content-fingerprint-ref:matrix:changed-v2",
            }
        )


def test_cross_room_and_missing_event_scopes_fail_closed() -> None:
    with pytest.raises(ValidationError, match="EVENT_SCOPE_INVALID"):
        _command(
            MatrixMessagingOperation.reply,
            event_ref=None,
            rollback_ref=matrix_messaging_rollback_ref(MatrixMessagingOperation.reply),
        )
    with pytest.raises(ValidationError, match="NOTIFICATION_SCOPE_INVALID"):
        _command(
            MatrixMessagingOperation.desktop_notify,
            transaction_ref=None,
            content_fingerprint_ref=None,
            outbox_ref=None,
            outbox_generation_ref=None,
            expected_outbox_state=None,
            room_ref="room-ref:matrix:substitution-v2",
            notification_target_ref="notification-target-ref:desktop:exact-v1",
            rollback_ref=matrix_messaging_rollback_ref(
                MatrixMessagingOperation.desktop_notify
            ),
        )


def test_encrypted_outbox_round_trip_and_plaintext_scan(tmp_path: Path) -> None:
    outbox, _backend = _outbox(tmp_path)
    record = _record()
    receipt_ref = outbox.write(record)
    restored = outbox.read(
        outbox_ref=record.outbox_ref,
        account_ref=record.account_ref,
        room_ref=record.room_ref,
    )
    assert receipt_ref.startswith("receipt-ref:matrix-outbox:write:sha256:")
    assert restored == record
    assert outbox.plaintext_absent(("transient-content-marker-v1",))
    assert "transient-content-marker-v1" not in repr(restored)


def test_outbox_key_failure_and_cross_room_substitution_fail_closed(
    tmp_path: Path,
) -> None:
    outbox, backend = _outbox(tmp_path)
    record = _record()
    outbox.write(record)
    with pytest.raises(MatrixOutboxError, match="DECRYPTION_FAILED"):
        outbox.read(
            outbox_ref=record.outbox_ref,
            account_ref=record.account_ref,
            room_ref="room-ref:matrix:substitution-v2",
        )
    backend.locked = True
    with pytest.raises(MatrixCacheKeyUnavailable, match="BACKEND_LOCKED"):
        outbox.read(
            outbox_ref=record.outbox_ref,
            account_ref=record.account_ref,
            room_ref=record.room_ref,
        )


def test_uncertain_outcome_cannot_retry_without_reconciliation(tmp_path: Path) -> None:
    outbox, _backend = _outbox(tmp_path)
    sending = _record(state=MatrixOutboxState.sending)
    outbox.write(sending)
    uncertain, _receipt = outbox.transition(
        record=sending,
        expected_state=MatrixOutboxState.sending,
        next_state=MatrixOutboxState.outcome_uncertain,
        next_generation_ref="outbox-generation-ref:matrix:uncertain-v2",
        failure_reason_ref="reason-ref:matrix-send:outcome-uncertain",
    )
    with pytest.raises(MatrixOutboxError, match="TRANSITION_DENIED"):
        outbox.transition(
            record=uncertain,
            expected_state=MatrixOutboxState.outcome_uncertain,
            next_state=MatrixOutboxState.queued,
            next_generation_ref="outbox-generation-ref:matrix:retry-v3",
        )


def test_outbox_discard_is_idempotent(tmp_path: Path) -> None:
    outbox, _backend = _outbox(tmp_path)
    record = _record()
    outbox.write(record)
    first = outbox.discard(outbox_ref=record.outbox_ref)
    second = outbox.discard(outbox_ref=record.outbox_ref)
    assert first == second
    with pytest.raises(MatrixOutboxError, match="NOT_FOUND"):
        outbox.read(
            outbox_ref=record.outbox_ref,
            account_ref=record.account_ref,
            room_ref=record.room_ref,
        )


def test_outbox_rejects_overwrite_and_stale_generation(tmp_path: Path) -> None:
    outbox, _backend = _outbox(tmp_path)
    queued = _record()
    outbox.write(queued)
    with pytest.raises(MatrixOutboxError, match="RECORD_ALREADY_EXISTS"):
        outbox.write(queued)
    sending, _receipt = outbox.transition(
        record=queued,
        expected_state=MatrixOutboxState.queued,
        next_state=MatrixOutboxState.sending,
        next_generation_ref="outbox-generation-ref:matrix:sending-v2",
    )
    assert sending.state == MatrixOutboxState.sending
    with pytest.raises(MatrixOutboxError, match="STATE_CONFLICT"):
        outbox.transition(
            record=queued,
            expected_state=MatrixOutboxState.queued,
            next_state=MatrixOutboxState.sending,
            next_generation_ref="outbox-generation-ref:matrix:stale-v3",
        )


def test_remote_echo_transition_preserves_bound_remote_event_ref(
    tmp_path: Path,
) -> None:
    outbox, _backend = _outbox(tmp_path)
    queued = _record()
    outbox.write(queued)
    sending, _ = outbox.transition(
        record=queued,
        expected_state=MatrixOutboxState.queued,
        next_state=MatrixOutboxState.sending,
        next_generation_ref="outbox-generation-ref:matrix:sending-v2",
    )
    acknowledged, _ = outbox.transition(
        record=sending,
        expected_state=MatrixOutboxState.sending,
        next_state=MatrixOutboxState.server_acknowledged,
        next_generation_ref="outbox-generation-ref:matrix:acknowledged-v3",
        remote_event_ref="event-ref:matrix:remote-v1",
    )
    remote_echo, _ = outbox.transition(
        record=acknowledged,
        expected_state=MatrixOutboxState.server_acknowledged,
        next_state=MatrixOutboxState.remote_echo,
        next_generation_ref="outbox-generation-ref:matrix:remote-echo-v4",
    )
    assert remote_echo.remote_event_ref == acknowledged.remote_event_ref


def test_live_runtime_writes_only_exact_bound_encrypted_outbox(tmp_path: Path) -> None:
    outbox, _backend = _outbox(tmp_path)
    record = _record()
    binary = Path("/usr/bin/true").resolve()
    broker = MatrixBrokerClient(
        MatrixBrokerConfig(
            binary_path=binary,
            expected_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            state_root=(tmp_path / "broker-state").resolve(),
        )
    )
    runtime = MatrixMessagingRuntime.live(
        broker_client=broker,
        outbox=outbox,
        runtime_input=MatrixMessagingRuntimeInput(outbox_record=record),
    )
    command = _command(
        MatrixMessagingOperation.outbox_enqueue,
        outbox_message_operation=MatrixMessagingOperation.send,
        content_fingerprint_ref=record.content_fingerprint_ref,
        rollback_ref=matrix_messaging_rollback_ref(
            MatrixMessagingOperation.outbox_enqueue
        ),
    )
    result = runtime.execute(command, "approval-ref:matrix-messaging:exact-v1")
    assert result.succeeded is True
    restored = outbox.read(
        outbox_ref=record.outbox_ref,
        account_ref=record.account_ref,
        room_ref=record.room_ref,
    )
    assert restored == record
    assert outbox.plaintext_absent(("transient-content-marker-v1",))

    changed = record.model_copy(
        update={"body": "transient-content-marker-changed-v2"}
    )
    with pytest.raises(ValidationError, match="CONTENT_FINGERPRINT_MISMATCH"):
        MatrixOutboxRecord.model_validate(changed.model_dump(mode="python"))


def test_broker_response_must_match_exact_invocation() -> None:
    now = datetime.now(UTC)
    invocation = MatrixBrokerInvocation(
        operation="send",
        request_ref="request-ref:matrix-broker:exact-v1",
        request_fingerprint_ref="request-fingerprint-ref:matrix-broker:exact-v1",
        nonce="a" * 64,
        issued_at=now,
        deadline=now + timedelta(seconds=30),
        account_ref="account-ref:matrix:exact-v1",
        homeserver_ref="homeserver-ref:matrix:exact-v1",
        device_ref="device-ref:matrix:exact-v1",
        approval_ref="approval-ref:matrix:exact-v1",
        lease_ref="authority-lease-ref:matrix:exact-v1",
        idempotency_ref="idempotency-ref:matrix:exact-v1",
        budget_ref="budget-ref:matrix:exact-v1",
        readiness_ref="readiness-ref:matrix:exact-v1",
        room_ref="room-ref:matrix:exact-v1",
        transaction_ref="transaction-ref:matrix:exact-v1",
    )
    response = MatrixBrokerResponse(
        protocol_version="uaa-matrix-rust-broker-response.v1",
        ok=True,
        operation="send",
        request_ref=invocation.request_ref,
        request_fingerprint_ref=invocation.request_fingerprint_ref,
        receipt_ref="receipt-ref:matrix-broker:exact-v1",
        outcome="server_acknowledged",
        transaction_ref=invocation.transaction_ref,
        replayed=False,
        credential_material_included=False,
        content_included=False,
        raw_identifiers_included=False,
    )
    broker_module._validate_response_binding(response, invocation)
    changed = response.model_copy(update={"request_ref": "request-ref:matrix-broker:changed-v2"})
    with pytest.raises(MatrixBrokerError, match="RESPONSE_BINDING_MISMATCH"):
        broker_module._validate_response_binding(changed, invocation)


@pytest.mark.parametrize(
    ("operation", "reaction_key"),
    [
        (MatrixMessagingOperation.reaction, "thumbs-up"),
        (MatrixMessagingOperation.redaction, None),
    ],
)
def test_reaction_and_redaction_transients_do_not_smuggle_message_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: MatrixMessagingOperation,
    reaction_key: str | None,
) -> None:
    event_ref = "event-ref:matrix:exact-v1"
    event_id = "$event:localhost"
    content_fingerprint_ref = matrix_outbox_content_fingerprint_ref(
        operation=operation,
        room_id="!room:localhost",
        event_id=event_id,
        transaction_id="transaction-exact-v1",
        body=None,
        formatted_body=None,
        mention_user_ids=(),
        reaction_key=reaction_key,
    )
    now = datetime.now(UTC)
    record = MatrixOutboxRecord(
        outbox_ref="outbox-ref:matrix:exact-v1",
        generation_ref="outbox-generation-ref:matrix:exact-v1",
        account_ref="account-ref:matrix:exact-v1",
        room_ref="room-ref:matrix:exact-v1",
        event_ref=event_ref,
        transaction_ref="transaction-ref:matrix:exact-v1",
        operation=operation,
        content_fingerprint_ref=content_fingerprint_ref,
        state=MatrixOutboxState.queued,
        created_at=now,
        expires_at=now + timedelta(minutes=15),
        room_id="!room:localhost",
        event_id=event_id,
        transaction_id="transaction-exact-v1",
        reaction_key=reaction_key,
    )
    command = _command(
        operation,
        event_ref=event_ref,
        content_fingerprint_ref=(
            content_fingerprint_ref
            if operation == MatrixMessagingOperation.reaction
            else None
        ),
        rollback_ref=matrix_messaging_rollback_ref(operation),
    )
    outbox, _backend = _outbox(tmp_path)
    outbox.write(record)
    binary = Path("/usr/bin/true").resolve()
    broker = MatrixBrokerClient(
        MatrixBrokerConfig(
            binary_path=binary,
            expected_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            state_root=(tmp_path / "broker").resolve(),
        )
    )
    captured: list[object] = []

    def execute(
        _self: MatrixBrokerClient,
        invocation: MatrixBrokerInvocation,
        *,
        transient: object,
    ) -> MatrixBrokerResponse:
        captured.append(transient)
        return MatrixBrokerResponse(
            protocol_version="uaa-matrix-rust-broker-response.v1",
            ok=True,
            operation=invocation.operation,
            request_ref=invocation.request_ref,
            request_fingerprint_ref=invocation.request_fingerprint_ref,
            receipt_ref="receipt-ref:matrix-broker:exact-v1",
            outcome="server_acknowledged",
            event_ref="event-ref:matrix:remote-v1",
            transaction_ref=invocation.transaction_ref,
            replayed=False,
            credential_material_included=False,
            content_included=False,
            raw_identifiers_included=False,
        )

    monkeypatch.setattr(MatrixBrokerClient, "execute", execute)
    runtime = MatrixMessagingRuntime.live(
        broker_client=broker,
        outbox=outbox,
        runtime_input=MatrixMessagingRuntimeInput(homeserver_url="http://localhost"),
    )
    result = runtime.execute(command, "approval-ref:matrix:exact-v1")
    assert result.succeeded is True
    assert len(captured) == 1
    transient = captured[0]
    assert isinstance(transient, MatrixBrokerTransientInput)
    assert transient.body is None
    assert transient.formatted_body is None
    assert transient.mention_user_ids is None
    assert transient.event_id == event_id
    if operation == MatrixMessagingOperation.reaction:
        assert transient.relation_event_id == event_id
        assert transient.reaction_key == reaction_key
    else:
        assert transient.relation_event_id is None
        assert transient.reaction_key is None


def test_broker_uncertain_replay_requires_safe_error_code() -> None:
    with pytest.raises(ValidationError, match="ERROR_POSTURE_INVALID"):
        MatrixBrokerResponse(
            protocol_version="uaa-matrix-rust-broker-response.v1",
            ok=False,
            operation="send",
            request_ref="request-ref:matrix-broker:exact-v1",
            request_fingerprint_ref="request-fingerprint-ref:matrix-broker:exact-v1",
            receipt_ref="receipt-ref:matrix-broker:exact-v1",
            outcome="outcome_uncertain",
            transaction_ref="transaction-ref:matrix:exact-v1",
            replayed=True,
            credential_material_included=False,
            content_included=False,
            raw_identifiers_included=False,
        )


def test_desktop_notification_is_fixed_content_and_rejects_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "darwin")
    with pytest.raises(
        MatrixDesktopNotificationError,
        match="EXECUTABLE_SUBSTITUTION_DENIED",
    ):
        MatrixDesktopNotifier(executable=Path("/usr/bin/true"))

    calls: list[object] = []

    def run(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("subprocess.run", run)
    notifier = MatrixDesktopNotifier()
    command = _command(
        MatrixMessagingOperation.desktop_notify,
        transaction_ref=None,
        outbox_ref=None,
        outbox_generation_ref=None,
        expected_outbox_state=None,
        event_ref="event-ref:matrix:exact-v1",
        notification_target_ref=MATRIX_MESSAGING_NOTIFICATION_TARGET_REF,
        notification_policy_ref=MATRIX_MESSAGING_NOTIFICATION_POLICY_REF,
        notification_disclosure_ref=MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF,
        notification_generation_ref="notification-generation-ref:matrix:exact-v1",
        rollback_ref=matrix_messaging_rollback_ref(
            MatrixMessagingOperation.desktop_notify
        ),
    )
    receipt = notifier.notify(command)
    assert receipt.displayed is True
    assert receipt.content_included is False
    serialized_call = repr(calls)
    assert "New Matrix activity" in serialized_call
    assert "transient-content-marker" not in serialized_call


def test_native_process_static_profiles_are_exact_and_tamper_evident() -> None:
    broker_source = Path(MATRIX_MESSAGING_BROKER_REL).read_text()
    notifier_source = Path(MATRIX_MESSAGING_NOTIFIER_REL).read_text()
    assert is_exact_matrix_messaging_broker_subprocess_site(
        rel_path=MATRIX_MESSAGING_BROKER_REL,
        source=broker_source,
        fragment="subprocess.Popen(",
    )
    assert is_exact_matrix_messaging_notifier_subprocess_site(
        rel_path=MATRIX_MESSAGING_NOTIFIER_REL,
        source=notifier_source,
        fragment="subprocess.run(",
    )
    assert not is_exact_matrix_messaging_broker_subprocess_site(
        rel_path=MATRIX_MESSAGING_BROKER_REL,
        source=broker_source + "\n# changed\n",
        fragment="subprocess.Popen(",
    )
    assert not is_exact_matrix_messaging_notifier_subprocess_site(
        rel_path=MATRIX_MESSAGING_NOTIFIER_REL,
        source=notifier_source.replace("shell=False", "shell=True"),
        fragment="subprocess.run(",
    )
