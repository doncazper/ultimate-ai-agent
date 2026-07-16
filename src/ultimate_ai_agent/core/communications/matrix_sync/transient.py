from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from ultimate_ai_agent.core.time import utc_now

from .contracts import stable_matrix_sync_ref
from .implementation import matrix_sync_implementation_ref
from .normalization import MatrixPrivateSyncBatch


class MatrixTransientBatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Entry:
    batch: MatrixPrivateSyncBatch
    expires_at: datetime
    request_fingerprint_ref: str


class MatrixTransientBatchRegistry:
    __slots__ = (
        "_entries",
        "_lock",
        "_maximum_entries",
        "_owner_ref",
        "_sealed",
        "_ttl",
    )

    def __init__(self, *, maximum_entries: int = 4, ttl_seconds: int = 30) -> None:
        object.__setattr__(self, "_maximum_entries", max(1, min(maximum_entries, 16)))
        object.__setattr__(
            self,
            "_ttl",
            timedelta(seconds=max(1, min(ttl_seconds, 60))),
        )
        object.__setattr__(
            self,
            "_owner_ref",
            stable_matrix_sync_ref(
                "transient-registry-owner-ref:matrix-sync",
                {"nonce": secrets.token_hex(32)},
            ),
        )
        object.__setattr__(self, "_entries", {})
        object.__setattr__(self, "_lock", threading.RLock())
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("MATRIX_SYNC_TRANSIENT_REGISTRY_IMMUTABLE")
        object.__setattr__(self, name, value)

    @property
    def binding_ref(self) -> str:
        configuration_binding_ref = stable_matrix_sync_ref(
            "transient-registry-binding-ref:matrix-sync",
            {
                "maximum_entries": self._maximum_entries,
                "ttl_seconds": int(self._ttl.total_seconds()),
            },
        )
        return stable_matrix_sync_ref(
            "transient-registry-owner-binding-ref:matrix-sync",
            {
                "configuration_binding_ref": configuration_binding_ref,
                "owner_ref": self._owner_ref,
                "implementation_refs": [
                    matrix_sync_implementation_ref(type(self).clear),
                    matrix_sync_implementation_ref(type(self).consume),
                    matrix_sync_implementation_ref(type(self).discard),
                    matrix_sync_implementation_ref(type(self).register),
                ],
            },
        )

    def register(
        self,
        batch: MatrixPrivateSyncBatch,
        *,
        request_fingerprint_ref: str,
        now: datetime | None = None,
    ) -> str:
        current = now or utc_now()
        with self._lock:
            self._discard_expired(current)
            if len(self._entries) >= self._maximum_entries:
                raise MatrixTransientBatchError(
                    "MATRIX_TRANSIENT_BATCH_CAPACITY_EXCEEDED"
                )
            batch_ref = stable_matrix_sync_ref(
                "transient-batch-ref:matrix-sync",
                {
                    "request_fingerprint_ref": request_fingerprint_ref,
                    "next_batch_ref": batch.next_batch_ref,
                    "event_refs": [event.event_ref for event in batch.events],
                },
            )
            self._entries[batch_ref] = _Entry(
                batch=batch,
                expires_at=current + self._ttl,
                request_fingerprint_ref=request_fingerprint_ref,
            )
            return batch_ref

    def consume(
        self,
        batch_ref: str,
        *,
        request_fingerprint_ref: str,
        now: datetime | None = None,
    ) -> MatrixPrivateSyncBatch:
        current = now or utc_now()
        with self._lock:
            entry = self._entries.get(batch_ref)
            if entry is None:
                raise MatrixTransientBatchError("MATRIX_TRANSIENT_BATCH_EXPIRED")
            if current >= entry.expires_at:
                self._entries.pop(batch_ref, None)
                raise MatrixTransientBatchError("MATRIX_TRANSIENT_BATCH_EXPIRED")
            if entry.request_fingerprint_ref != request_fingerprint_ref:
                raise MatrixTransientBatchError("MATRIX_TRANSIENT_BATCH_SCOPE_MISMATCH")
            self._entries.pop(batch_ref)
            return entry.batch

    def discard(
        self,
        batch_ref: str,
        *,
        request_fingerprint_ref: str,
    ) -> None:
        with self._lock:
            entry = self._entries.get(batch_ref)
            if entry is None:
                return
            if entry.request_fingerprint_ref != request_fingerprint_ref:
                raise MatrixTransientBatchError("MATRIX_TRANSIENT_BATCH_SCOPE_MISMATCH")
            self._entries.pop(batch_ref)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _discard_expired(self, now: datetime) -> None:
        for batch_ref, entry in tuple(self._entries.items()):
            if now >= entry.expires_at:
                self._entries.pop(batch_ref, None)


class MatrixCredentialWriter:
    __slots__ = ()

    backend_ref = "credential-backend-ref:matrix:unavailable"

    @property
    def owner_ref(self) -> str:
        return "credential-writer-owner-ref:matrix:unavailable"

    @property
    def binding_ref(self) -> str:
        return stable_matrix_sync_ref(
            "credential-writer-binding-ref:matrix-sync",
            {
                "backend_ref": self.backend_ref,
                "owner_ref": self.owner_ref,
                "implementation_ref": matrix_sync_implementation_ref(
                    type(self).write_once
                ),
            },
        )

    def write_once(
        self,
        fd: int,
        *,
        credential_item_ref: str,
        credential_version_ref: str,
        request_fingerprint_ref: str,
    ) -> None:
        del fd, credential_item_ref, credential_version_ref, request_fingerprint_ref
        raise MatrixTransientBatchError("MATRIX_SYNC_CREDENTIAL_BROKER_UNAVAILABLE")


class InMemoryMatrixCredentialWriter(MatrixCredentialWriter):
    """Test-only writer that proves FD handoff without a token field or environment."""

    __slots__ = (
        "_credential",
        "_credential_commitment",
        "_credential_commitment_key",
        "_owner_ref",
        "_sealed",
    )

    backend_ref = "credential-backend-ref:matrix:in-memory-test-only"

    def __init__(self, credential: bytes) -> None:
        if not credential or len(credential) > 8192:
            raise ValueError("MATRIX_SYNC_TEST_CREDENTIAL_INVALID")
        commitment_key = secrets.token_bytes(32)
        object.__setattr__(self, "_credential", credential)
        object.__setattr__(self, "_credential_commitment_key", commitment_key)
        object.__setattr__(
            self,
            "_credential_commitment",
            hmac.digest(commitment_key, credential, hashlib.sha256),
        )
        object.__setattr__(
            self,
            "_owner_ref",
            stable_matrix_sync_ref(
                "credential-writer-owner-ref:matrix-sync:test-only",
                {"nonce": secrets.token_hex(32)},
            ),
        )
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("MATRIX_SYNC_CREDENTIAL_WRITER_IMMUTABLE")
        object.__setattr__(self, name, value)

    @property
    def owner_ref(self) -> str:
        return self._owner_ref

    def write_once(
        self,
        fd: int,
        *,
        credential_item_ref: str,
        credential_version_ref: str,
        request_fingerprint_ref: str,
    ) -> None:
        del credential_item_ref, credential_version_ref, request_fingerprint_ref
        if not hmac.compare_digest(
            self._credential_commitment,
            hmac.digest(
                self._credential_commitment_key,
                self._credential,
                hashlib.sha256,
            ),
        ):
            raise MatrixTransientBatchError(
                "MATRIX_SYNC_CREDENTIAL_WRITER_BINDING_CHANGED"
            )
        view = memoryview(self._credential)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise MatrixTransientBatchError("MATRIX_SYNC_CREDENTIAL_HANDOFF_FAILED")
            view = view[written:]
