from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import selectors
import signal
import socket
import stat
import subprocess
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
)


MATRIX_BROKER_PROTOCOL_VERSION = "uaa-matrix-rust-broker.v1"
MATRIX_BROKER_RESPONSE_VERSION = "uaa-matrix-rust-broker-response.v1"
MATRIX_BROKER_ADAPTER_REF = "adapter-ref:matrix-rust-broker:v1"
MATRIX_BROKER_MAX_FRAME_BYTES = 64 * 1024
MATRIX_BROKER_MAX_READINESS_BYTES = 4 * 1024
MATRIX_BROKER_AUTH_KEY_BYTES = 32
MATRIX_BROKER_MAX_EXECUTABLE_BYTES = 64 * 1024 * 1024


class MatrixBrokerError(RuntimeError):
    pass


MatrixBrokerCancelCheck = Callable[[], bool]
MatrixBrokerProgressObserver = Callable[[str], None]


class _BrokerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class _Readiness(_BrokerModel):
    protocol_version: Literal["uaa-matrix-rust-broker.v1"]
    adapter_ref: Literal["adapter-ref:matrix-rust-broker:v1"]
    bind_ref: Literal["loopback-ref:ipv4:127.0.0.1"]
    port: int = Field(ge=1, le=65535)
    maximum_frame_bytes: Literal[65536]
    one_request_only: Literal[True]
    credential_material_included: Literal[False]


class _ResponseEnvelope(_BrokerModel):
    payload_b64: str = Field(min_length=1, max_length=MATRIX_BROKER_MAX_FRAME_BYTES)
    auth_tag: str = Field(pattern=r"^[0-9a-f]{64}$")


class MatrixBrokerResponse(_BrokerModel):
    protocol_version: Literal["uaa-matrix-rust-broker-response.v1"]
    ok: bool
    operation: str = Field(min_length=1, max_length=64)
    request_ref: str
    request_fingerprint_ref: str
    receipt_ref: str
    outcome: Literal[
        "ready",
        "created",
        "available",
        "rotated",
        "deleted",
        "authenticated",
        "restored",
        "logged_out",
        "server_acknowledged",
        "replayed",
        "blocked",
        "outcome_uncertain",
    ]
    event_ref: str | None = None
    transaction_ref: str | None = None
    quarantine_ref: str | None = None
    byte_count: int | None = Field(default=None, ge=0, le=24_576)
    replayed: bool
    credential_material_included: Literal[False]
    content_included: Literal[False]
    raw_identifiers_included: Literal[False]
    error_code: str | None = Field(default=None, pattern=r"^MATRIX_[A-Z0-9_]+$")

    @model_validator(mode="after")
    def validate_response(self) -> MatrixBrokerResponse:
        for value in (
            self.request_ref,
            self.request_fingerprint_ref,
            self.receipt_ref,
            self.event_ref,
            self.transaction_ref,
            self.quarantine_ref,
        ):
            if value is not None:
                validate_execution_ref(value, "matrix_broker_response_ref")
        validate_safe_execution_payload(
            self.model_dump(mode="json"), "matrix_broker_response"
        )
        if self.ok == (self.error_code is not None):
            raise ValueError("MATRIX_BROKER_RESPONSE_ERROR_POSTURE_INVALID")
        if self.outcome == "outcome_uncertain" and self.ok:
            raise ValueError("MATRIX_BROKER_UNCERTAIN_SUCCESS_FORBIDDEN")
        if self.ok and self.outcome == "blocked":
            raise ValueError("MATRIX_BROKER_BLOCKED_SUCCESS_FORBIDDEN")
        if not self.ok and self.outcome not in {"blocked", "outcome_uncertain"}:
            raise ValueError("MATRIX_BROKER_FAILURE_OUTCOME_INVALID")
        if self.replayed and self.outcome not in {"replayed", "outcome_uncertain"}:
            raise ValueError("MATRIX_BROKER_REPLAY_OUTCOME_INVALID")
        if self.outcome == "replayed" and not self.replayed:
            raise ValueError("MATRIX_BROKER_REPLAY_FLAG_REQUIRED")
        return self


@dataclass(frozen=True)
class MatrixBrokerConfig:
    binary_path: Path
    expected_binary_sha256: str
    state_root: Path
    startup_timeout_seconds: float = 10.0
    operation_timeout_seconds: float = 30.0
    _state_root_identity: tuple[int, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.binary_path.is_absolute() or not self.state_root.is_absolute():
            raise ValueError("MATRIX_BROKER_ABSOLUTE_PATHS_REQUIRED")
        if len(self.expected_binary_sha256) != 64 or any(
            value not in "0123456789abcdef" for value in self.expected_binary_sha256
        ):
            raise ValueError("MATRIX_BROKER_BINARY_DIGEST_INVALID")
        if not (0.1 <= self.startup_timeout_seconds <= 30):
            raise ValueError("MATRIX_BROKER_STARTUP_TIMEOUT_INVALID")
        if not (0.1 <= self.operation_timeout_seconds <= 300):
            raise ValueError("MATRIX_BROKER_OPERATION_TIMEOUT_INVALID")
        _validate_binary(self.binary_path, self.expected_binary_sha256)
        object.__setattr__(
            self, "_state_root_identity", _prepare_state_root(self.state_root)
        )


@dataclass(frozen=True)
class MatrixBrokerInvocation:
    operation: str
    request_ref: str
    request_fingerprint_ref: str
    nonce: str
    issued_at: datetime
    deadline: datetime
    account_ref: str
    homeserver_ref: str
    device_ref: str
    approval_ref: str
    lease_ref: str
    idempotency_ref: str
    budget_ref: str
    readiness_ref: str
    room_ref: str | None = None
    event_ref: str | None = None
    transaction_ref: str | None = None
    member_ref: str | None = None
    space_ref: str | None = None
    media_ref: str | None = None
    quarantine_ref: str | None = None
    secret_kind: str | None = None
    adapter_ref: str = MATRIX_BROKER_ADAPTER_REF
    safe_disable_ref: str = "safe-disable-ref:matrix-messenger:enabled"
    kill_switch_ref: str = "kill-switch-ref:matrix-messenger:clear"

    def __post_init__(self) -> None:
        if self.issued_at.tzinfo is None or self.deadline.tzinfo is None:
            raise ValueError("MATRIX_BROKER_TIMEZONE_REQUIRED")
        if not self.issued_at < self.deadline:
            raise ValueError("MATRIX_BROKER_DEADLINE_ORDER_INVALID")
        if (self.deadline - self.issued_at).total_seconds() > 300:
            raise ValueError("MATRIX_BROKER_DEADLINE_WINDOW_EXCEEDED")
        if not (32 <= len(self.nonce) <= 128) or not self.nonce.isalnum():
            raise ValueError("MATRIX_BROKER_NONCE_INVALID")
        for value in (
            self.request_ref,
            self.request_fingerprint_ref,
            self.account_ref,
            self.homeserver_ref,
            self.device_ref,
            self.approval_ref,
            self.lease_ref,
            self.idempotency_ref,
            self.budget_ref,
            self.readiness_ref,
            self.room_ref,
            self.event_ref,
            self.transaction_ref,
            self.member_ref,
            self.space_ref,
            self.media_ref,
            self.quarantine_ref,
            self.adapter_ref,
            self.safe_disable_ref,
            self.kill_switch_ref,
        ):
            if value is not None:
                validate_execution_ref(value, "matrix_broker_invocation_ref")


@dataclass(frozen=True, repr=False)
class MatrixBrokerTransientInput:
    homeserver_url: str | None = None
    username: str | None = None
    password: str | None = None
    room_id: str | None = None
    event_id: str | None = None
    transaction_id: str | None = None
    body: str | None = None
    formatted_body: str | None = None
    mention_user_ids: tuple[str, ...] | None = None
    relation_event_id: str | None = None
    reaction_key: str | None = None
    typing_active: bool | None = None
    member_id: str | None = None
    space_id: str | None = None
    room_name: str | None = None
    desired_state: str | None = None
    prior_state: str | None = None
    media_uri: str | None = None
    media_type: str | None = None
    media_b64: str | None = None

    def __repr__(self) -> str:
        return "MatrixBrokerTransientInput(<redacted>)"


class MatrixBrokerClient:
    def __init__(self, config: MatrixBrokerConfig) -> None:
        self._config = config
        self.binding_ref = (
            "broker-client-binding-ref:matrix:sha256:"
            + hashlib.sha256(
                json.dumps(
                    {
                        "adapter_ref": MATRIX_BROKER_ADAPTER_REF,
                        "binary_sha256": config.expected_binary_sha256,
                        "state_root_ref": hashlib.sha256(
                            os.fsencode(config.state_root)
                        ).hexdigest(),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
        )

    def scope_root(
        self,
        *,
        account_ref: str,
        homeserver_ref: str,
        device_ref: str,
    ) -> Path:
        """Return the exact per-account broker scope without creating it."""
        for value in (account_ref, homeserver_ref, device_ref):
            validate_execution_ref(value, "matrix_broker_scope_ref")
        digest = hashlib.sha256()
        digest.update(account_ref.encode())
        digest.update(b"\0")
        digest.update(homeserver_ref.encode())
        digest.update(b"\0")
        digest.update(device_ref.encode())
        return self._config.state_root / digest.hexdigest()[:32]

    def execute(
        self,
        invocation: MatrixBrokerInvocation,
        *,
        transient: MatrixBrokerTransientInput,
        cancel_requested: MatrixBrokerCancelCheck | None = None,
        progress_observer: MatrixBrokerProgressObserver | None = None,
    ) -> MatrixBrokerResponse:
        if _cancel_requested(cancel_requested):
            raise MatrixBrokerError("MATRIX_BROKER_CANCELLED_BEFORE_START")
        _emit_progress(progress_observer, "preflight")
        _validate_binary(self._config.binary_path, self._config.expected_binary_sha256)
        _validate_state_root(
            self._config.state_root,
            expected_identity=self._config._state_root_identity,
        )
        auth_key = bytearray(os.urandom(MATRIX_BROKER_AUTH_KEY_BYTES))
        auth_read_fd, auth_write_fd = os.pipe()
        root_read_fd, root_write_fd = os.pipe()
        process: subprocess.Popen[bytes] | None = None
        try:
            _write_all(auth_write_fd, auth_key)
            _write_all(root_write_fd, os.fsencode(self._config.state_root))
            os.close(auth_write_fd)
            auth_write_fd = -1
            os.close(root_write_fd)
            root_write_fd = -1
            with _staged_broker_binary(
                self._config.binary_path,
                self._config.expected_binary_sha256,
            ) as executable:
                process = subprocess.Popen(
                    [
                        os.fspath(executable),
                        f"--auth-fd={auth_read_fd}",
                        f"--state-root-fd={root_read_fd}",
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    cwd=executable.parent,
                    shell=False,
                    close_fds=True,
                    pass_fds=(auth_read_fd, root_read_fd),
                    start_new_session=True,
                    env={
                        "LANG": "C",
                        "LC_ALL": "C",
                        "PATH": "/usr/bin:/bin",
                        "RUST_BACKTRACE": "0",
                        "TMPDIR": "/tmp",
                    },
                )
                os.close(auth_read_fd)
                auth_read_fd = -1
                os.close(root_read_fd)
                root_read_fd = -1
                if process.stdout is None:
                    raise MatrixBrokerError("MATRIX_BROKER_STDOUT_PIPE_REQUIRED")
                readiness_bytes = _read_line_bounded(
                    process.stdout.fileno(),
                    maximum=MATRIX_BROKER_MAX_READINESS_BYTES,
                    timeout_seconds=self._config.startup_timeout_seconds,
                )
                try:
                    readiness = _Readiness.model_validate_json(readiness_bytes)
                except ValueError as exc:
                    raise MatrixBrokerError("MATRIX_BROKER_READINESS_INVALID") from exc
                request_payload = _request_payload(invocation, transient)
                response = _exchange(
                    readiness.port,
                    request_payload,
                    auth_key=auth_key,
                    timeout_seconds=min(
                        self._config.operation_timeout_seconds,
                        max(0.1, invocation.deadline.timestamp() - time.time()),
                    ),
                    cancel_requested=cancel_requested,
                    progress_observer=progress_observer,
                )
                _validate_response_binding(response, invocation)
                try:
                    return_code = process.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    _terminate_process_group(process)
                    raise MatrixBrokerError("MATRIX_BROKER_EXIT_TIMEOUT") from exc
                if return_code != 0:
                    raise MatrixBrokerError("MATRIX_BROKER_EXIT_FAILED")
                _emit_progress(progress_observer, "completed")
                return response
        except BaseException:
            if process is not None and process.poll() is None:
                _terminate_process_group(process)
            raise
        finally:
            for descriptor in (
                auth_read_fd,
                auth_write_fd,
                root_read_fd,
                root_write_fd,
            ):
                if descriptor >= 0:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
            for index in range(len(auth_key)):
                auth_key[index] = 0
            if process is not None and process.stdout is not None:
                process.stdout.close()


def _request_payload(
    invocation: MatrixBrokerInvocation,
    transient: MatrixBrokerTransientInput,
) -> bytes:
    payload: dict[str, Any] = {
        "protocol_version": MATRIX_BROKER_PROTOCOL_VERSION,
        "request_ref": invocation.request_ref,
        "request_fingerprint_ref": invocation.request_fingerprint_ref,
        "nonce": invocation.nonce,
        "issued_at_ms": int(invocation.issued_at.timestamp() * 1000),
        "deadline_ms": int(invocation.deadline.timestamp() * 1000),
        "operation": invocation.operation,
        "account_ref": invocation.account_ref,
        "homeserver_ref": invocation.homeserver_ref,
        "device_ref": invocation.device_ref,
        "room_ref": invocation.room_ref,
        "event_ref": invocation.event_ref,
        "transaction_ref": invocation.transaction_ref,
        "member_ref": invocation.member_ref,
        "space_ref": invocation.space_ref,
        "media_ref": invocation.media_ref,
        "quarantine_ref": invocation.quarantine_ref,
        "approval_ref": invocation.approval_ref,
        "lease_ref": invocation.lease_ref,
        "idempotency_ref": invocation.idempotency_ref,
        "adapter_ref": invocation.adapter_ref,
        "budget_ref": invocation.budget_ref,
        "readiness_ref": invocation.readiness_ref,
        "safe_disable_ref": invocation.safe_disable_ref,
        "kill_switch_ref": invocation.kill_switch_ref,
        "secret_kind": invocation.secret_kind,
        "homeserver_url": transient.homeserver_url,
        "username": transient.username,
        "password": transient.password,
        "room_id": transient.room_id,
        "event_id": transient.event_id,
        "transaction_id": transient.transaction_id,
        "body": transient.body,
        "formatted_body": transient.formatted_body,
        "mention_user_ids": (
            None
            if transient.mention_user_ids is None
            else list(transient.mention_user_ids)
        ),
        "relation_event_id": transient.relation_event_id,
        "reaction_key": transient.reaction_key,
        "typing_active": transient.typing_active,
        "member_id": transient.member_id,
        "space_id": transient.space_id,
        "room_name": transient.room_name,
        "desired_state": transient.desired_state,
        "prior_state": transient.prior_state,
        "media_uri": transient.media_uri,
        "media_type": transient.media_type,
        "media_b64": transient.media_b64,
    }
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    if not encoded or len(encoded) > MATRIX_BROKER_MAX_FRAME_BYTES:
        raise MatrixBrokerError("MATRIX_BROKER_REQUEST_OVERSIZE")
    return encoded


def _exchange(
    port: int,
    payload: bytes,
    *,
    auth_key: bytearray,
    timeout_seconds: float,
    cancel_requested: MatrixBrokerCancelCheck | None,
    progress_observer: MatrixBrokerProgressObserver | None,
) -> MatrixBrokerResponse:
    tag = hmac.new(auth_key, payload, hashlib.sha256).hexdigest()
    envelope = json.dumps(
        {
            "payload_b64": base64.b64encode(payload).decode("ascii"),
            "auth_tag": tag,
        },
        separators=(",", ":"),
    ).encode("ascii")
    if len(envelope) > MATRIX_BROKER_MAX_FRAME_BYTES:
        raise MatrixBrokerError("MATRIX_BROKER_ENVELOPE_OVERSIZE")
    if _cancel_requested(cancel_requested):
        raise MatrixBrokerError("MATRIX_BROKER_CANCELLED_BEFORE_START")
    deadline = time.monotonic() + timeout_seconds
    try:
        with socket.create_connection(
            ("127.0.0.1", port), timeout=timeout_seconds
        ) as connection:
            connection.settimeout(min(0.1, timeout_seconds))
            connection.sendall(len(envelope).to_bytes(4, "big") + envelope)
            _emit_progress(progress_observer, "request_sent")
            response_length = int.from_bytes(
                _recv_exact_cancellable(
                    connection,
                    4,
                    deadline=deadline,
                    cancel_requested=cancel_requested,
                ),
                "big",
            )
            if not (1 <= response_length <= MATRIX_BROKER_MAX_FRAME_BYTES):
                raise MatrixBrokerError("MATRIX_BROKER_RESPONSE_SIZE_INVALID")
            response_envelope_bytes = _recv_exact_cancellable(
                connection,
                response_length,
                deadline=deadline,
                cancel_requested=cancel_requested,
            )
            _emit_progress(progress_observer, "response_received")
    except (OSError, TimeoutError) as exc:
        raise MatrixBrokerError("MATRIX_BROKER_OUTCOME_UNCERTAIN") from exc
    try:
        response_envelope = _ResponseEnvelope.model_validate_json(
            response_envelope_bytes
        )
        response_payload = base64.b64decode(
            response_envelope.payload_b64, validate=True
        )
    except (ValueError, TypeError) as exc:
        raise MatrixBrokerError("MATRIX_BROKER_RESPONSE_ENVELOPE_INVALID") from exc
    expected_tag = hmac.new(auth_key, response_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_tag, response_envelope.auth_tag):
        raise MatrixBrokerError("MATRIX_BROKER_RESPONSE_AUTHENTICATION_FAILED")
    try:
        return MatrixBrokerResponse.model_validate_json(response_payload)
    except ValueError as exc:
        raise MatrixBrokerError("MATRIX_BROKER_RESPONSE_INVALID") from exc


def _validate_response_binding(
    response: MatrixBrokerResponse,
    invocation: MatrixBrokerInvocation,
) -> None:
    if (
        response.operation != invocation.operation
        or response.request_ref != invocation.request_ref
        or response.request_fingerprint_ref != invocation.request_fingerprint_ref
        or response.transaction_ref != invocation.transaction_ref
        or response.quarantine_ref != invocation.quarantine_ref
    ):
        raise MatrixBrokerError("MATRIX_BROKER_RESPONSE_BINDING_MISMATCH")


def _recv_exact_cancellable(
    connection: socket.socket,
    count: int,
    *,
    deadline: float,
    cancel_requested: MatrixBrokerCancelCheck | None,
) -> bytes:
    result = bytearray()
    while len(result) < count:
        if _cancel_requested(cancel_requested):
            raise MatrixBrokerError("MATRIX_BROKER_CANCELLED_OUTCOME_UNCERTAIN")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        connection.settimeout(min(0.1, remaining))
        try:
            chunk = connection.recv(count - len(result))
        except socket.timeout:
            continue
        if not chunk:
            raise MatrixBrokerError("MATRIX_BROKER_RESPONSE_TRUNCATED")
        result.extend(chunk)
    return bytes(result)


def _cancel_requested(callback: MatrixBrokerCancelCheck | None) -> bool:
    if callback is None:
        return False
    try:
        return callback() is True
    except Exception:
        return True


def _emit_progress(
    observer: MatrixBrokerProgressObserver | None,
    phase: str,
) -> None:
    if observer is None:
        return
    try:
        observer(phase)
    except Exception:
        # Progress is content-free observation only and never execution authority.
        return


def _read_line_bounded(fd: int, *, maximum: int, timeout_seconds: float) -> bytes:
    selector = selectors.DefaultSelector()
    result = bytearray()
    deadline = time.monotonic() + timeout_seconds
    try:
        os.set_blocking(fd, False)
        selector.register(fd, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MatrixBrokerError("MATRIX_BROKER_READINESS_TIMEOUT")
            if not selector.select(min(remaining, 0.1)):
                continue
            chunk = os.read(fd, min(1024, maximum + 1 - len(result)))
            if not chunk:
                raise MatrixBrokerError("MATRIX_BROKER_READINESS_TRUNCATED")
            result.extend(chunk)
            newline = result.find(b"\n")
            if newline >= 0:
                if newline != len(result) - 1:
                    raise MatrixBrokerError("MATRIX_BROKER_READINESS_TRAILING_DATA")
                return bytes(result[:newline])
            if len(result) > maximum:
                raise MatrixBrokerError("MATRIX_BROKER_READINESS_OVERSIZE")
    finally:
        selector.close()


def _write_all(fd: int, value: bytes | bytearray) -> None:
    offset = 0
    while offset < len(value):
        written = os.write(fd, value[offset:])
        if written <= 0:
            raise MatrixBrokerError("MATRIX_BROKER_INHERITED_FD_WRITE_FAILED")
        offset += written


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        process.wait(timeout=1)
        return

    def signal_process(value: signal.Signals) -> None:
        try:
            os.killpg(process.pid, value)
            return
        except OSError:
            pass
        try:
            process.send_signal(value)
        except OSError:
            pass

    signal_process(signal.SIGTERM)
    try:
        process.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    signal_process(signal.SIGKILL)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired as exc:
        raise MatrixBrokerError("MATRIX_BROKER_PROCESS_CLEANUP_FAILED") from exc


def _prepare_state_root(path: Path) -> tuple[int, int]:
    if path.resolve() != path:
        raise ValueError("MATRIX_BROKER_STATE_ROOT_CANONICAL_PATH_REQUIRED")
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path, 0o700)
    except OSError as exc:
        raise ValueError("MATRIX_BROKER_STATE_ROOT_UNAVAILABLE") from exc
    info = os.lstat(path)
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise ValueError("MATRIX_BROKER_STATE_ROOT_UNTRUSTED")
    return info.st_dev, info.st_ino


def _validate_state_root(
    path: Path,
    *,
    expected_identity: tuple[int, int],
) -> None:
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise MatrixBrokerError("MATRIX_BROKER_STATE_ROOT_UNAVAILABLE") from exc
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
        or (info.st_dev, info.st_ino) != expected_identity
    ):
        raise MatrixBrokerError("MATRIX_BROKER_STATE_ROOT_SUBSTITUTION_DENIED")


def _open_validated_binary(path: Path, expected_sha256: str) -> tuple[int, str]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError("MATRIX_BROKER_BINARY_UNAVAILABLE") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid not in {0, os.getuid()}
        or not (1 <= metadata.st_size <= MATRIX_BROKER_MAX_EXECUTABLE_BYTES)
    ):
        raise ValueError("MATRIX_BROKER_BINARY_REGULAR_FILE_REQUIRED")
    if metadata.st_mode & 0o022 or not metadata.st_mode & stat.S_IXUSR:
        raise ValueError("MATRIX_BROKER_BINARY_PERMISSIONS_INVALID")
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise ValueError("MATRIX_BROKER_BINARY_UNAVAILABLE") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
        ):
            raise ValueError("MATRIX_BROKER_BINARY_CHANGED")
        hasher = hashlib.sha256()
        while chunk := os.read(descriptor, 65_536):
            hasher.update(chunk)
        digest = hasher.hexdigest()
    except BaseException:
        os.close(descriptor)
        raise
    if digest != expected_sha256:
        os.close(descriptor)
        raise ValueError("MATRIX_BROKER_BINARY_HASH_MISMATCH")
    os.lseek(descriptor, 0, os.SEEK_SET)
    return descriptor, digest


def _validate_binary(path: Path, expected_sha256: str) -> None:
    descriptor, _digest = _open_validated_binary(path, expected_sha256)
    os.close(descriptor)


@contextmanager
def _staged_broker_binary(path: Path, expected_sha256: str) -> Iterator[Path]:
    descriptor, digest = _open_validated_binary(path, expected_sha256)
    try:
        with tempfile.TemporaryDirectory(
            prefix="uaa-matrix-rust-broker-",
            dir="/tmp",
        ) as temporary:
            os.chmod(temporary, 0o700)
            executable = Path(temporary) / "uaa-matrix-rust-broker"
            target_fd = os.open(
                executable,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o700,
            )
            copied = hashlib.sha256()
            try:
                while chunk := os.read(descriptor, 65_536):
                    copied.update(chunk)
                    _write_all(target_fd, chunk)
                os.fsync(target_fd)
            finally:
                os.close(target_fd)
            if copied.hexdigest() != digest:
                raise MatrixBrokerError("MATRIX_BROKER_STAGED_BINARY_MISMATCH")
            yield executable
    finally:
        os.close(descriptor)


__all__ = [
    "MATRIX_BROKER_ADAPTER_REF",
    "MATRIX_BROKER_PROTOCOL_VERSION",
    "MatrixBrokerClient",
    "MatrixBrokerConfig",
    "MatrixBrokerError",
    "MatrixBrokerInvocation",
    "MatrixBrokerResponse",
    "MatrixBrokerTransientInput",
]
