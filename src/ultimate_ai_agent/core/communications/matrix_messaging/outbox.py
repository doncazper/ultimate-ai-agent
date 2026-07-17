from __future__ import annotations

import hashlib
import json
import os
import stat
import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.communications.matrix_sync.cache import (
    MatrixCacheCryptoBackend,
    MatrixCacheKeyUnavailable,
)

from .constants import MATRIX_MESSAGING_OUTBOX_SCHEMA_REF, MatrixMessagingOperation
from .contracts import MatrixOutboxState, stable_matrix_messaging_ref


_OUTBOX_MAGIC = b"UAA-MATRIX-OUTBOX-V1\x00"
_MAX_OUTBOX_BYTES = 1024 * 1024
_OUTBOX_LOCK_NAME = ".matrix-outbox.lock"


class MatrixOutboxError(RuntimeError):
    pass


class MatrixOutboxRecord(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True
    )

    schema_ref: Literal["outbox-schema-ref:matrix:encrypted-v1"] = (
        MATRIX_MESSAGING_OUTBOX_SCHEMA_REF
    )
    outbox_ref: str
    generation_ref: str
    account_ref: str
    room_ref: str
    event_ref: str | None = None
    transaction_ref: str
    operation: MatrixMessagingOperation
    content_fingerprint_ref: str
    state: MatrixOutboxState
    created_at: datetime
    expires_at: datetime
    attempt_count: int = Field(default=0, ge=0, le=3)
    room_id: str = Field(repr=False, min_length=1, max_length=255)
    event_id: str | None = Field(default=None, repr=False, max_length=255)
    transaction_id: str = Field(repr=False, min_length=1, max_length=128)
    body: str | None = Field(default=None, repr=False, max_length=16 * 1024)
    formatted_body: str | None = Field(
        default=None, repr=False, max_length=24 * 1024
    )
    mention_user_ids: tuple[str, ...] = Field(
        default_factory=tuple, repr=False, max_length=32
    )
    reaction_key: str | None = Field(default=None, repr=False, max_length=64)
    failure_reason_ref: str | None = None
    remote_event_ref: str | None = None

    @model_validator(mode="after")
    def validate_record(self) -> MatrixOutboxRecord:
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("MATRIX_OUTBOX_TIMEZONE_REQUIRED")
        if not self.created_at < self.expires_at:
            raise ValueError("MATRIX_OUTBOX_TTL_INVALID")
        if (self.expires_at - self.created_at).total_seconds() > 7 * 24 * 60 * 60:
            raise ValueError("MATRIX_OUTBOX_TTL_EXCEEDED")
        if self.operation not in {
            MatrixMessagingOperation.send,
            MatrixMessagingOperation.reply,
            MatrixMessagingOperation.thread,
            MatrixMessagingOperation.reaction,
            MatrixMessagingOperation.edit,
            MatrixMessagingOperation.redaction,
        }:
            raise ValueError("MATRIX_OUTBOX_OPERATION_INVALID")
        event_scoped = self.operation != MatrixMessagingOperation.send
        if event_scoped != (self.event_ref is not None and self.event_id is not None):
            raise ValueError("MATRIX_OUTBOX_EVENT_SCOPE_INVALID")
        body_required = self.operation in {
            MatrixMessagingOperation.send,
            MatrixMessagingOperation.reply,
            MatrixMessagingOperation.thread,
            MatrixMessagingOperation.edit,
        }
        if body_required != (self.body is not None):
            raise ValueError("MATRIX_OUTBOX_BODY_SCOPE_INVALID")
        if (self.operation == MatrixMessagingOperation.reaction) != (
            self.reaction_key is not None
        ):
            raise ValueError("MATRIX_OUTBOX_REACTION_SCOPE_INVALID")
        expected = matrix_outbox_content_fingerprint_ref(
            operation=self.operation,
            room_id=self.room_id,
            event_id=self.event_id,
            transaction_id=self.transaction_id,
            body=self.body,
            formatted_body=self.formatted_body,
            mention_user_ids=self.mention_user_ids,
            reaction_key=self.reaction_key,
        )
        if expected != self.content_fingerprint_ref:
            raise ValueError("MATRIX_OUTBOX_CONTENT_FINGERPRINT_MISMATCH")
        if self.state != MatrixOutboxState.outcome_uncertain and self.failure_reason_ref:
            if self.state != MatrixOutboxState.failed:
                raise ValueError("MATRIX_OUTBOX_FAILURE_REASON_FORBIDDEN")
        if (self.state in {MatrixOutboxState.server_acknowledged, MatrixOutboxState.remote_echo}) != (
            self.remote_event_ref is not None
        ):
            raise ValueError("MATRIX_OUTBOX_REMOTE_EVENT_SCOPE_INVALID")
        return self


class MatrixEncryptedOutbox:
    def __init__(
        self,
        *,
        root: Path,
        crypto_backend: MatrixCacheCryptoBackend,
        key_item_ref: str,
        key_version_ref: str,
    ) -> None:
        if not root.is_absolute() or root == Path(root.anchor):
            raise ValueError("MATRIX_OUTBOX_ROOT_INVALID")
        self._root = root
        self._crypto_backend = crypto_backend
        self._key_item_ref = key_item_ref
        self._key_version_ref = key_version_ref
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise ValueError("MATRIX_OUTBOX_ROOT_INVALID")
        os.chmod(root, 0o700)
        info = root.stat()
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("MATRIX_OUTBOX_ROOT_PERMISSIONS_INVALID")
        self._root_identity = (info.st_dev, info.st_ino)
        self.binding_ref = stable_matrix_messaging_ref(
            "outbox-binding-ref:matrix",
            {
                "backend_ref": crypto_backend.backend_ref,
                "key_item_ref": key_item_ref,
                "key_version_ref": key_version_ref,
                "root_identity_ref": hashlib.sha256(
                    f"{info.st_dev}:{info.st_ino}".encode()
                ).hexdigest(),
            },
        )

    def create_key(self) -> str:
        return self._crypto_backend.create(
            key_item_ref=self._key_item_ref,
            key_version_ref=self._key_version_ref,
        )

    def probe_key(self) -> str:
        return self._crypto_backend.probe(
            key_item_ref=self._key_item_ref,
            key_version_ref=self._key_version_ref,
        )

    def write(self, record: MatrixOutboxRecord) -> str:
        self._validate_root()
        with self._locked_root(exclusive=True) as root_fd:
            return self._write_locked(record, root_fd=root_fd, replace_existing=False)

    def _write_locked(
        self,
        record: MatrixOutboxRecord,
        *,
        root_fd: int,
        replace_existing: bool,
    ) -> str:
        plaintext = record.model_dump_json().encode("utf-8")
        try:
            ciphertext = self._crypto_backend.encrypt(
                key_item_ref=self._key_item_ref,
                key_version_ref=self._key_version_ref,
                plaintext=plaintext,
                aad=self._aad(record),
            )
        except MatrixCacheKeyUnavailable:
            raise
        except Exception as exc:
            raise MatrixOutboxError("MATRIX_OUTBOX_ENCRYPTION_FAILED") from exc
        container = _OUTBOX_MAGIC + ciphertext
        if len(container) > _MAX_OUTBOX_BYTES:
            raise MatrixOutboxError("MATRIX_OUTBOX_SIZE_LIMIT_EXCEEDED")
        name = self._name(record.outbox_ref)
        if not replace_existing:
            try:
                existing = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                if stat.S_ISREG(existing.st_mode):
                    raise MatrixOutboxError("MATRIX_OUTBOX_RECORD_ALREADY_EXISTS")
                raise MatrixOutboxError("MATRIX_OUTBOX_FILE_INVALID")
        temporary = f".{name}.{os.getpid()}.tmp"
        descriptor = -1
        try:
            descriptor = os.open(
                temporary,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=root_fd,
            )
            _write_all(descriptor, container)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary, name, src_dir_fd=root_fd, dst_dir_fd=root_fd)
            os.fsync(root_fd)
        except OSError as exc:
            try:
                os.unlink(temporary, dir_fd=root_fd)
            except OSError:
                pass
            raise MatrixOutboxError("MATRIX_OUTBOX_ATOMIC_WRITE_FAILED") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        return stable_matrix_messaging_ref(
            "receipt-ref:matrix-outbox:write",
            {
                "outbox_ref": record.outbox_ref,
                "generation_ref": record.generation_ref,
                "ciphertext_sha256": hashlib.sha256(container).hexdigest(),
            },
        )

    def read(
        self,
        *,
        outbox_ref: str,
        account_ref: str,
        room_ref: str,
    ) -> MatrixOutboxRecord:
        self._validate_root()
        with self._locked_root(exclusive=False) as root_fd:
            return self._read_locked(
                outbox_ref=outbox_ref,
                account_ref=account_ref,
                room_ref=room_ref,
                root_fd=root_fd,
            )

    def _read_locked(
        self,
        *,
        outbox_ref: str,
        account_ref: str,
        room_ref: str,
        root_fd: int,
    ) -> MatrixOutboxRecord:
        try:
            descriptor = os.open(
                self._name(outbox_ref),
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=root_fd,
            )
            try:
                info = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.geteuid()
                    or info.st_nlink != 1
                    or info.st_size > _MAX_OUTBOX_BYTES
                ):
                    raise MatrixOutboxError("MATRIX_OUTBOX_FILE_INVALID")
                container = _read_bounded(descriptor, _MAX_OUTBOX_BYTES)
            finally:
                os.close(descriptor)
        except FileNotFoundError as exc:
            raise MatrixOutboxError("MATRIX_OUTBOX_NOT_FOUND") from exc
        if not container.startswith(_OUTBOX_MAGIC):
            raise MatrixOutboxError("MATRIX_OUTBOX_CONTAINER_INVALID")
        aad = _aad_values(
            account_ref=account_ref,
            room_ref=room_ref,
            outbox_ref=outbox_ref,
            key_version_ref=self._key_version_ref,
        )
        try:
            plaintext = self._crypto_backend.decrypt(
                key_item_ref=self._key_item_ref,
                key_version_ref=self._key_version_ref,
                ciphertext=container[len(_OUTBOX_MAGIC) :],
                aad=aad,
            )
            record = MatrixOutboxRecord.model_validate_json(plaintext)
        except MatrixCacheKeyUnavailable:
            raise
        except Exception as exc:
            raise MatrixOutboxError("MATRIX_OUTBOX_DECRYPTION_FAILED") from exc
        if (
            record.outbox_ref != outbox_ref
            or record.account_ref != account_ref
            or record.room_ref != room_ref
        ):
            raise MatrixOutboxError("MATRIX_OUTBOX_EXACT_SCOPE_MISMATCH")
        if datetime.now(UTC) >= record.expires_at:
            raise MatrixOutboxError("MATRIX_OUTBOX_RECORD_EXPIRED")
        return record

    def transition(
        self,
        *,
        record: MatrixOutboxRecord,
        expected_state: MatrixOutboxState,
        next_state: MatrixOutboxState,
        next_generation_ref: str,
        failure_reason_ref: str | None = None,
        remote_event_ref: str | None = None,
    ) -> tuple[MatrixOutboxRecord, str]:
        with self._locked_root(exclusive=True) as root_fd:
            current = self._read_locked(
                outbox_ref=record.outbox_ref,
                account_ref=record.account_ref,
                room_ref=record.room_ref,
                root_fd=root_fd,
            )
            if current != record or record.state != expected_state:
                raise MatrixOutboxError("MATRIX_OUTBOX_STATE_CONFLICT")
            if next_state not in _ALLOWED_TRANSITIONS[expected_state]:
                raise MatrixOutboxError("MATRIX_OUTBOX_TRANSITION_DENIED")
            attempts = record.attempt_count + (
                1 if next_state == MatrixOutboxState.sending else 0
            )
            next_remote_event_ref = remote_event_ref
            if (
                next_state == MatrixOutboxState.remote_echo
                and expected_state == MatrixOutboxState.server_acknowledged
                and next_remote_event_ref is None
            ):
                next_remote_event_ref = record.remote_event_ref
            updated = record.model_copy(
                update={
                    "generation_ref": next_generation_ref,
                    "state": next_state,
                    "attempt_count": attempts,
                    "failure_reason_ref": failure_reason_ref,
                    "remote_event_ref": next_remote_event_ref,
                }
            )
            updated = MatrixOutboxRecord.model_validate(
                updated.model_dump(mode="python")
            )
            receipt_ref = self._write_locked(
                updated,
                root_fd=root_fd,
                replace_existing=True,
            )
            return updated, receipt_ref

    def discard(self, *, outbox_ref: str) -> str:
        self._validate_root()
        with self._locked_root(exclusive=True) as root_fd:
            try:
                os.unlink(self._name(outbox_ref), dir_fd=root_fd)
            except FileNotFoundError:
                pass
            os.fsync(root_fd)
        return stable_matrix_messaging_ref(
            "receipt-ref:matrix-outbox:discard", {"outbox_ref": outbox_ref}
        )

    def plaintext_absent(self, markers: tuple[str, ...]) -> bool:
        self._validate_root()
        encoded = tuple(value.encode("utf-8") for value in markers if value)
        with self._locked_root(exclusive=False) as root_fd:
            for name in os.listdir(root_fd):
                if not name.endswith(".uaamxoutbox"):
                    continue
                descriptor = os.open(
                    name,
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_CLOEXEC", 0),
                    dir_fd=root_fd,
                )
                try:
                    info = os.fstat(descriptor)
                    if (
                        not stat.S_ISREG(info.st_mode)
                        or info.st_uid != os.geteuid()
                        or info.st_nlink != 1
                        or info.st_size > _MAX_OUTBOX_BYTES
                    ):
                        raise MatrixOutboxError("MATRIX_OUTBOX_FILE_INVALID")
                    payload = _read_bounded(descriptor, _MAX_OUTBOX_BYTES)
                finally:
                    os.close(descriptor)
                if any(marker in payload for marker in encoded):
                    return False
        return True

    def _aad(self, record: MatrixOutboxRecord) -> bytes:
        return _aad_values(
            account_ref=record.account_ref,
            room_ref=record.room_ref,
            outbox_ref=record.outbox_ref,
            key_version_ref=self._key_version_ref,
        )

    def _name(self, outbox_ref: str) -> str:
        return f"{hashlib.sha256(outbox_ref.encode()).hexdigest()}.uaamxoutbox"

    def _validate_root(self) -> None:
        info = os.lstat(self._root)
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._root_identity
        ):
            raise MatrixOutboxError("MATRIX_OUTBOX_ROOT_SUBSTITUTION_DENIED")

    def _open_root(self) -> int:
        descriptor = os.open(
            self._root,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) != self._root_identity:
            os.close(descriptor)
            raise MatrixOutboxError("MATRIX_OUTBOX_ROOT_SUBSTITUTION_DENIED")
        return descriptor

    @contextmanager
    def _locked_root(self, *, exclusive: bool) -> Iterator[int]:
        root_fd = self._open_root()
        lock_fd = -1
        try:
            lock_fd = os.open(
                _OUTBOX_LOCK_NAME,
                os.O_RDWR
                | os.O_CREAT
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=root_fd,
            )
            info = os.fstat(lock_fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_nlink != 1
                or info.st_mode & 0o077
            ):
                raise MatrixOutboxError("MATRIX_OUTBOX_LOCK_INVALID")
            fcntl.flock(lock_fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            yield root_fd
        finally:
            if lock_fd >= 0:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                finally:
                    os.close(lock_fd)
            os.close(root_fd)


_ALLOWED_TRANSITIONS = {
    MatrixOutboxState.draft: {MatrixOutboxState.queued, MatrixOutboxState.discarded},
    MatrixOutboxState.queued: {MatrixOutboxState.sending, MatrixOutboxState.discarded},
    MatrixOutboxState.sending: {
        MatrixOutboxState.server_acknowledged,
        MatrixOutboxState.failed,
        MatrixOutboxState.outcome_uncertain,
    },
    MatrixOutboxState.failed: {MatrixOutboxState.queued, MatrixOutboxState.discarded},
    MatrixOutboxState.outcome_uncertain: {
        MatrixOutboxState.server_acknowledged,
        MatrixOutboxState.remote_echo,
        MatrixOutboxState.discarded,
    },
    MatrixOutboxState.server_acknowledged: {MatrixOutboxState.remote_echo},
    MatrixOutboxState.remote_echo: set(),
    MatrixOutboxState.discarded: set(),
}


def matrix_outbox_content_fingerprint_ref(
    *,
    operation: MatrixMessagingOperation | str,
    room_id: str,
    event_id: str | None,
    transaction_id: str,
    body: str | None,
    formatted_body: str | None,
    mention_user_ids: tuple[str, ...],
    reaction_key: str | None,
) -> str:
    return stable_matrix_messaging_ref(
        "content-fingerprint-ref:matrix-message",
        {
            "operation": MatrixMessagingOperation(operation).value,
            "room_id": room_id,
            "event_id": event_id,
            "transaction_id": transaction_id,
            "body": body,
            "formatted_body": formatted_body,
            "mention_user_ids": list(mention_user_ids),
            "reaction_key": reaction_key,
        },
    )


def _aad_values(
    *,
    account_ref: str,
    room_ref: str,
    outbox_ref: str,
    key_version_ref: str,
) -> bytes:
    return json.dumps(
        {
            "schema_ref": MATRIX_MESSAGING_OUTBOX_SCHEMA_REF,
            "account_ref": account_ref,
            "room_ref": room_ref,
            "outbox_ref": outbox_ref,
            "key_version_ref": key_version_ref,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write_all(descriptor: int, value: bytes) -> None:
    offset = 0
    while offset < len(value):
        written = os.write(descriptor, value[offset:])
        if written <= 0:
            raise MatrixOutboxError("MATRIX_OUTBOX_WRITE_FAILED")
        offset += written


def _read_bounded(descriptor: int, maximum: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(descriptor, min(65_536, maximum + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > maximum:
            raise MatrixOutboxError("MATRIX_OUTBOX_SIZE_LIMIT_EXCEEDED")
    return b"".join(chunks)


__all__ = [
    "MatrixEncryptedOutbox",
    "MatrixOutboxError",
    "MatrixOutboxRecord",
    "matrix_outbox_content_fingerprint_ref",
]
