from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from ultimate_ai_agent.core.time import utc_now

from .contracts import stable_matrix_sync_ref
from .normalization import MatrixPrivateSyncBatch


class MatrixTransientBatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Entry:
    batch: MatrixPrivateSyncBatch
    expires_at: datetime
    request_fingerprint_ref: str


class MatrixTransientBatchRegistry:
    def __init__(self, *, maximum_entries: int = 4, ttl_seconds: int = 30) -> None:
        self._maximum_entries = max(1, min(maximum_entries, 16))
        self._ttl = timedelta(seconds=max(1, min(ttl_seconds, 60)))
        self._entries: dict[str, _Entry] = {}
        self._lock = threading.RLock()

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
    backend_ref = "credential-backend-ref:matrix:unavailable"

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

    backend_ref = "credential-backend-ref:matrix:in-memory-test-only"

    def __init__(self, credential: bytes) -> None:
        if not credential or len(credential) > 8192:
            raise ValueError("MATRIX_SYNC_TEST_CREDENTIAL_INVALID")
        self._credential = credential

    def write_once(
        self,
        fd: int,
        *,
        credential_item_ref: str,
        credential_version_ref: str,
        request_fingerprint_ref: str,
    ) -> None:
        del credential_item_ref, credential_version_ref, request_fingerprint_ref
        view = memoryview(self._credential)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise MatrixTransientBatchError("MATRIX_SYNC_CREDENTIAL_HANDOFF_FAILED")
            view = view[written:]
