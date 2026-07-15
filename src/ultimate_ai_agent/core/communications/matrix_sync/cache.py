from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .constants import MATRIX_SYNC_CACHE_SCHEMA_REF, MATRIX_SYNC_MAX_CACHE_BYTES
from .contracts import MatrixSyncFreshness, stable_matrix_sync_ref
from .normalization import (
    MatrixNormalizedEventKind,
    MatrixPrivateEvent,
    MatrixPrivateRoom,
    MatrixPrivateSyncBatch,
)


_CONTAINER_MAGIC = b"UAA-MATRIX-CACHE-V1\x00"
_NONCE_BYTES = 12


class MatrixProtectedCacheError(RuntimeError):
    pass


class MatrixCacheKeyUnavailable(MatrixProtectedCacheError):
    pass


class MatrixCacheCryptoBackend(Protocol):
    backend_ref: str

    def create(self, *, key_item_ref: str, key_version_ref: str) -> str: ...
    def probe(self, *, key_item_ref: str, key_version_ref: str) -> str: ...
    def encrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        plaintext: bytes,
        aad: bytes,
    ) -> bytes: ...
    def decrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        ciphertext: bytes,
        aad: bytes,
    ) -> bytes: ...
    def delete(self, *, key_item_ref: str, key_version_ref: str) -> str: ...


class InMemoryMatrixCacheCryptoBackend:
    """Test-only key backend. It never represents macOS runtime readiness."""

    backend_ref = "cache-key-backend-ref:matrix:in-memory-test-only"

    def __init__(self) -> None:
        self._keys: dict[tuple[str, str], bytes] = {}
        self.locked = False

    def create(self, *, key_item_ref: str, key_version_ref: str) -> str:
        if self.locked:
            raise MatrixCacheKeyUnavailable("MATRIX_CACHE_KEY_BACKEND_LOCKED")
        self._keys.setdefault((key_item_ref, key_version_ref), secrets.token_bytes(32))
        return stable_matrix_sync_ref(
            "cache-key-receipt-ref:matrix:create",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )

    def _resolve(self, *, key_item_ref: str, key_version_ref: str) -> bytes:
        if self.locked:
            raise MatrixCacheKeyUnavailable("MATRIX_CACHE_KEY_BACKEND_LOCKED")
        try:
            return self._keys[(key_item_ref, key_version_ref)]
        except KeyError as exc:
            raise MatrixCacheKeyUnavailable("MATRIX_CACHE_KEY_NOT_FOUND") from exc

    def probe(self, *, key_item_ref: str, key_version_ref: str) -> str:
        self._resolve(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return stable_matrix_sync_ref(
            "cache-key-receipt-ref:matrix:probe",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )

    def encrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        plaintext: bytes,
        aad: bytes,
    ) -> bytes:
        key = self._resolve(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        nonce = secrets.token_bytes(_NONCE_BYTES)
        return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)

    def decrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        ciphertext: bytes,
        aad: bytes,
    ) -> bytes:
        if len(ciphertext) <= _NONCE_BYTES:
            raise MatrixProtectedCacheError("MATRIX_CACHE_CONTAINER_INVALID")
        key = self._resolve(key_item_ref=key_item_ref, key_version_ref=key_version_ref)
        return AESGCM(key).decrypt(
            ciphertext[:_NONCE_BYTES], ciphertext[_NONCE_BYTES:], aad
        )

    def delete(self, *, key_item_ref: str, key_version_ref: str) -> str:
        if self.locked:
            raise MatrixCacheKeyUnavailable("MATRIX_CACHE_KEY_BACKEND_LOCKED")
        self._keys.pop((key_item_ref, key_version_ref), None)
        return stable_matrix_sync_ref(
            "cache-key-receipt-ref:matrix:delete",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )


class MatrixProtectedCacheState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_ref: str = MATRIX_SYNC_CACHE_SCHEMA_REF
    account_ref: str
    cache_ref: str
    generation_ref: str
    key_version_ref: str
    pseudonymization_salt_base64url: str = Field(..., repr=False)
    next_batch_token: str | None = Field(default=None, max_length=2048, repr=False)
    next_batch_ref: str
    freshness: MatrixSyncFreshness
    rooms: tuple[MatrixPrivateRoom, ...] = ()
    events: tuple[MatrixPrivateEvent, ...] = ()

    @model_validator(mode="after")
    def validate_state(self) -> "MatrixProtectedCacheState":
        if self.schema_ref != MATRIX_SYNC_CACHE_SCHEMA_REF:
            raise ValueError("MATRIX_CACHE_SCHEMA_UNSUPPORTED")
        try:
            salt = _decode_base64url(self.pseudonymization_salt_base64url)
        except ValueError as exc:
            raise ValueError("MATRIX_CACHE_SALT_INVALID") from exc
        if len(salt) != 32:
            raise ValueError("MATRIX_CACHE_SALT_INVALID")
        event_refs = {event.event_ref for event in self.events}
        if any(not set(room.event_refs) <= event_refs for room in self.rooms):
            raise ValueError("MATRIX_CACHE_ROOM_EVENT_REF_INVALID")
        return self

    @property
    def pseudonymization_salt(self) -> bytes:
        return _decode_base64url(self.pseudonymization_salt_base64url)

    @classmethod
    def empty(
        cls,
        *,
        account_ref: str,
        cache_ref: str,
        generation_ref: str,
        key_version_ref: str,
    ) -> "MatrixProtectedCacheState":
        return cls(
            account_ref=account_ref,
            cache_ref=cache_ref,
            generation_ref=generation_ref,
            key_version_ref=key_version_ref,
            pseudonymization_salt_base64url=_encode_base64url(secrets.token_bytes(32)),
            next_batch_ref="sync-cursor-ref:matrix:initial",
            freshness=MatrixSyncFreshness.unknown,
        )

    def apply_batch(
        self,
        batch: MatrixPrivateSyncBatch,
        *,
        next_generation_ref: str,
    ) -> "MatrixProtectedCacheState":
        if batch.account_ref != self.account_ref:
            raise MatrixProtectedCacheError("MATRIX_CACHE_ACCOUNT_MISMATCH")
        events = {event.event_ref: event for event in self.events}
        incoming_events = {event.event_ref: event for event in batch.events}
        tombstone_rooms: dict[str, str] = {}
        for event in (*self.events, *batch.events):
            if (
                event.event_kind == MatrixNormalizedEventKind.redaction
                and event.relation_event_ref is not None
            ):
                existing_room = tombstone_rooms.get(event.relation_event_ref)
                if existing_room is not None and existing_room != event.room_ref:
                    raise MatrixProtectedCacheError(
                        "MATRIX_CACHE_REDACTION_SCOPE_CONFLICT"
                    )
                tombstone_rooms[event.relation_event_ref] = event.room_ref
        for target_ref, redaction_room_ref in tombstone_rooms.items():
            target = incoming_events.get(target_ref) or events.get(target_ref)
            if target is not None and target.room_ref != redaction_room_ref:
                raise MatrixProtectedCacheError(
                    "MATRIX_CACHE_CROSS_ROOM_REDACTION_DENIED"
                )
        for event in batch.events:
            existing = events.get(event.event_ref)
            if existing is not None and existing != event:
                if event.event_ref not in tombstone_rooms:
                    raise MatrixProtectedCacheError(
                        "MATRIX_CACHE_EVENT_REPLAY_CONFLICT"
                    )
                existing_identity = (
                    existing.event_ref,
                    existing.room_ref,
                    existing.sender_ref,
                    existing.origin_server_ts,
                )
                incoming_identity = (
                    event.event_ref,
                    event.room_ref,
                    event.sender_ref,
                    event.origin_server_ts,
                )
                if existing_identity != incoming_identity:
                    raise MatrixProtectedCacheError(
                        "MATRIX_CACHE_REDACTED_EVENT_IDENTITY_CONFLICT"
                    )
                continue
            events[event.event_ref] = (
                event.model_copy(update={"body": None, "redacted": True})
                if event.event_ref in tombstone_rooms
                else event
            )
        for target_ref in tombstone_rooms:
            target = events.get(target_ref)
            if target is not None:
                events[target_ref] = target.model_copy(
                    update={"body": None, "redacted": True}
                )
        rooms = {room.room_ref: room for room in self.rooms}
        for room in batch.rooms:
            previous = rooms.get(room.room_ref)
            combined_refs = tuple(
                dict.fromkeys(
                    [*(previous.event_refs if previous else ()), *room.event_refs]
                )
            )
            rooms[room.room_ref] = room.model_copy(update={"event_refs": combined_refs})
        return self.model_copy(
            update={
                "generation_ref": next_generation_ref,
                "next_batch_token": batch.next_batch_token,
                "next_batch_ref": batch.next_batch_ref,
                "freshness": MatrixSyncFreshness.current,
                "rooms": tuple(sorted(rooms.values(), key=lambda item: item.room_ref)),
                "events": tuple(
                    sorted(
                        events.values(),
                        key=lambda item: (item.origin_server_ts, item.event_ref),
                    )
                ),
            }
        )


@dataclass(frozen=True)
class MatrixCacheWriteResult:
    cache_ref: str
    generation_ref: str
    ciphertext_fingerprint_ref: str
    byte_count: int
    receipt_ref: str


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_base64url(value: str) -> bytes:
    if not value or any(
        char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        for char in value
    ):
        raise ValueError("BASE64URL_INVALID")
    padding = "=" * ((4 - len(value) % 4) % 4)
    decoded = base64.urlsafe_b64decode(value + padding)
    if _encode_base64url(decoded) != value:
        raise ValueError("BASE64URL_NON_CANONICAL")
    return decoded


def _aad(*, account_ref: str, cache_ref: str, key_version_ref: str) -> bytes:
    return json.dumps(
        {
            "schema_ref": MATRIX_SYNC_CACHE_SCHEMA_REF,
            "account_ref": account_ref,
            "cache_ref": cache_ref,
            "key_version_ref": key_version_ref,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class MatrixProtectedCache:
    def __init__(self, *, root: Path, crypto_backend: MatrixCacheCryptoBackend) -> None:
        self._root = root
        self._crypto_backend = crypto_backend
        self._root_identity = self._validate_root()

    def _validate_root(self) -> tuple[int, int]:
        if not self._root.is_absolute():
            raise ValueError("MATRIX_CACHE_ROOT_ABSOLUTE_REQUIRED")
        if self._root == Path(self._root.anchor):
            raise ValueError("MATRIX_CACHE_ROOT_UNSAFE")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(self._root.anchor, flags)
        try:
            for component in self._root.parts[1:]:
                if component in {"", ".", ".."}:
                    raise ValueError("MATRIX_CACHE_ROOT_UNSAFE")
                try:
                    next_descriptor = os.open(component, flags, dir_fd=descriptor)
                except FileNotFoundError:
                    try:
                        os.mkdir(component, mode=0o700, dir_fd=descriptor)
                    except FileExistsError:
                        pass
                    next_descriptor = os.open(component, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
            info = os.fstat(descriptor)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError("MATRIX_CACHE_ROOT_UNSAFE")
            if info.st_uid != os.geteuid():
                raise ValueError("MATRIX_CACHE_ROOT_OWNER_INVALID")
            if info.st_mode & 0o077:
                os.fchmod(descriptor, 0o700)
                info = os.fstat(descriptor)
            return (info.st_dev, info.st_ino)
        except OSError as exc:
            raise ValueError("MATRIX_CACHE_ROOT_UNSAFE") from exc
        finally:
            os.close(descriptor)

    def _verify_root_identity(self, info: os.stat_result) -> None:
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._root_identity
        ):
            raise MatrixProtectedCacheError("MATRIX_CACHE_ROOT_SUBSTITUTION_DENIED")

    def _open_root_fd(self) -> int:
        try:
            self._verify_root_identity(os.lstat(self._root))
            flags = (
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
            )
            descriptor = os.open(self._root, flags)
        except MatrixProtectedCacheError:
            raise
        except OSError as exc:
            raise MatrixProtectedCacheError(
                "MATRIX_CACHE_ROOT_SUBSTITUTION_DENIED"
            ) from exc
        try:
            self._verify_root_identity(os.fstat(descriptor))
            self._verify_root_identity(os.lstat(self._root))
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    @staticmethod
    def _validate_file_descriptor(descriptor: int) -> os.stat_result:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.geteuid()
        ):
            raise MatrixProtectedCacheError("MATRIX_CACHE_PATH_SUBSTITUTION_DENIED")
        if info.st_size > MATRIX_SYNC_MAX_CACHE_BYTES:
            raise MatrixProtectedCacheError("MATRIX_CACHE_SIZE_LIMIT_EXCEEDED")
        return info

    def _cache_name(self, cache_ref: str) -> str:
        digest = hashlib.sha256(cache_ref.encode("utf-8")).hexdigest()
        return f"{digest}.uaamxcache"

    def _path(self, cache_ref: str) -> Path:
        return self._root / self._cache_name(cache_ref)

    def _open_cache_fd_if_present(self, *, root_fd: int, cache_name: str) -> int | None:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            descriptor = os.open(cache_name, flags, dir_fd=root_fd)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise MatrixProtectedCacheError(
                "MATRIX_CACHE_PATH_SUBSTITUTION_DENIED"
            ) from exc
        try:
            self._validate_file_descriptor(descriptor)
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    def _open_cache_fd(self, *, root_fd: int, cache_name: str) -> int:
        descriptor = self._open_cache_fd_if_present(
            root_fd=root_fd, cache_name=cache_name
        )
        if descriptor is None:
            raise MatrixProtectedCacheError("MATRIX_CACHE_NOT_FOUND")
        return descriptor

    def read(
        self,
        *,
        account_ref: str,
        cache_ref: str,
        key_item_ref: str,
        key_version_ref: str,
        expected_generation_ref: str,
    ) -> MatrixProtectedCacheState:
        root_fd = self._open_root_fd()
        try:
            fd = self._open_cache_fd(
                root_fd=root_fd, cache_name=self._cache_name(cache_ref)
            )
            try:
                chunks: list[bytes] = []
                remaining = MATRIX_SYNC_MAX_CACHE_BYTES + 1
                while remaining:
                    chunk = os.read(fd, min(64 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                ciphertext = b"".join(chunks)
            finally:
                os.close(fd)
        finally:
            os.close(root_fd)
        if len(ciphertext) > MATRIX_SYNC_MAX_CACHE_BYTES:
            raise MatrixProtectedCacheError("MATRIX_CACHE_SIZE_LIMIT_EXCEEDED")
        if (
            not ciphertext.startswith(_CONTAINER_MAGIC)
            or len(ciphertext) <= len(_CONTAINER_MAGIC) + _NONCE_BYTES
        ):
            raise MatrixProtectedCacheError("MATRIX_CACHE_CONTAINER_INVALID")
        try:
            plaintext = self._crypto_backend.decrypt(
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
                ciphertext=ciphertext[len(_CONTAINER_MAGIC) :],
                aad=_aad(
                    account_ref=account_ref,
                    cache_ref=cache_ref,
                    key_version_ref=key_version_ref,
                ),
            )
            state = MatrixProtectedCacheState.model_validate_json(plaintext)
        except MatrixCacheKeyUnavailable:
            raise
        except Exception as exc:
            raise MatrixProtectedCacheError("MATRIX_CACHE_INTEGRITY_FAILED") from exc
        if (state.account_ref, state.cache_ref, state.key_version_ref) != (
            account_ref,
            cache_ref,
            key_version_ref,
        ):
            raise MatrixProtectedCacheError("MATRIX_CACHE_SCOPE_MISMATCH")
        if state.generation_ref != expected_generation_ref:
            raise MatrixProtectedCacheError("MATRIX_CACHE_GENERATION_MISMATCH")
        return state

    def write(
        self,
        state: MatrixProtectedCacheState,
        *,
        key_item_ref: str,
    ) -> MatrixCacheWriteResult:
        plaintext = state.model_dump_json().encode("utf-8")
        if len(plaintext) > MATRIX_SYNC_MAX_CACHE_BYTES - 1024:
            raise MatrixProtectedCacheError("MATRIX_CACHE_SIZE_LIMIT_EXCEEDED")
        ciphertext = _CONTAINER_MAGIC + self._crypto_backend.encrypt(
            key_item_ref=key_item_ref,
            key_version_ref=state.key_version_ref,
            plaintext=plaintext,
            aad=_aad(
                account_ref=state.account_ref,
                cache_ref=state.cache_ref,
                key_version_ref=state.key_version_ref,
            ),
        )
        cache_name = self._cache_name(state.cache_ref)
        stage_name = f"{cache_name}.stage-{secrets.token_hex(8)}"
        root_fd = self._open_root_fd()
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        stage_created = False
        try:
            fd = os.open(stage_name, flags, 0o600, dir_fd=root_fd)
            stage_created = True
            try:
                self._validate_file_descriptor(fd)
                view = memoryview(ciphertext)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise MatrixProtectedCacheError("MATRIX_CACHE_WRITE_FAILED")
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
            self._verify_root_identity(os.lstat(self._root))
            os.replace(
                stage_name,
                cache_name,
                src_dir_fd=root_fd,
                dst_dir_fd=root_fd,
            )
            stage_created = False
            os.fsync(root_fd)
            verified_fd = self._open_cache_fd(root_fd=root_fd, cache_name=cache_name)
            os.close(verified_fd)
            self._verify_root_identity(os.lstat(self._root))
        finally:
            if stage_created:
                try:
                    os.unlink(stage_name, dir_fd=root_fd)
                    os.fsync(root_fd)
                except FileNotFoundError:
                    pass
            os.close(root_fd)
        fingerprint = hashlib.sha256(ciphertext).hexdigest()
        return MatrixCacheWriteResult(
            cache_ref=state.cache_ref,
            generation_ref=state.generation_ref,
            ciphertext_fingerprint_ref=f"ciphertext-fingerprint-ref:sha256:{fingerprint}",
            byte_count=len(ciphertext),
            receipt_ref=stable_matrix_sync_ref(
                "cache-write-receipt-ref:matrix",
                {
                    "cache_ref": state.cache_ref,
                    "generation_ref": state.generation_ref,
                    "ciphertext_fingerprint": fingerprint,
                },
            ),
        )

    def rotate(
        self,
        *,
        account_ref: str,
        cache_ref: str,
        key_item_ref: str,
        old_key_version_ref: str,
        new_key_version_ref: str,
        expected_generation_ref: str,
        next_generation_ref: str,
    ) -> MatrixCacheWriteResult:
        if old_key_version_ref == new_key_version_ref:
            raise MatrixProtectedCacheError("MATRIX_CACHE_KEY_VERSION_REUSE_DENIED")
        state = self.read(
            account_ref=account_ref,
            cache_ref=cache_ref,
            key_item_ref=key_item_ref,
            key_version_ref=old_key_version_ref,
            expected_generation_ref=expected_generation_ref,
        )
        self._crypto_backend.create(
            key_item_ref=key_item_ref, key_version_ref=new_key_version_ref
        )
        rotated = state.model_copy(
            update={
                "key_version_ref": new_key_version_ref,
                "generation_ref": next_generation_ref,
            }
        )
        result = self.write(rotated, key_item_ref=key_item_ref)
        verified = self.read(
            account_ref=account_ref,
            cache_ref=cache_ref,
            key_item_ref=key_item_ref,
            key_version_ref=new_key_version_ref,
            expected_generation_ref=next_generation_ref,
        )
        if verified.generation_ref != next_generation_ref:
            raise MatrixProtectedCacheError("MATRIX_CACHE_ROTATION_VERIFY_FAILED")
        self._crypto_backend.delete(
            key_item_ref=key_item_ref, key_version_ref=old_key_version_ref
        )
        return result

    def purge(self, *, cache_ref: str) -> str:
        cache_name = self._cache_name(cache_ref)
        stage_prefix = f"{cache_name}.stage-"
        root_fd = self._open_root_fd()
        deleted = False
        try:
            descriptor = self._open_cache_fd_if_present(
                root_fd=root_fd, cache_name=cache_name
            )
            if descriptor is not None:
                os.close(descriptor)
                os.unlink(cache_name, dir_fd=root_fd)
                deleted = True
            for candidate_name in os.listdir(root_fd):
                if not candidate_name.startswith(stage_prefix):
                    continue
                try:
                    info = os.stat(
                        candidate_name, dir_fd=root_fd, follow_symlinks=False
                    )
                except FileNotFoundError:
                    continue
                if (
                    not stat.S_ISREG(info.st_mode)
                    or stat.S_ISLNK(info.st_mode)
                    or info.st_uid != os.geteuid()
                ):
                    raise MatrixProtectedCacheError(
                        "MATRIX_CACHE_STAGE_SUBSTITUTION_DENIED"
                    )
                os.unlink(candidate_name, dir_fd=root_fd)
                deleted = True
            if deleted:
                os.fsync(root_fd)
                self._verify_root_identity(os.lstat(self._root))
        finally:
            os.close(root_fd)
        return stable_matrix_sync_ref(
            "cache-purge-receipt-ref:matrix", {"cache_ref": cache_ref}
        )
