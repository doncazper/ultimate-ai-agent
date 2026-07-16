from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import secrets
import stat
import time
import types
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

from scripts.verification.verification_contracts import (
    VerificationReceipt,
    VerificationRunManifest,
    verification_receipt_payload,
    verification_run_manifest_payload,
)


MAX_ARTIFACT_BYTES = 1024 * 1024
MAX_PUBLISH_ATTEMPTS = 16
MAX_LOCK_ATTEMPTS = 500
LOCK_RETRY_SECONDS = 0.01
MAX_DIRECTORY_ENTRIES = 2048
ARTIFACT_DIGEST_LENGTH = 64
OWNER_DIRECTORY_MODE = 0o700
OWNER_FILE_MODE = 0o600
PUBLICATION_LOCK_NAME = ".publication.lock"
_HEX_DIGITS = frozenset("0123456789abcdef")
_STAGE_NAME_PATTERN = re.compile(
    r"^\.(?P<digest>[0-9a-f]{64})\.[0-9]{1,20}\.[0-9a-f]{24}\.tmp$"
)


class VerificationReceiptStoreError(ValueError):
    """A content-free failure raised by the immutable verification store."""


class VerificationArtifactKind(StrEnum):
    RECEIPT = "receipt"
    RUN_MANIFEST = "run_manifest"

    @property
    def directory_name(self) -> str:
        return "receipts" if self is self.RECEIPT else "runs"


@dataclass(frozen=True)
class StoredVerificationArtifact:
    artifact_kind: VerificationArtifactKind
    artifact_digest: str
    byte_count: int
    created: bool

    @property
    def artifact_ref(self) -> str:
        return (
            f"verification-artifact:{self.artifact_kind.value}:"
            f"{self.artifact_digest}"
        )


def _fail(reason: str) -> None:
    raise VerificationReceiptStoreError(reason) from None


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _file_read_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _file_write_flags() -> int:
    return (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _is_safe_ancestor(metadata: os.stat_result) -> bool:
    if not stat.S_ISDIR(metadata.st_mode):
        return False
    mode = stat.S_IMODE(metadata.st_mode)
    owner_ok = metadata.st_uid in {0, os.geteuid()}
    root_sticky_directory = metadata.st_uid == 0 and bool(metadata.st_mode & stat.S_ISVTX)
    writable_by_others = bool(mode & 0o022)
    return owner_ok and (not writable_by_others or root_sticky_directory)


def _validate_owner_directory(metadata: os.stat_result) -> None:
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != OWNER_DIRECTORY_MODE
    ):
        _fail("verification-store-directory-unsafe")


def _validate_owner_file(
    metadata: os.stat_result,
    *,
    expected_size: int | None = None,
    expected_link_count: int = 1,
) -> None:
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != expected_link_count
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != OWNER_FILE_MODE
        or not 0 < metadata.st_size <= MAX_ARTIFACT_BYTES
        or (expected_size is not None and metadata.st_size != expected_size)
    ):
        _fail("verification-store-artifact-unsafe")


def _validate_lock_file(metadata: os.stat_result) -> None:
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != OWNER_FILE_MODE
        or metadata.st_size != 0
    ):
        _fail("verification-store-lock-unsafe")


def _validate_incomplete_stage_file(metadata: os.stat_result) -> None:
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != OWNER_FILE_MODE
        or not 0 <= metadata.st_size <= MAX_ARTIFACT_BYTES
    ):
        _fail("verification-store-stale-stage-unsafe")


def _canonical_bytes(contract: VerificationReceipt | VerificationRunManifest) -> bytes:
    try:
        contract.validate()
        payload = (
            verification_receipt_payload(contract)
            if isinstance(contract, VerificationReceipt)
            else verification_run_manifest_payload(contract)
        )
        encoded = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail("verification-store-contract-invalid")
    if not 0 < len(encoded) <= MAX_ARTIFACT_BYTES:
        _fail("verification-store-artifact-size-invalid")
    return encoded


def _artifact_digest(encoded: bytes) -> str:
    return hashlib.sha256(encoded).hexdigest()


def _validate_artifact_digest(value: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != ARTIFACT_DIGEST_LENGTH
        or any(character not in _HEX_DIGITS for character in value)
    ):
        _fail("verification-store-digest-invalid")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            _fail("verification-store-json-duplicate-field")
        output[key] = value
    return output


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("verification-store-json-nonfinite-number")
    return parsed


def _reject_nonfinite_constant(_value: str) -> None:
    _fail("verification-store-json-nonfinite-number")


def _decode_strict_json(encoded: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(
            encoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
            parse_float=_parse_finite_float,
        )
    except VerificationReceiptStoreError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        _fail("verification-store-json-invalid")
    if not isinstance(payload, dict):
        _fail("verification-store-json-invalid")
    try:
        canonical = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail("verification-store-json-invalid")
    if canonical != encoded:
        _fail("verification-store-json-not-canonical")
    return payload


def _coerce_json_value(value: Any, expected_type: Any) -> Any:
    if expected_type is Any:
        return value
    origin = get_origin(expected_type)
    arguments = get_args(expected_type)
    if origin in {Union, types.UnionType}:
        if value is None and type(None) in arguments:
            return None
        for candidate in arguments:
            if candidate is type(None):
                continue
            try:
                return _coerce_json_value(value, candidate)
            except (TypeError, ValueError):
                continue
        raise TypeError
    if origin is tuple:
        if not isinstance(value, list):
            raise TypeError
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return tuple(_coerce_json_value(item, arguments[0]) for item in value)
        if len(arguments) != len(value):
            raise TypeError
        return tuple(
            _coerce_json_value(item, item_type)
            for item, item_type in zip(value, arguments, strict=True)
        )
    if origin is list:
        if not isinstance(value, list) or len(arguments) != 1:
            raise TypeError
        return [_coerce_json_value(item, arguments[0]) for item in value]
    if origin is dict:
        if not isinstance(value, dict) or len(arguments) != 2:
            raise TypeError
        return {
            _coerce_json_value(key, arguments[0]): _coerce_json_value(
                item, arguments[1]
            )
            for key, item in value.items()
        }
    if isinstance(expected_type, type) and issubclass(expected_type, Enum):
        if not isinstance(value, str):
            raise TypeError
        return expected_type(value)
    if expected_type is str:
        if not isinstance(value, str):
            raise TypeError
        return value
    if expected_type is bool:
        if not isinstance(value, bool):
            raise TypeError
        return value
    if expected_type is int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError
        return value
    if expected_type is float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError
        output = float(value)
        if not math.isfinite(output):
            raise ValueError
        return output
    if is_dataclass(expected_type):
        if not isinstance(value, dict):
            raise TypeError
        return _contract_from_payload(expected_type, value)
    if value is None and expected_type is type(None):
        return None
    if not isinstance(value, expected_type):
        raise TypeError
    return value


def _contract_from_payload(contract_type: type[Any], payload: dict[str, Any]) -> Any:
    contract_fields = {field.name: field for field in fields(contract_type)}
    if any(key not in contract_fields for key in payload):
        _fail("verification-store-contract-unknown-field")
    try:
        type_hints = get_type_hints(contract_type)
        values = {
            key: _coerce_json_value(value, type_hints[key])
            for key, value in payload.items()
        }
        contract = contract_type(**values)
        contract.validate()
    except VerificationReceiptStoreError:
        raise
    except (KeyError, RecursionError, TypeError, ValueError):
        _fail("verification-store-contract-invalid")
    return contract


class VerificationReceiptStore:
    """Immutable content-addressed storage for content-free verification proof."""

    def __init__(self, base: Path) -> None:
        self._base = Path(base)
        self._base_identity = self._initialize_base()
        self._artifact_directory_identities: dict[
            VerificationArtifactKind, tuple[int, int]
        ] = {}
        self._publication_lock_identities: dict[
            VerificationArtifactKind, tuple[int, int]
        ] = {}
        for kind in VerificationArtifactKind:
            descriptor = self._open_artifact_directory(kind, create=True)
            try:
                metadata = os.fstat(descriptor)
                self._artifact_directory_identities[kind] = (
                    metadata.st_dev,
                    metadata.st_ino,
                )
                lock_descriptor = self._open_publication_lock_file(
                    kind=kind,
                    directory_descriptor=descriptor,
                    create=True,
                )
                try:
                    lock_metadata = os.fstat(lock_descriptor)
                    self._publication_lock_identities[kind] = (
                        lock_metadata.st_dev,
                        lock_metadata.st_ino,
                    )
                finally:
                    os.close(lock_descriptor)
            finally:
                os.close(descriptor)

    def _walk_base(self, *, create: bool) -> int:
        if (
            not self._base.is_absolute()
            or self._base.anchor != os.sep
            or self._base == Path(self._base.anchor)
        ):
            _fail("verification-store-base-invalid")
        components = self._base.parts[1:]
        if not components or any(component in {"", ".", ".."} for component in components):
            _fail("verification-store-base-invalid")
        try:
            descriptor = os.open(self._base.anchor, _directory_flags())
        except OSError:
            _fail("verification-store-base-unavailable")
        try:
            if not _is_safe_ancestor(os.fstat(descriptor)):
                _fail("verification-store-ancestor-unsafe")
            for index, component in enumerate(components):
                try:
                    next_descriptor = os.open(
                        component, _directory_flags(), dir_fd=descriptor
                    )
                except FileNotFoundError:
                    if not create:
                        _fail("verification-store-base-substituted")
                    try:
                        os.mkdir(component, OWNER_DIRECTORY_MODE, dir_fd=descriptor)
                        os.fsync(descriptor)
                    except FileExistsError:
                        pass
                    except OSError:
                        _fail("verification-store-base-unavailable")
                    try:
                        next_descriptor = os.open(
                            component, _directory_flags(), dir_fd=descriptor
                        )
                    except OSError:
                        _fail("verification-store-base-unavailable")
                except OSError:
                    _fail("verification-store-base-unsafe")
                os.close(descriptor)
                descriptor = next_descriptor
                metadata = os.fstat(descriptor)
                if index == len(components) - 1:
                    _validate_owner_directory(metadata)
                elif not _is_safe_ancestor(metadata):
                    _fail("verification-store-ancestor-unsafe")
            return descriptor
        except Exception:
            os.close(descriptor)
            raise

    def _initialize_base(self) -> tuple[int, int]:
        descriptor = self._walk_base(create=True)
        try:
            metadata = os.fstat(descriptor)
            return metadata.st_dev, metadata.st_ino
        finally:
            os.close(descriptor)

    def _open_base(self) -> int:
        descriptor = self._walk_base(create=False)
        metadata = os.fstat(descriptor)
        if (metadata.st_dev, metadata.st_ino) != self._base_identity:
            os.close(descriptor)
            _fail("verification-store-base-substituted")
        return descriptor

    def _open_artifact_directory(
        self, kind: VerificationArtifactKind, *, create: bool
    ) -> int:
        base_descriptor = self._open_base()
        descriptor: int | None = None
        try:
            try:
                descriptor = os.open(
                    kind.directory_name, _directory_flags(), dir_fd=base_descriptor
                )
            except FileNotFoundError:
                if not create:
                    _fail("verification-store-directory-unavailable")
                try:
                    os.mkdir(
                        kind.directory_name,
                        OWNER_DIRECTORY_MODE,
                        dir_fd=base_descriptor,
                    )
                    os.fsync(base_descriptor)
                except FileExistsError:
                    pass
                except OSError:
                    _fail("verification-store-directory-unavailable")
                try:
                    descriptor = os.open(
                        kind.directory_name,
                        _directory_flags(),
                        dir_fd=base_descriptor,
                    )
                except OSError:
                    _fail("verification-store-directory-unsafe")
            except OSError:
                _fail("verification-store-directory-unsafe")
            metadata = os.fstat(descriptor)
            _validate_owner_directory(metadata)
            expected_identity = self._artifact_directory_identities.get(kind)
            if expected_identity is not None and (
                metadata.st_dev,
                metadata.st_ino,
            ) != expected_identity:
                _fail("verification-store-directory-substituted")
            return descriptor
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            raise
        finally:
            os.close(base_descriptor)

    @staticmethod
    def _write_all(descriptor: int, encoded: bytes) -> None:
        remaining = memoryview(encoded)
        while remaining:
            try:
                written = os.write(descriptor, remaining)
            except OSError:
                _fail("verification-store-write-failed")
            if written <= 0:
                _fail("verification-store-write-failed")
            remaining = remaining[written:]

    @staticmethod
    def _read_open_descriptor(descriptor: int, before: os.stat_result) -> bytes:
        chunks: list[bytes] = []
        remaining = MAX_ARTIFACT_BYTES + 1
        try:
            while remaining:
                chunk = os.read(descriptor, min(64 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
        except OSError:
            _fail("verification-store-read-failed")
        encoded = b"".join(chunks)
        after = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_mode,
            before.st_nlink,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_mode,
            after.st_nlink,
        )
        if (
            len(encoded) != before.st_size
            or len(encoded) > MAX_ARTIFACT_BYTES
            or before_identity != after_identity
        ):
            _fail("verification-store-artifact-changed-during-read")
        return encoded

    def _open_publication_lock_file(
        self,
        *,
        kind: VerificationArtifactKind,
        directory_descriptor: int,
        create: bool,
    ) -> int:
        flags = (
            os.O_RDWR
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor: int | None = None
        if create:
            try:
                descriptor = os.open(
                    PUBLICATION_LOCK_NAME,
                    flags | os.O_CREAT | os.O_EXCL,
                    OWNER_FILE_MODE,
                    dir_fd=directory_descriptor,
                )
                os.fsync(directory_descriptor)
            except FileExistsError:
                descriptor = None
            except OSError:
                _fail("verification-store-lock-unsafe")
        if descriptor is None:
            for attempt in range(MAX_PUBLISH_ATTEMPTS):
                try:
                    descriptor = os.open(
                        PUBLICATION_LOCK_NAME,
                        flags,
                        dir_fd=directory_descriptor,
                    )
                    break
                except FileNotFoundError:
                    if not create or attempt + 1 == MAX_PUBLISH_ATTEMPTS:
                        _fail("verification-store-lock-unsafe")
                    time.sleep(0.001)
                except OSError:
                    _fail("verification-store-lock-unsafe")
        if descriptor is None:
            _fail("verification-store-lock-unsafe")
        try:
            metadata = os.fstat(descriptor)
            _validate_lock_file(metadata)
            expected_identity = self._publication_lock_identities.get(kind)
            if expected_identity is not None and (
                metadata.st_dev,
                metadata.st_ino,
            ) != expected_identity:
                _fail("verification-store-lock-substituted")
            return descriptor
        except Exception:
            os.close(descriptor)
            raise

    def _acquire_publication_lock(
        self,
        *,
        kind: VerificationArtifactKind,
        directory_descriptor: int,
    ) -> int:
        descriptor = self._open_publication_lock_file(
            kind=kind,
            directory_descriptor=directory_descriptor,
            create=False,
        )
        try:
            for attempt in range(MAX_LOCK_ATTEMPTS):
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return descriptor
                except BlockingIOError:
                    if attempt + 1 == MAX_LOCK_ATTEMPTS:
                        _fail("verification-store-lock-timeout")
                    time.sleep(LOCK_RETRY_SECONDS)
                except OSError:
                    _fail("verification-store-lock-failed")
            _fail("verification-store-lock-timeout")
        except Exception:
            os.close(descriptor)
            raise

    @staticmethod
    def _read_contract_payload(
        *, kind: VerificationArtifactKind, encoded: bytes
    ) -> VerificationReceipt | VerificationRunManifest:
        payload = _decode_strict_json(encoded)
        contract_type = (
            VerificationReceipt
            if kind is VerificationArtifactKind.RECEIPT
            else VerificationRunManifest
        )
        return _contract_from_payload(contract_type, payload)

    @staticmethod
    def _bounded_directory_entries(directory_descriptor: int) -> tuple[str, ...]:
        try:
            entries = os.listdir(directory_descriptor)
        except OSError:
            _fail("verification-store-directory-enumeration-failed")
        if (
            len(entries) > MAX_DIRECTORY_ENTRIES
            or any(not isinstance(entry, str) for entry in entries)
        ):
            _fail("verification-store-directory-entry-bound-exceeded")
        return tuple(sorted(entries))

    def _remove_stale_prelink_stages_locked(
        self,
        *,
        directory_descriptor: int,
        kind: VerificationArtifactKind,
    ) -> None:
        removed = False
        try:
            for entry in self._bounded_directory_entries(directory_descriptor):
                match = _STAGE_NAME_PATTERN.fullmatch(entry)
                if match is None:
                    continue
                try:
                    descriptor = os.open(
                        entry,
                        _file_read_flags(),
                        dir_fd=directory_descriptor,
                    )
                except OSError:
                    _fail("verification-store-stale-stage-unsafe")
                try:
                    metadata = os.fstat(descriptor)
                    postlink_recovery = metadata.st_nlink == 2
                    if not postlink_recovery:
                        # A process may die after the exclusive stage create or
                        # during the bounded write loop. While the publication
                        # lock is held, an exact stage-shaped owner-only
                        # nlink-one regular file has no live writer and can be
                        # reclaimed without interpreting incomplete bytes.
                        _validate_incomplete_stage_file(metadata)
                finally:
                    os.close(descriptor)
                if postlink_recovery:
                    self._recover_interrupted_publication_locked(
                        directory_descriptor=directory_descriptor,
                        kind=kind,
                        artifact_digest=match.group("digest"),
                    )
                else:
                    try:
                        os.unlink(entry, dir_fd=directory_descriptor)
                    except OSError:
                        _fail("verification-store-stale-stage-recovery-failed")
                    removed = True
        finally:
            if removed:
                try:
                    os.fsync(directory_descriptor)
                except OSError:
                    _fail("verification-store-stale-stage-recovery-failed")

    def _assert_publication_capacity_locked(
        self,
        *,
        directory_descriptor: int,
        additional_entries: int,
    ) -> None:
        entries = self._bounded_directory_entries(directory_descriptor)
        if len(entries) + additional_entries > MAX_DIRECTORY_ENTRIES:
            _fail("verification-store-directory-entry-capacity-exceeded")

    def _recover_interrupted_publication_locked(
        self,
        *,
        directory_descriptor: int,
        kind: VerificationArtifactKind,
        artifact_digest: str,
    ) -> None:
        final_name = f"{artifact_digest}.json"
        try:
            final_descriptor = os.open(
                final_name,
                _file_read_flags(),
                dir_fd=directory_descriptor,
            )
        except OSError:
            _fail("verification-store-artifact-unsafe")
        try:
            final_metadata = os.fstat(final_descriptor)
            _validate_owner_file(final_metadata, expected_link_count=2)
            encoded = self._read_open_descriptor(final_descriptor, final_metadata)
            if _artifact_digest(encoded) != artifact_digest:
                _fail("verification-store-artifact-digest-mismatch")
            self._read_contract_payload(kind=kind, encoded=encoded)
            stage_pattern = re.compile(
                rf"^\.{re.escape(artifact_digest)}\.[0-9]{{1,20}}\."
                r"[0-9a-f]{24}\.tmp$"
            )
            candidates: list[str] = []
            for entry in self._bounded_directory_entries(directory_descriptor):
                if stage_pattern.fullmatch(entry) is None:
                    continue
                try:
                    candidate_descriptor = os.open(
                        entry,
                        _file_read_flags(),
                        dir_fd=directory_descriptor,
                    )
                except OSError:
                    _fail("verification-store-recovery-failed")
                try:
                    candidate_metadata = os.fstat(candidate_descriptor)
                    if (
                        candidate_metadata.st_dev,
                        candidate_metadata.st_ino,
                    ) != (final_metadata.st_dev, final_metadata.st_ino):
                        continue
                    _validate_owner_file(
                        candidate_metadata,
                        expected_size=len(encoded),
                        expected_link_count=2,
                    )
                    candidates.append(entry)
                finally:
                    os.close(candidate_descriptor)
            if len(candidates) != 1:
                _fail("verification-store-artifact-unsafe")
            try:
                os.unlink(candidates[0], dir_fd=directory_descriptor)
                os.fsync(directory_descriptor)
            except OSError:
                _fail("verification-store-recovery-failed")
            recovered_metadata = os.fstat(final_descriptor)
            _validate_owner_file(
                recovered_metadata,
                expected_size=len(encoded),
                expected_link_count=1,
            )
        finally:
            os.close(final_descriptor)

    def _read_encoded_locked(
        self,
        *,
        directory_descriptor: int,
        kind: VerificationArtifactKind,
        artifact_digest: str,
        allow_missing: bool,
    ) -> bytes | None:
        final_name = f"{artifact_digest}.json"
        try:
            descriptor = os.open(
                final_name,
                _file_read_flags(),
                dir_fd=directory_descriptor,
            )
        except FileNotFoundError:
            if allow_missing:
                return None
            _fail("verification-store-artifact-not-found")
        except OSError:
            _fail("verification-store-artifact-unsafe")
        try:
            before = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        if before.st_nlink == 2:
            self._recover_interrupted_publication_locked(
                directory_descriptor=directory_descriptor,
                kind=kind,
                artifact_digest=artifact_digest,
            )
        elif before.st_nlink != 1:
            _fail("verification-store-artifact-unsafe")
        try:
            descriptor = os.open(
                final_name,
                _file_read_flags(),
                dir_fd=directory_descriptor,
            )
        except OSError:
            _fail("verification-store-artifact-unsafe")
        try:
            before = os.fstat(descriptor)
            _validate_owner_file(before)
            encoded = self._read_open_descriptor(descriptor, before)
        finally:
            os.close(descriptor)
        if _artifact_digest(encoded) != artifact_digest:
            _fail("verification-store-artifact-digest-mismatch")
        return encoded

    def _read_encoded(
        self,
        *,
        kind: VerificationArtifactKind,
        artifact_digest: str,
    ) -> bytes:
        _validate_artifact_digest(artifact_digest)
        directory_descriptor = self._open_artifact_directory(kind, create=False)
        lock_descriptor: int | None = None
        try:
            lock_descriptor = self._acquire_publication_lock(
                kind=kind,
                directory_descriptor=directory_descriptor,
            )
            encoded = self._read_encoded_locked(
                directory_descriptor=directory_descriptor,
                kind=kind,
                artifact_digest=artifact_digest,
                allow_missing=False,
            )
            assert encoded is not None
            return encoded
        finally:
            if lock_descriptor is not None:
                os.close(lock_descriptor)
            os.close(directory_descriptor)

    def _publish(
        self,
        *,
        kind: VerificationArtifactKind,
        encoded: bytes,
    ) -> StoredVerificationArtifact:
        digest = _artifact_digest(encoded)
        final_name = f"{digest}.json"
        directory_descriptor = self._open_artifact_directory(kind, create=False)
        lock_descriptor: int | None = None
        temporary_name: str | None = None
        temporary_descriptor: int | None = None
        try:
            lock_descriptor = self._acquire_publication_lock(
                kind=kind,
                directory_descriptor=directory_descriptor,
            )
            self._remove_stale_prelink_stages_locked(
                directory_descriptor=directory_descriptor,
                kind=kind,
            )
            existing = self._read_encoded_locked(
                directory_descriptor=directory_descriptor,
                kind=kind,
                artifact_digest=digest,
                allow_missing=True,
            )
            if existing is not None:
                if existing != encoded:
                    _fail("verification-store-artifact-conflict")
                return StoredVerificationArtifact(
                    artifact_kind=kind,
                    artifact_digest=digest,
                    byte_count=len(encoded),
                    created=False,
                )
            self._assert_publication_capacity_locked(
                directory_descriptor=directory_descriptor,
                additional_entries=2,
            )
            for _attempt in range(MAX_PUBLISH_ATTEMPTS):
                candidate = f".{digest}.{os.getpid()}.{secrets.token_hex(12)}.tmp"
                try:
                    temporary_descriptor = os.open(
                        candidate,
                        _file_write_flags(),
                        OWNER_FILE_MODE,
                        dir_fd=directory_descriptor,
                    )
                    temporary_name = candidate
                    break
                except FileExistsError:
                    continue
                except OSError:
                    _fail("verification-store-temporary-create-failed")
            if temporary_descriptor is None or temporary_name is None:
                _fail("verification-store-temporary-create-failed")
            before_write = os.fstat(temporary_descriptor)
            if (
                not stat.S_ISREG(before_write.st_mode)
                or before_write.st_nlink != 1
                or before_write.st_uid != os.geteuid()
                or stat.S_IMODE(before_write.st_mode) != OWNER_FILE_MODE
                or before_write.st_size != 0
            ):
                _fail("verification-store-temporary-unsafe")
            self._write_all(temporary_descriptor, encoded)
            try:
                os.fsync(temporary_descriptor)
            except OSError:
                _fail("verification-store-write-failed")
            _validate_owner_file(
                os.fstat(temporary_descriptor), expected_size=len(encoded)
            )
            os.close(temporary_descriptor)
            temporary_descriptor = None
            try:
                os.link(
                    temporary_name,
                    final_name,
                    src_dir_fd=directory_descriptor,
                    dst_dir_fd=directory_descriptor,
                    follow_symlinks=False,
                )
                created = True
            except FileExistsError:
                created = False
            except OSError:
                _fail("verification-store-publish-failed")
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
                temporary_name = None
                os.fsync(directory_descriptor)
            except OSError:
                _fail("verification-store-publish-failed")
            observed = self._read_encoded_locked(
                directory_descriptor=directory_descriptor,
                kind=kind,
                artifact_digest=digest,
                allow_missing=False,
            )
            if observed != encoded:
                _fail("verification-store-artifact-conflict")
            return StoredVerificationArtifact(
                artifact_kind=kind,
                artifact_digest=digest,
                byte_count=len(encoded),
                created=created,
            )
        finally:
            if temporary_descriptor is not None:
                os.close(temporary_descriptor)
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name, dir_fd=directory_descriptor)
                    os.fsync(directory_descriptor)
                except OSError:
                    pass
            if lock_descriptor is not None:
                os.close(lock_descriptor)
            os.close(directory_descriptor)

    def put_receipt(self, receipt: VerificationReceipt) -> StoredVerificationArtifact:
        if not isinstance(receipt, VerificationReceipt):
            _fail("verification-store-contract-type-invalid")
        return self._publish(
            kind=VerificationArtifactKind.RECEIPT,
            encoded=_canonical_bytes(receipt),
        )

    def put_run_manifest(
        self, run_manifest: VerificationRunManifest
    ) -> StoredVerificationArtifact:
        if not isinstance(run_manifest, VerificationRunManifest):
            _fail("verification-store-contract-type-invalid")
        return self._publish(
            kind=VerificationArtifactKind.RUN_MANIFEST,
            encoded=_canonical_bytes(run_manifest),
        )

    def get_receipt(self, artifact_digest: str) -> VerificationReceipt:
        payload = _decode_strict_json(
            self._read_encoded(
                kind=VerificationArtifactKind.RECEIPT,
                artifact_digest=artifact_digest,
            )
        )
        return _contract_from_payload(VerificationReceipt, payload)

    def get_run_manifest(self, artifact_digest: str) -> VerificationRunManifest:
        payload = _decode_strict_json(
            self._read_encoded(
                kind=VerificationArtifactKind.RUN_MANIFEST,
                artifact_digest=artifact_digest,
            )
        )
        return _contract_from_payload(VerificationRunManifest, payload)

    # Narrow compatibility aliases for consumers that use read/write vocabulary.
    write_receipt = put_receipt
    write_run_manifest = put_run_manifest
    read_receipt = get_receipt
    read_run_manifest = get_run_manifest
