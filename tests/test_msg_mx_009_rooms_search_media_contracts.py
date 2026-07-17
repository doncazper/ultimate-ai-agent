from __future__ import annotations

import hashlib
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.authority_surfaces import (
    build_matrix_rooms_media_lease_issue_request,
    capture_exact_matrix_rooms_media_approval,
    issue_exact_matrix_rooms_media_lease,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.constants import (
    EXTERNAL_MUTATION_OPERATIONS,
    MATRIX_ROOMS_MEDIA_LANES,
    MatrixRoomsMediaOperation,
    matrix_rooms_media_lane,
    matrix_rooms_media_rollback_ref,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.contracts import (
    MatrixRoomsMediaCommand,
    MatrixRoomsMediaReadiness,
    build_matrix_rooms_media_command,
    build_matrix_rooms_media_proposal,
    stable_matrix_rooms_media_ref,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.media import (
    MatrixMediaError,
    MatrixMediaStore,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.search import (
    MatrixEncryptedSearchError,
    MatrixEncryptedSearchIndex,
    MatrixSearchDocument,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.service import (
    MatrixRoomsMediaRuntime,
    MatrixRoomsMediaRuntimeInput,
    execute_matrix_rooms_media_command,
)
from ultimate_ai_agent.core.communications.matrix_messaging.broker import (
    MatrixBrokerClient,
    MatrixBrokerConfig,
    MatrixBrokerError,
    MatrixBrokerInvocation,
    MatrixBrokerTransientInput,
)
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    MATRIX_LOCAL_HARNESS_ORIGIN,
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync import matrix_sync_private_ref
from ultimate_ai_agent.core.communications.matrix_sync.cache import (
    InMemoryMatrixCacheCryptoBackend,
)


def _command(
    operation: MatrixRoomsMediaOperation, **updates: object
) -> MatrixRoomsMediaCommand:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "operation": operation,
        "request_ref": "request-ref:msg-mx-009:test",
        "task_ref": "task-ref:msg-mx-009:test",
        "mission_ref": "mission-ref:msg-mx-009:test",
        "run_ref": "run-ref:msg-mx-009:test",
        "dispatch_ref": f"dispatch-ref:msg-mx-009:{operation.value}",
        "idempotency_ref": f"idempotency-ref:msg-mx-009:{operation.value}",
        "lease_ref": f"lease-ref:msg-mx-009:{operation.value}",
        "account_ref": "account-ref:matrix:test",
        "homeserver_ref": "homeserver-ref:matrix:sha256:" + "a" * 64,
        "device_ref": "device-ref:matrix:test",
        "readiness_ref": f"readiness-ref:msg-mx-009:{operation.value}",
        "rollback_ref": matrix_rooms_media_rollback_ref(operation),
        "request_created_at": now,
        "start_deadline": now + timedelta(minutes=4),
    }
    refs = {
        "room_ref": "room-ref:matrix:sha256:" + "b" * 64,
        "member_ref": "member-ref:matrix:sha256:" + "c" * 64,
        "event_ref": "event-ref:matrix:sha256:" + "d" * 64,
        "transaction_ref": "transaction-ref:matrix:sha256:" + "e" * 64,
        "space_ref": "space-ref:matrix:sha256:" + "f" * 64,
        "media_ref": "media-ref:matrix:sha256:" + "1" * 64,
        "source_file_ref": "source-file-ref:matrix-media:sha256:" + "2" * 64,
        "quarantine_ref": "quarantine-ref:matrix-media:sha256:" + "3" * 64,
        "materialization_ref": "materialization-ref:matrix-media:sha256:" + "4" * 64,
        "filesystem_root_ref": "filesystem-root-ref:matrix-media:sha256:" + "5" * 64,
        "search_index_ref": "search-index-ref:matrix:sha256:" + "6" * 64,
        "query_ref": "query-ref:matrix-search:sha256:" + "7" * 64,
        "room_allowlist_ref": "room-allowlist-ref:matrix-search:sha256:" + "8" * 64,
        "prior_state_ref": "state-ref:matrix:sha256:" + "9" * 64,
        "desired_state_ref": "state-ref:matrix:sha256:" + "0" * 64,
        "declared_media_type_ref": "media-type-ref:matrix:sha256:" + "a" * 64,
        "parser_ref": "parser-ref:matrix-media:metadata-only-v1",
    }
    fields: dict[MatrixRoomsMediaOperation, tuple[str, ...]] = {
        MatrixRoomsMediaOperation.dm_create: ("member_ref", "transaction_ref"),
        MatrixRoomsMediaOperation.room_create: ("desired_state_ref", "transaction_ref"),
        MatrixRoomsMediaOperation.room_join: (
            "room_ref",
            "transaction_ref",
            "prior_state_ref",
        ),
        MatrixRoomsMediaOperation.room_leave: (
            "room_ref",
            "transaction_ref",
            "prior_state_ref",
        ),
        MatrixRoomsMediaOperation.invite_send: (
            "room_ref",
            "member_ref",
            "transaction_ref",
            "prior_state_ref",
        ),
        MatrixRoomsMediaOperation.invite_accept: (
            "room_ref",
            "transaction_ref",
            "prior_state_ref",
        ),
        MatrixRoomsMediaOperation.invite_reject: (
            "room_ref",
            "transaction_ref",
            "prior_state_ref",
        ),
        MatrixRoomsMediaOperation.invite_withdraw: (
            "room_ref",
            "member_ref",
            "transaction_ref",
            "prior_state_ref",
        ),
        MatrixRoomsMediaOperation.room_power_role_write: (
            "room_ref",
            "member_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.space_mapping_write: (
            "room_ref",
            "space_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.notification_settings_write: (
            "room_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.history_visibility_write: (
            "room_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.pin_write: (
            "room_ref",
            "event_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.account_room_preference_write: (
            "room_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.search_local_read: (
            "search_index_ref",
            "query_ref",
            "room_allowlist_ref",
        ),
        MatrixRoomsMediaOperation.media_upload: (
            "room_ref",
            "media_ref",
            "source_file_ref",
            "filesystem_root_ref",
            "declared_media_type_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.media_download_quarantine: (
            "room_ref",
            "media_ref",
            "quarantine_ref",
            "filesystem_root_ref",
            "declared_media_type_ref",
            "transaction_ref",
        ),
        MatrixRoomsMediaOperation.media_materialize: (
            "media_ref",
            "quarantine_ref",
            "materialization_ref",
            "filesystem_root_ref",
            "declared_media_type_ref",
        ),
        MatrixRoomsMediaOperation.media_preview: (
            "media_ref",
            "quarantine_ref",
            "filesystem_root_ref",
            "parser_ref",
            "declared_media_type_ref",
        ),
        MatrixRoomsMediaOperation.media_cleanup: (
            "media_ref",
            "quarantine_ref",
            "filesystem_root_ref",
            "prior_state_ref",
            "declared_media_type_ref",
        ),
    }
    payload.update({name: refs[name] for name in fields[operation]})
    payload.update(updates)
    return build_matrix_rooms_media_command(**payload)


def test_twenty_exact_lanes_are_request_scoped_and_composites_are_narrow() -> None:
    assert len(MATRIX_ROOMS_MEDIA_LANES) == 20
    upload = matrix_rooms_media_lane(MatrixRoomsMediaOperation.media_upload)
    assert upload.requested_domains == {
        AuthorityDomain.messages: (AuthorityCapability.upload,),
        AuthorityDomain.files: (AuthorityCapability.read,),
    }
    download = matrix_rooms_media_lane(
        MatrixRoomsMediaOperation.media_download_quarantine
    )
    assert download.requested_domains == {
        AuthorityDomain.messages: (AuthorityCapability.download,),
        AuthorityDomain.files: (AuthorityCapability.write,),
    }
    assert all(lane.side_effect_class for lane in MATRIX_ROOMS_MEDIA_LANES.values())
    assert MatrixRoomsMediaOperation.media_download_quarantine not in (
        EXTERNAL_MUTATION_OPERATIONS
    )
    assert MatrixRoomsMediaOperation.media_upload in EXTERNAL_MUTATION_OPERATIONS


@pytest.mark.parametrize("operation", tuple(MatrixRoomsMediaOperation))
def test_every_operation_builds_content_free_proposal(
    operation: MatrixRoomsMediaOperation,
) -> None:
    command = _command(operation)
    proposal = build_matrix_rooms_media_proposal(command)
    assert proposal.operation == operation
    assert proposal.request_scoped_evaluation_required
    assert not proposal.approval_ref_authorizes_execution
    assert not proposal.execution_permitted
    assert not proposal.mutation_performed
    assert not proposal.raw_content_included


def test_composite_authority_requires_exact_full_domain_map(tmp_path: Path) -> None:
    command = _command(MatrixRoomsMediaOperation.media_upload)
    store = AuthorityLeaseStore(tmp_path)
    lease, receipt = issue_exact_matrix_rooms_media_lease(
        command, store=store, confirmed=True
    )
    assert receipt.status == "issued"
    assert lease.domains == {
        "messages": ["upload"],
        "files": ["read"],
    }
    request = build_matrix_rooms_media_lease_issue_request(command)
    substituted = request.model_copy(
        update={
            "requested_domains": {
                AuthorityDomain.messages: [AuthorityCapability.upload],
                AuthorityDomain.files: [AuthorityCapability.write],
            }
        }
    )
    requirement_store = AuthorityLeaseStore(tmp_path / "substituted")
    denied_lease, denied_receipt = requirement_store.issue_lease(
        substituted,
        idempotency_ref="idempotency-ref:msg-mx-009:substituted",
    )
    assert denied_lease is None
    assert denied_receipt.status == "denied"


def test_approval_is_exact_and_proposal_does_not_authorize() -> None:
    command = _command(MatrixRoomsMediaOperation.room_power_role_write)
    authority = LocalApprovalAuthority()
    with pytest.raises(ValueError, match="EXACT_CONFIRMATION_REQUIRED"):
        capture_exact_matrix_rooms_media_approval(
            command, approval_authority=authority, confirmed=False
        )
    approval_ref = capture_exact_matrix_rooms_media_approval(
        command, approval_authority=authority, confirmed=True
    )
    assert approval_ref.startswith("approval-ref:matrix-rooms-media:")


def test_fingerprint_rejects_target_power_and_limit_substitution() -> None:
    command = _command(MatrixRoomsMediaOperation.room_power_role_write)
    for update in (
        {"room_ref": "room-ref:matrix:sha256:" + "1" * 64},
        {"desired_state_ref": "state-ref:matrix:sha256:" + "2" * 64},
        {"max_bytes": command.max_bytes - 1},
    ):
        with pytest.raises(ValueError, match="REQUEST_FINGERPRINT_MISMATCH"):
            MatrixRoomsMediaCommand.model_validate(
                {**command.model_dump(mode="python"), **update}
            )


def test_operation_scope_rejects_extraneous_refs() -> None:
    with pytest.raises(ValueError, match="EXTRANEOUS_SCOPE_FORBIDDEN"):
        _command(
            MatrixRoomsMediaOperation.dm_create,
            room_ref="room-ref:matrix:sha256:" + "1" * 64,
        )


def test_preview_parser_substitution_is_rejected_by_the_command_contract() -> None:
    with pytest.raises(ValueError, match="parser_ref"):
        _command(
            MatrixRoomsMediaOperation.media_preview,
            parser_ref="parser-ref:matrix-media:external-handler-v1",
        )


def _media_store(tmp_path: Path) -> MatrixMediaStore:
    return MatrixMediaStore(root=(tmp_path / "media").resolve())


def test_media_rejects_symlink_fifo_archive_executable_and_mime_confusion(
    tmp_path: Path,
) -> None:
    store = _media_store(tmp_path)
    upload_root = store.root / "media-upload-source"
    source = upload_root / "source.txt"
    source.write_text("safe text")
    source.chmod(0o600)
    data, inspection = store.read_upload_source(
        path=source, declared_media_type="text/plain", max_bytes=100
    )
    assert data == b"safe text" and inspection.byte_count == 9

    symlink = upload_root / "link.txt"
    symlink.symlink_to(source)
    with pytest.raises(MatrixMediaError, match="SOURCE_PATH_DENIED"):
        store.read_upload_source(
            path=symlink, declared_media_type="text/plain", max_bytes=100
        )

    fifo = upload_root / "pipe.txt"
    os.mkfifo(fifo, 0o600)
    with pytest.raises(MatrixMediaError, match="SOURCE_PATH_DENIED"):
        store.read_upload_source(
            path=fifo, declared_media_type="text/plain", max_bytes=100
        )

    for payload, error in (
        (b"PK\x03\x04" + b"x" * 20, "ARCHIVE_DENIED"),
        (b"MZ" + b"x" * 20, "EXECUTABLE_DENIED"),
        (b"not-a-png", "MIME_CONFUSION_DENIED"),
    ):
        with pytest.raises(MatrixMediaError, match=error):
            store.inspect(data=payload, declared_media_type="image/png")

    outside = store.root / "outside.txt"
    outside.write_text("outside")
    outside.chmod(0o600)
    traversal = upload_root / ".." / "outside.txt"
    for denied_path in (traversal, Path("/dev/null")):
        with pytest.raises(MatrixMediaError, match="SOURCE_OUTSIDE_APP_ROOT"):
            store.read_upload_source(
                path=denied_path,
                declared_media_type="text/plain",
                max_bytes=100,
            )

    for compressed_bomb_header in (
        b"PK\x03\x04" + b"A" * 128,
        b"\x1f\x8b" + b"A" * 128,
    ):
        with pytest.raises(MatrixMediaError, match="ARCHIVE_DENIED"):
            store.inspect(
                data=compressed_bomb_header,
                declared_media_type="text/plain",
            )


def test_quarantine_is_required_before_preview_and_cleanup_detects_substitution(
    tmp_path: Path,
) -> None:
    store = _media_store(tmp_path)
    quarantine_ref = "quarantine-ref:matrix-media:test"
    with pytest.raises(MatrixMediaError, match="QUARANTINE_REQUIRED"):
        store.inspect_quarantine(
            quarantine_ref=quarantine_ref,
            declared_media_type="text/plain",
            max_bytes=100,
        )
    quarantine = store.quarantine_path(quarantine_ref)
    quarantine.write_text("safe")
    quarantine.chmod(0o600)
    assert (
        store.inspect_quarantine(
            quarantine_ref=quarantine_ref,
            declared_media_type="text/plain",
            max_bytes=100,
        ).byte_count
        == 4
    )
    quarantine.unlink()
    quarantine.symlink_to(store.root / "missing")
    with pytest.raises(MatrixMediaError, match="CLEANUP_PATH_DENIED"):
        store.cleanup(
            quarantine_ref=quarantine_ref,
            materialization_ref=None,
            declared_media_type="text/plain",
        )


def test_media_store_rejects_directory_substitution_and_quarantine_fifo(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "prebuilt-media").resolve()
    root.mkdir(mode=0o700)
    outside = (tmp_path / "outside").resolve()
    outside.mkdir(mode=0o700)
    (root / "media-quarantine").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="DIRECTORY_UNSAFE"):
        MatrixMediaStore(root=root)

    store = _media_store(tmp_path / "fresh")
    quarantine = store.quarantine_path("quarantine-ref:matrix-media:fifo")
    os.mkfifo(quarantine, 0o600)
    with pytest.raises(MatrixMediaError, match="QUARANTINE_INVALID"):
        store.inspect_quarantine(
            quarantine_ref="quarantine-ref:matrix-media:fifo",
            declared_media_type="text/plain",
            max_bytes=100,
        )

    materialized = store.root / "media-materialized"
    materialized.rmdir()
    materialized.symlink_to(outside, target_is_directory=True)
    with pytest.raises(MatrixMediaError, match="DIRECTORY_SUBSTITUTION_DENIED"):
        store.cleanup(
            quarantine_ref="quarantine-ref:matrix-media:absent",
            materialization_ref=None,
            declared_media_type=None,
        )

    fresh_store = _media_store(tmp_path / "removed")
    shutil.rmtree(fresh_store.root)
    with pytest.raises(MatrixMediaError, match="ROOT_SUBSTITUTION_DENIED"):
        fresh_store.inspect_quarantine(
            quarantine_ref="quarantine-ref:matrix-media:absent",
            declared_media_type="text/plain",
            max_bytes=100,
        )


def test_media_cleanup_requires_type_for_materialized_target(tmp_path: Path) -> None:
    store = _media_store(tmp_path)
    with pytest.raises(MatrixMediaError, match="CLEANUP_TYPE_REQUIRED"):
        store.cleanup(
            quarantine_ref="quarantine-ref:matrix-media:absent",
            materialization_ref="materialization-ref:matrix-media:exact",
            declared_media_type=None,
        )


def test_media_and_search_constructors_do_not_chmod_symlink_targets(
    tmp_path: Path,
) -> None:
    media_target = tmp_path / "media-target"
    media_target.mkdir(mode=0o755)
    os.chmod(media_target, 0o755)
    media_link = tmp_path / "media-link"
    media_link.symlink_to(media_target, target_is_directory=True)
    with pytest.raises(ValueError, match="MATRIX_MEDIA_ROOT_UNSAFE"):
        MatrixMediaStore(root=media_link)
    assert os.stat(media_target).st_mode & 0o777 == 0o755

    search_target = tmp_path / "search-target"
    search_target.mkdir(mode=0o755)
    os.chmod(search_target, 0o755)
    search_link = tmp_path / "search-link"
    search_link.symlink_to(search_target, target_is_directory=True)
    crypto = InMemoryMatrixCacheCryptoBackend()
    crypto.create(
        key_item_ref="key-item-ref:matrix-search:test",
        key_version_ref="key-version-ref:matrix-search:v1",
    )
    with pytest.raises(ValueError, match="MATRIX_SEARCH_ROOT_UNSAFE"):
        MatrixEncryptedSearchIndex(
            root=search_link,
            crypto_backend=crypto,
            key_item_ref="key-item-ref:matrix-search:test",
            key_version_ref="key-version-ref:matrix-search:v1",
            token_key=b"t" * 32,
        )
    assert os.stat(search_target).st_mode & 0o777 == 0o755


def _search_index(tmp_path: Path) -> MatrixEncryptedSearchIndex:
    crypto = InMemoryMatrixCacheCryptoBackend()
    crypto.create(
        key_item_ref="key-item-ref:matrix-search:test",
        key_version_ref="key-version-ref:matrix-search:v1",
    )
    return MatrixEncryptedSearchIndex(
        root=(tmp_path / "search").resolve(),
        crypto_backend=crypto,
        key_item_ref="key-item-ref:matrix-search:test",
        key_version_ref="key-version-ref:matrix-search:v1",
        token_key=b"t" * 32,
    )


def test_encrypted_search_is_room_scoped_and_raw_content_is_absent(
    tmp_path: Path,
) -> None:
    index = _search_index(tmp_path)
    room_a = "room-ref:matrix:a"
    room_b = "room-ref:matrix:b"
    index_ref = "search-index-ref:matrix:test"
    index.rebuild(
        index_ref=index_ref,
        account_ref="account-ref:matrix:test",
        generation_ref="generation-ref:matrix-search:1",
        documents=(
            MatrixSearchDocument(
                room_ref=room_a, event_ref="event-ref:matrix:a", body="private alpha"
            ),
            MatrixSearchDocument(
                room_ref=room_b, event_ref="event-ref:matrix:b", body="private alpha"
            ),
        ),
        allowed_room_refs=frozenset({room_a, room_b}),
    )
    encrypted = next((tmp_path / "search").iterdir()).read_bytes()
    assert b"private" not in encrypted and b"alpha" not in encrypted
    assert index.search(
        index_ref=index_ref,
        account_ref="account-ref:matrix:test",
        query="alpha",
        allowed_room_refs=frozenset({room_a, room_b}),
        exact_room_ref=room_a,
        max_results=10,
    ) == ("event-ref:matrix:a",)
    with pytest.raises(MatrixEncryptedSearchError, match="ROOM_SCOPE_DENIED"):
        index.search(
            index_ref=index_ref,
            account_ref="account-ref:matrix:test",
            query="alpha",
            allowed_room_refs=frozenset({room_a}),
            exact_room_ref=room_b,
            max_results=10,
        )


def test_index_rebuild_removes_deleted_refs_and_purge_proves_path_absent(
    tmp_path: Path,
) -> None:
    index = _search_index(tmp_path)
    room = "room-ref:matrix:a"
    index_ref = "search-index-ref:matrix:test"
    index.rebuild(
        index_ref=index_ref,
        account_ref="account-ref:matrix:test",
        generation_ref="generation-ref:matrix-search:1",
        documents=(
            MatrixSearchDocument(
                room_ref=room, event_ref="event-ref:matrix:deleted", body="erase token"
            ),
        ),
        allowed_room_refs=frozenset({room}),
    )
    index.rebuild(
        index_ref=index_ref,
        account_ref="account-ref:matrix:test",
        generation_ref="generation-ref:matrix-search:2",
        documents=(),
        allowed_room_refs=frozenset({room}),
    )
    assert (
        index.search(
            index_ref=index_ref,
            account_ref="account-ref:matrix:test",
            query="erase",
            allowed_room_refs=frozenset({room}),
            exact_room_ref=None,
            max_results=10,
        )
        == ()
    )
    receipt = index.purge(index_ref=index_ref)
    assert receipt.startswith("receipt-ref:matrix-search:purge:")
    assert not any((tmp_path / "search").iterdir())


def test_search_limits_and_fifo_substitution_fail_closed(tmp_path: Path) -> None:
    index = _search_index(tmp_path)
    room = "room-ref:matrix:a"
    index_ref = "search-index-ref:matrix:test"
    index.rebuild(
        index_ref=index_ref,
        account_ref="account-ref:matrix:test",
        generation_ref="generation-ref:matrix-search:bounded",
        documents=(
            MatrixSearchDocument(
                room_ref=room,
                event_ref="event-ref:matrix:bounded",
                body="bounded query",
            ),
        ),
        allowed_room_refs=frozenset({room}),
    )
    with pytest.raises(MatrixEncryptedSearchError, match="QUERY_LIMIT_EXCEEDED"):
        index.search(
            index_ref=index_ref,
            account_ref="account-ref:matrix:test",
            query="x" * 4097,
            allowed_room_refs=frozenset({room}),
            exact_room_ref=None,
            max_results=10,
        )

    with pytest.raises(MatrixEncryptedSearchError, match="TOKEN_LIMIT_EXCEEDED"):
        index.rebuild(
            index_ref="search-index-ref:matrix:bounded-overflow",
            account_ref="account-ref:matrix:test",
            generation_ref="generation-ref:matrix-search:bounded-overflow",
            documents=(
                MatrixSearchDocument(
                    room_ref=room,
                    event_ref="event-ref:matrix:bounded-overflow",
                    body=" ".join(f"token{item}" for item in range(257)),
                ),
            ),
            allowed_room_refs=frozenset({room}),
        )

    encrypted_path = next((tmp_path / "search").iterdir())
    encrypted_path.unlink()
    os.mkfifo(encrypted_path, 0o600)
    with pytest.raises(MatrixEncryptedSearchError, match="INDEX_INVALID"):
        index.search(
            index_ref=index_ref,
            account_ref="account-ref:matrix:test",
            query="bounded",
            allowed_room_refs=frozenset({room}),
            exact_room_ref=None,
            max_results=10,
        )

    search_root = tmp_path / "search"
    shutil.rmtree(search_root)
    search_root.symlink_to(tmp_path / "outside-search", target_is_directory=True)
    with pytest.raises(MatrixEncryptedSearchError, match="ROOT_SUBSTITUTION_DENIED"):
        index.search(
            index_ref=index_ref,
            account_ref="account-ref:matrix:test",
            query="bounded",
            allowed_room_refs=frozenset({room}),
            exact_room_ref=None,
            max_results=10,
        )


def _broker_client(tmp_path: Path) -> MatrixBrokerClient:
    binary = (tmp_path / "matrix-broker").resolve()
    binary.write_bytes(b"#!/bin/sh\nexit 0\n")
    binary.chmod(0o700)
    return MatrixBrokerClient(
        MatrixBrokerConfig(
            binary_path=binary,
            expected_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            state_root=(tmp_path / "broker-state").resolve(),
        )
    )


def test_media_transfer_cancel_before_start_never_spawns_the_broker(
    tmp_path: Path,
) -> None:
    broker = _broker_client(tmp_path)
    now = datetime.now(UTC)
    invocation = MatrixBrokerInvocation(
        operation="media_upload",
        request_ref="request-ref:msg-mx-009:cancel",
        request_fingerprint_ref="request-fingerprint-ref:msg-mx-009:cancel",
        nonce="a" * 48,
        issued_at=now,
        deadline=now + timedelta(seconds=30),
        account_ref="account-ref:matrix:cancel",
        homeserver_ref="homeserver-ref:matrix:cancel",
        device_ref="device-ref:matrix:cancel",
        approval_ref="approval-ref:matrix-rooms-media:cancel",
        lease_ref="lease-ref:matrix-rooms-media:cancel",
        idempotency_ref="idempotency-ref:matrix-rooms-media:cancel",
        budget_ref="budget-ref:matrix-rooms-media:zero-cost-v1",
        readiness_ref="readiness-ref:matrix-rooms-media:cancel",
        room_ref="room-ref:matrix:cancel",
        transaction_ref="transaction-ref:matrix:cancel",
        media_ref="media-ref:matrix:cancel",
    )
    with pytest.raises(MatrixBrokerError, match="CANCELLED_BEFORE_START"):
        broker.execute(
            invocation,
            transient=MatrixBrokerTransientInput(),
            cancel_requested=lambda: True,
        )


def _runtime_for_command(
    tmp_path: Path,
    command: MatrixRoomsMediaCommand,
    *,
    runtime_input: MatrixRoomsMediaRuntimeInput,
    search_index: MatrixEncryptedSearchIndex | None = None,
) -> MatrixRoomsMediaRuntime:
    broker = _broker_client(tmp_path)
    media_store = MatrixMediaStore(
        root=broker.scope_root(
            account_ref=command.account_ref,
            homeserver_ref=command.homeserver_ref,
            device_ref=command.device_ref,
        )
    )
    return MatrixRoomsMediaRuntime.live(
        broker_client=broker,
        media_store=media_store,
        search_index=search_index or _search_index(tmp_path),
        runtime_input=runtime_input,
    )


def _ready(command: MatrixRoomsMediaCommand) -> MatrixRoomsMediaReadiness:
    observed = datetime.now(UTC)
    return MatrixRoomsMediaReadiness(
        readiness_ref=command.readiness_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
        adapter_ref=matrix_rooms_media_lane(command.operation).adapter_ref,
        status="ready",
        observed_at=observed,
        expires_at=min(command.start_deadline, observed + timedelta(seconds=10)),
        kill_switch_engaged=False,
        safe_disable_active=False,
        broker_integrity_verified=True,
        filesystem_root_verified=True,
        encrypted_index_available=True,
    )


def test_encrypted_search_dispatch_requires_exact_lease_approval_and_replays(
    tmp_path: Path,
) -> None:
    query = "bounded alpha"
    allowed_rooms = ("room-ref:matrix:allowed-a", "room-ref:matrix:allowed-b")
    query_ref = matrix_sync_private_ref("query-ref:matrix-search", b"m" * 32, query)
    allowlist_ref = stable_matrix_rooms_media_ref(
        "room-allowlist-ref:matrix-search", {"room_refs": sorted(allowed_rooms)}
    )
    command = _command(
        MatrixRoomsMediaOperation.search_local_read,
        query_ref=query_ref,
        room_allowlist_ref=allowlist_ref,
    )
    index = _search_index(tmp_path)
    index.rebuild(
        index_ref=command.search_index_ref,
        account_ref=command.account_ref,
        generation_ref="generation-ref:matrix-search:dispatch",
        documents=(
            MatrixSearchDocument(
                room_ref=allowed_rooms[0],
                event_ref="event-ref:matrix:search-result",
                body=query,
            ),
        ),
        allowed_room_refs=frozenset(allowed_rooms),
    )
    runtime = _runtime_for_command(
        tmp_path,
        command,
        search_index=index,
        runtime_input=MatrixRoomsMediaRuntimeInput(
            pseudonymization_salt=b"m" * 32,
            search_query=query,
            allowed_room_refs=allowed_rooms,
        ),
    )
    state_dir = (tmp_path / "authority").resolve()
    store = AuthorityLeaseStore(state_dir)
    approvals = LocalApprovalAuthority()
    issue_exact_matrix_rooms_media_lease(command, store=store, confirmed=True)

    denied = execute_matrix_rooms_media_command(
        command,
        authority_state_dir=state_dir,
        runtime=runtime,
        readiness_provider=_ready,
        lease_store=store,
        approval_authority=approvals,
    )
    assert denied.receipt.status == "denied"
    assert denied.receipt.execution_started is False

    approval_ref = capture_exact_matrix_rooms_media_approval(
        command,
        approval_authority=approvals,
        confirmed=True,
    )
    approved_state_dir = (tmp_path / "approved-authority").resolve()
    approved_store = AuthorityLeaseStore(approved_state_dir)
    issue_exact_matrix_rooms_media_lease(command, store=approved_store, confirmed=True)
    result = execute_matrix_rooms_media_command(
        command,
        authority_state_dir=approved_state_dir,
        runtime=runtime,
        readiness_provider=_ready,
        approval_ref=approval_ref,
        lease_store=approved_store,
        approval_authority=approvals,
    )
    replay = execute_matrix_rooms_media_command(
        command,
        authority_state_dir=approved_state_dir,
        runtime=runtime,
        readiness_provider=_ready,
        approval_ref=approval_ref,
        lease_store=approved_store,
        approval_authority=approvals,
    )
    assert result.receipt.status == "succeeded"
    assert result.adapter_result is not None
    assert result.adapter_result.safe_output["result_refs"] == [
        "event-ref:matrix:search-result"
    ]
    assert result.adapter_result.safe_output["raw_content_included"] is False
    assert replay.replayed is True
    assert replay.receipt.receipt_ref == result.receipt.receipt_ref


def test_unexpected_transient_scope_is_rejected_before_broker_execution(
    tmp_path: Path,
) -> None:
    salt = b"m" * 32
    member_id = "@member:localhost"
    transaction_id = "transaction-exact-v1"
    command = _command(
        MatrixRoomsMediaOperation.dm_create,
        homeserver_ref=matrix_homeserver_ref(MATRIX_LOCAL_HARNESS_ORIGIN),
        member_ref=matrix_sync_private_ref("member-ref:matrix", salt, member_id),
        transaction_ref=matrix_sync_private_ref(
            "transaction-ref:matrix", salt, transaction_id
        ),
    )
    runtime = _runtime_for_command(
        tmp_path,
        command,
        runtime_input=MatrixRoomsMediaRuntimeInput(
            homeserver_url=MATRIX_LOCAL_HARNESS_ORIGIN,
            pseudonymization_salt=salt,
            member_id=member_id,
            transaction_id=transaction_id,
            room_id="!smuggled-room:localhost",
        ),
    )
    with pytest.raises(ValueError, match="TRANSIENT_BINDING_MISMATCH"):
        runtime.execute(command, "approval-ref:matrix-rooms-media:test")


def test_room_create_binds_the_exact_name_and_rejects_desired_state_smuggling(
    tmp_path: Path,
) -> None:
    salt = b"m" * 32
    room_name = "Exact room"
    transaction_id = "transaction-exact-v1"
    command = _command(
        MatrixRoomsMediaOperation.room_create,
        homeserver_ref=matrix_homeserver_ref(MATRIX_LOCAL_HARNESS_ORIGIN),
        desired_state_ref=matrix_sync_private_ref("state-ref:matrix", salt, room_name),
        transaction_ref=matrix_sync_private_ref(
            "transaction-ref:matrix", salt, transaction_id
        ),
    )
    runtime = _runtime_for_command(
        tmp_path,
        command,
        runtime_input=MatrixRoomsMediaRuntimeInput(
            homeserver_url=MATRIX_LOCAL_HARNESS_ORIGIN,
            pseudonymization_salt=salt,
            transaction_id=transaction_id,
            room_name="Different room",
            desired_state=room_name,
        ),
    )
    with pytest.raises(ValueError, match="TRANSIENT_BINDING_MISMATCH"):
        runtime.execute(command, "approval-ref:matrix-rooms-media:test")


def test_runtime_rejects_media_store_outside_exact_broker_scope(tmp_path: Path) -> None:
    command = _command(MatrixRoomsMediaOperation.search_local_read)
    broker = _broker_client(tmp_path)
    runtime = MatrixRoomsMediaRuntime.live(
        broker_client=broker,
        media_store=MatrixMediaStore(root=(tmp_path / "wrong-media-root").resolve()),
        search_index=_search_index(tmp_path),
        runtime_input=MatrixRoomsMediaRuntimeInput(
            pseudonymization_salt=b"m" * 32,
            search_query="test",
            allowed_room_refs=(),
        ),
    )
    with pytest.raises(ValueError, match="BROKER_MEDIA_SCOPE_MISMATCH"):
        runtime.execute(command, "approval-ref:matrix-rooms-media:test")
