from __future__ import annotations

import errno
import json
import os
import signal
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ultimate_ai_agent.core.communications.matrix_session.backend import (
    create_matrix_runtime_snapshot,
    remove_matrix_runtime_snapshot,
    _validate_hash_bound_file as validate_matrix_runtime_file,
    _validate_runtime_integrity as validate_matrix_adapter_runtime_integrity,
)
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    MATRIX_LOCAL_HARNESS_ORIGIN,
    matrix_homeserver_ref,
    validate_matrix_transient_target,
)

from .constants import MATRIX_SYNC_MAX_BYTES, MatrixSyncOperation
from .contracts import MatrixSyncCommand, stable_matrix_sync_ref
from .normalization import (
    MatrixPrivateSyncBatch,
    matrix_sync_private_ref,
    normalize_matrix_sync_response,
    normalize_matrix_timeline_response,
)
from .transient import MatrixCredentialWriter, MatrixTransientBatchRegistry


class MatrixSyncTransportError(RuntimeError):
    pass


@dataclass(frozen=True, repr=False)
class MatrixSyncTransientTarget:
    base_url: str
    since_token: str | None = None
    room_ids: tuple[str, ...] = ()
    room_id: str | None = None
    pagination_token: str | None = None

    def __repr__(self) -> str:
        return "MatrixSyncTransientTarget(<redacted>)"


@dataclass(frozen=True)
class MatrixSyncTransportResult:
    batch_ref: str
    event_count: int
    byte_count: int
    batch_fingerprint_ref: str
    next_batch_ref: str
    _discard_callback: Callable[[], None] = field(repr=False, compare=False)

    def discard(self) -> None:
        self._discard_callback()


_MATRIX_EVENT_TYPES_BY_CLASS_REF: dict[str, tuple[str, ...]] = {
    "event-class-ref:matrix:message": ("m.room.message",),
    "event-class-ref:matrix:encrypted-placeholder": ("m.room.encrypted",),
    "event-class-ref:matrix:redaction": ("m.room.redaction",),
    "event-class-ref:matrix:reaction": ("m.reaction",),
    "event-class-ref:matrix:poll": (
        "m.poll.start",
        "org.matrix.msc3381.poll.start",
    ),
    "event-class-ref:matrix:room-metadata": (
        "m.room.avatar",
        "m.room.name",
        "m.room.topic",
        "m.space.parent",
    ),
    "event-class-ref:matrix:typing": ("m.typing",),
    "event-class-ref:matrix:receipt": ("m.receipt",),
}
_MINIMAL_SUBPROCESS_ENV = {
    "HOME": "/var/empty",
    "LANG": "C",
    "PATH": "/usr/bin:/bin",
    "TMPDIR": "/tmp",
}
_PROCESS_GROUP_GRACE_SECONDS = 2.0
_MATRIX_ROOM_ID_MAX_BYTES = 255


def _validate_file(path: Path, expected_sha256: str, *, executable: bool) -> None:
    validate_matrix_runtime_file(path, expected_sha256)
    if executable and not os.access(path, os.X_OK):
        raise ValueError("MATRIX_SYNC_RUNTIME_EXECUTABLE_REQUIRED")


def _terminate_process_group(
    process: subprocess.Popen[bytes],
    *,
    grace_seconds: float = _PROCESS_GROUP_GRACE_SECONDS,
) -> None:
    """Terminate and reap the permission-confined adapter within a bound."""
    if process.poll() is not None:
        process.wait(timeout=grace_seconds)
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired as exc:
        raise MatrixSyncTransportError("MATRIX_SYNC_PROCESS_REAP_FAILED") from exc


def _event_types_for_command(command: MatrixSyncCommand) -> tuple[str, ...]:
    event_types: list[str] = []
    try:
        for event_class_ref in command.event_class_refs:
            event_types.extend(_MATRIX_EVENT_TYPES_BY_CLASS_REF[event_class_ref])
    except KeyError as exc:
        raise MatrixSyncTransportError("MATRIX_SYNC_EVENT_SCOPE_DENIED") from exc
    if not event_types:
        raise MatrixSyncTransportError("MATRIX_SYNC_EVENT_SCOPE_REQUIRED")
    return tuple(dict.fromkeys(event_types))


def _validate_transient_scope(
    command: MatrixSyncCommand,
    *,
    target: MatrixSyncTransientTarget,
    pseudonymization_salt: bytes,
    allow_loopback_harness: bool,
) -> tuple[str, ...]:
    if len(pseudonymization_salt) != 32:
        raise MatrixSyncTransportError("MATRIX_SYNC_PSEUDONYMIZATION_SALT_INVALID")
    try:
        validate_matrix_transient_target(
            expected_homeserver_ref=command.homeserver_ref,
            endpoint_class_ref=command.endpoint_class_ref,
            endpoint_url=target.base_url,
            discovery_origin=None,
            expected_redirect_target_ref=None,
            callback_url=None,
        )
    except ValueError as exc:
        raise MatrixSyncTransportError(str(exc)) from exc
    if (
        matrix_homeserver_ref(target.base_url)
        == matrix_homeserver_ref(MATRIX_LOCAL_HARNESS_ORIGIN)
        and not allow_loopback_harness
    ):
        raise MatrixSyncTransportError("MATRIX_SYNC_LOOPBACK_HARNESS_DISABLED")
    event_types = _event_types_for_command(command)
    if command.operation == MatrixSyncOperation.sync_read:
        if target.room_id is not None or target.pagination_token is not None:
            raise MatrixSyncTransportError("MATRIX_SYNC_TRANSIENT_SCOPE_INVALID")
        expected_sync_cursor_ref = (
            "sync-cursor-ref:matrix:initial"
            if target.since_token is None
            else matrix_sync_private_ref(
                "sync-cursor-ref:matrix",
                pseudonymization_salt,
                target.since_token,
            )
        )
        if command.sync_cursor_ref != expected_sync_cursor_ref:
            raise MatrixSyncTransportError("MATRIX_SYNC_CURSOR_BINDING_MISMATCH")
        if any(
            not room_id or len(room_id.encode("utf-8")) > _MATRIX_ROOM_ID_MAX_BYTES
            for room_id in target.room_ids
        ):
            raise MatrixSyncTransportError("MATRIX_SYNC_ROOM_SCOPE_INVALID")
        room_refs = {
            matrix_sync_private_ref("room-ref:matrix", pseudonymization_salt, room_id)
            for room_id in target.room_ids
        }
        if len(room_refs) != len(target.room_ids) or room_refs != set(
            command.room_refs
        ):
            raise MatrixSyncTransportError("MATRIX_SYNC_ROOM_BINDING_MISMATCH")
    else:
        if (
            target.since_token is not None
            or target.room_ids
            or target.room_id is None
            or target.pagination_token is None
        ):
            raise MatrixSyncTransportError("MATRIX_SYNC_TRANSIENT_SCOPE_INVALID")
        if len(target.room_id.encode("utf-8")) > _MATRIX_ROOM_ID_MAX_BYTES:
            raise MatrixSyncTransportError("MATRIX_SYNC_ROOM_SCOPE_INVALID")
        room_ref = matrix_sync_private_ref(
            "room-ref:matrix", pseudonymization_salt, target.room_id
        )
        pagination_cursor_ref = matrix_sync_private_ref(
            "pagination-cursor-ref:matrix",
            pseudonymization_salt,
            target.pagination_token,
        )
        if command.room_refs != (room_ref,):
            raise MatrixSyncTransportError("MATRIX_SYNC_ROOM_BINDING_MISMATCH")
        if command.pagination_cursor_ref != pagination_cursor_ref:
            raise MatrixSyncTransportError("MATRIX_SYNC_CURSOR_BINDING_MISMATCH")
    return event_types


class MatrixSyncTransport:
    def __init__(
        self,
        *,
        node_binary: Path,
        runner_path: Path,
        expected_node_sha256: str,
        expected_runner_sha256: str,
        credential_writer: MatrixCredentialWriter,
        registry: MatrixTransientBatchRegistry,
        allow_loopback_harness: bool = False,
    ) -> None:
        _validate_file(node_binary, expected_node_sha256, executable=True)
        _validate_file(runner_path, expected_runner_sha256, executable=False)
        adapter_root = runner_path.parent.parent
        validate_matrix_adapter_runtime_integrity(
            adapter_root=adapter_root,
            package_lock_path=adapter_root / "package-lock.json",
            manifest_path=adapter_root / "runtime-integrity.json",
        )
        self._node_binary = node_binary
        self._runner_path = runner_path
        self._adapter_root = adapter_root
        self._expected_node_sha256 = expected_node_sha256
        self._expected_runner_sha256 = expected_runner_sha256
        self._credential_writer = credential_writer
        self._registry = registry
        self._allow_loopback_harness = allow_loopback_harness

    def execute(
        self,
        command: MatrixSyncCommand,
        *,
        target: MatrixSyncTransientTarget,
        pseudonymization_salt: bytes,
    ) -> MatrixSyncTransportResult:
        if command.operation not in {
            MatrixSyncOperation.sync_read,
            MatrixSyncOperation.timeline_paginate_read,
        }:
            raise MatrixSyncTransportError("MATRIX_SYNC_TRANSPORT_OPERATION_DENIED")
        event_types = _validate_transient_scope(
            command,
            target=target,
            pseudonymization_salt=pseudonymization_salt,
            allow_loopback_harness=self._allow_loopback_harness,
        )
        _validate_file(
            self._node_binary,
            self._expected_node_sha256,
            executable=True,
        )
        _validate_file(
            self._runner_path,
            self._expected_runner_sha256,
            executable=False,
        )
        validate_matrix_adapter_runtime_integrity(
            adapter_root=self._adapter_root,
            package_lock_path=self._adapter_root / "package-lock.json",
            manifest_path=self._adapter_root / "runtime-integrity.json",
        )
        runtime_snapshot = create_matrix_runtime_snapshot(
            adapter_root=self._adapter_root,
            node_binary=self._node_binary,
            runner_path=self._runner_path,
            expected_node_sha256=self._expected_node_sha256,
            expected_runner_sha256=self._expected_runner_sha256,
        )
        try:
            read_fd, write_fd = os.pipe()
        except BaseException:
            remove_matrix_runtime_snapshot(runtime_snapshot)
            raise
        request = {
            "schema_version": "uaa-matrix-sync-adapter-request.v1",
            "operation": command.operation.value,
            "request_fingerprint_ref": command.request_fingerprint_ref,
            "account_ref": command.account_ref,
            "session_generation_ref": command.session_generation_ref,
            "base_url": target.base_url,
            "since_token": target.since_token,
            "room_ids": list(target.room_ids),
            "room_id": target.room_id,
            "pagination_token": target.pagination_token,
            "event_types": list(event_types),
            "allow_harness": self._allow_loopback_harness,
            "max_events": command.max_events,
            "max_bytes": command.max_bytes,
            "max_duration_ms": command.max_duration_ms,
            "credential_fd": read_fd,
        }
        request = {key: value for key, value in request.items() if value is not None}
        read_fd_open = True
        write_fd_open = True
        try:
            process = subprocess.Popen(
                [
                    str(runtime_snapshot.node_binary),
                    "--permission",
                    f"--allow-fs-read={runtime_snapshot.adapter_root}",
                    str(runtime_snapshot.runner_path),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                cwd=runtime_snapshot.adapter_root,
                env=_MINIMAL_SUBPROCESS_ENV,
                start_new_session=True,
                pass_fds=(read_fd,),
            )
        except BaseException:
            for descriptor in (read_fd, write_fd):
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            remove_matrix_runtime_snapshot(runtime_snapshot)
            raise
        try:
            os.close(read_fd)
            read_fd_open = False
            try:
                self._credential_writer.write_once(
                    write_fd,
                    credential_item_ref=command.credential_item_ref,
                    credential_version_ref=command.credential_version_ref,
                    request_fingerprint_ref=command.request_fingerprint_ref,
                )
            finally:
                os.close(write_fd)
                write_fd_open = False
            try:
                stdout, stderr = process.communicate(
                    json.dumps(request, separators=(",", ":")).encode("utf-8"),
                    timeout=command.max_duration_ms / 1000,
                )
            except subprocess.TimeoutExpired as exc:
                _terminate_process_group(process)
                raise MatrixSyncTransportError("MATRIX_SYNC_TRANSPORT_TIMEOUT") from exc
        except BaseException:
            if process.poll() is None:
                _terminate_process_group(process)
            raise
        finally:
            cleanup_error: BaseException | None = None
            if read_fd_open:
                try:
                    os.close(read_fd)
                except OSError as exc:
                    if exc.errno != errno.EBADF:
                        cleanup_error = cleanup_error or exc
            if write_fd_open:
                try:
                    os.close(write_fd)
                except OSError as exc:
                    if exc.errno != errno.EBADF:
                        cleanup_error = cleanup_error or exc
            for stream in (
                getattr(process, "stdin", None),
                getattr(process, "stdout", None),
                getattr(process, "stderr", None),
            ):
                if stream is not None and not stream.closed:
                    try:
                        stream.close()
                    except BaseException as exc:
                        cleanup_error = cleanup_error or exc
            try:
                remove_matrix_runtime_snapshot(runtime_snapshot)
            except BaseException as exc:
                cleanup_error = cleanup_error or exc
            if cleanup_error is not None:
                raise MatrixSyncTransportError(
                    "MATRIX_SYNC_TRANSPORT_CLEANUP_UNCONFIRMED"
                ) from cleanup_error
        if process.returncode != 0:
            code = stderr.decode("ascii", errors="ignore").strip()
            if not code.startswith("MATRIX_"):
                code = "MATRIX_SYNC_ADAPTER_FAILURE"
            raise MatrixSyncTransportError(code[:128])
        if len(stdout) > min(command.max_bytes, MATRIX_SYNC_MAX_BYTES):
            raise MatrixSyncTransportError("MATRIX_SYNC_RESPONSE_TOO_LARGE")
        if command.operation == MatrixSyncOperation.timeline_paginate_read:
            if target.room_id is None:
                raise MatrixSyncTransportError("MATRIX_SYNC_PAGINATION_ROOM_REQUIRED")
            batch = normalize_matrix_timeline_response(
                account_ref=command.account_ref,
                raw_room_id=target.room_id,
                payload=stdout,
                pseudonymization_salt=pseudonymization_salt,
                allowed_room_refs=set(command.room_refs),
                allowed_event_types=set(event_types),
                max_event_envelopes=command.max_events,
            )
        else:
            batch = normalize_matrix_sync_response(
                account_ref=command.account_ref,
                payload=stdout,
                pseudonymization_salt=pseudonymization_salt,
                allowed_room_refs=set(command.room_refs) if command.room_refs else None,
                allowed_event_types=set(event_types),
                max_event_envelopes=command.max_events,
            )
        if batch.event_count > command.max_events:
            raise MatrixSyncTransportError("MATRIX_SYNC_EVENT_LIMIT_EXCEEDED")
        if batch.byte_count > command.max_bytes:
            raise MatrixSyncTransportError("MATRIX_SYNC_RESPONSE_TOO_LARGE")
        batch_ref = self._registry.register(
            batch, request_fingerprint_ref=command.request_fingerprint_ref
        )
        try:
            return MatrixSyncTransportResult(
                batch_ref=batch_ref,
                event_count=batch.event_count,
                byte_count=batch.byte_count,
                batch_fingerprint_ref=stable_matrix_sync_ref(
                    "batch-fingerprint-ref:matrix-sync",
                    {
                        "account_ref": batch.account_ref,
                        "next_batch_ref": batch.next_batch_ref,
                        "event_refs": [event.event_ref for event in batch.events],
                    },
                ),
                next_batch_ref=batch.next_batch_ref,
                _discard_callback=lambda: self.discard_batch(
                    batch_ref,
                    request_fingerprint_ref=command.request_fingerprint_ref,
                ),
            )
        except BaseException:
            self._registry.discard(
                batch_ref,
                request_fingerprint_ref=command.request_fingerprint_ref,
            )
            raise

    def consume_batch(
        self, batch_ref: str, *, request_fingerprint_ref: str
    ) -> MatrixPrivateSyncBatch:
        return self._registry.consume(
            batch_ref, request_fingerprint_ref=request_fingerprint_ref
        )

    def discard_batch(
        self,
        batch_ref: str,
        *,
        request_fingerprint_ref: str,
    ) -> None:
        self._registry.discard(
            batch_ref,
            request_fingerprint_ref=request_fingerprint_ref,
        )
