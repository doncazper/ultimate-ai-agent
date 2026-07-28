from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.verification.ci_fallback_contracts import (
    MAX_LEDGER_BYTES,
    MAX_LEDGER_RECORDS,
    MAX_DURATION_MS,
    SHA_PATTERN,
    SAFE_REF_PATTERN,
    validate_utc_timestamp,
)


FULL_SUITE_SHARED_DIRECTORY = Path("/tmp/uaa-ci-full-suite.v3")
FULL_SUITE_LOCK_PATH = FULL_SUITE_SHARED_DIRECTORY / "active.lock"
FULL_SUITE_ATTEMPT_PATH = FULL_SUITE_SHARED_DIRECTORY / "attempts.json"
TYPESCRIPT_TYPECHECK_LOCK_PATH = (
    FULL_SUITE_SHARED_DIRECTORY / "typescript-typecheck.lock"
)
TYPESCRIPT_TYPECHECK_ATTEMPT_PATH = (
    FULL_SUITE_SHARED_DIRECTORY / "typescript-typecheck-attempts.json"
)
SHARED_FULL_SUITE_DIRECTORY_MODE = 0o770
SHARED_FULL_SUITE_FILE_MODE = 0o660
FULL_SUITE_RESOURCE_REFS = frozenset(
    {
        "resource-ref:complete-pytest",
        "resource-ref:typescript-typecheck",
    }
)
FULL_SUITE_RESOURCE_LOCK_NAMES = frozenset(
    full_suite_lock_name
    for full_suite_lock_name in (
        "active.lock",
        "typescript-typecheck.lock",
    )
)
FULL_SUITE_RESOURCE_ATTEMPT_PATHS = frozenset(
    {
        FULL_SUITE_ATTEMPT_PATH,
        TYPESCRIPT_TYPECHECK_ATTEMPT_PATH,
    }
)


def _full_suite_path_identity(path: Path) -> Path:
    """Return one normalized path identity without exposing the raw path."""

    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError):
        raise ValueError("full-suite path identity is unavailable") from None


def _same_full_suite_path(left: Path, right: Path) -> bool:
    return _full_suite_path_identity(left) == _full_suite_path_identity(right)


class FullSuiteLockUnavailableError(RuntimeError):
    """Raised when the host-wide full-suite lock cannot be acquired safely."""


class FullSuiteAttemptAlreadyRecordedError(RuntimeError):
    """Raised when an execution plane already consumed its exact-SHA attempt."""


def full_suite_resource_paths(
    resource_ref: str,
    *,
    root: Path = FULL_SUITE_SHARED_DIRECTORY,
) -> tuple[Path, Path]:
    """Return the independent lock and attempt ledger for one resource class."""

    if resource_ref == "resource-ref:complete-pytest":
        return root / "active.lock", root / "attempts.json"
    if resource_ref == "resource-ref:typescript-typecheck":
        return (
            root / "typescript-typecheck.lock",
            root / "typescript-typecheck-attempts.json",
        )
    raise ValueError("full-suite resource ref is invalid")


def _validate_full_suite_resource_path_binding(
    *,
    resource_ref: str,
    lock_path: Path,
    attempt_path: Path,
) -> None:
    """Fail closed when a recognized resource lock is paired incorrectly."""

    recognized_lock_name = lock_path.name in FULL_SUITE_RESOURCE_LOCK_NAMES
    canonical_attempt_path = any(
        _same_full_suite_path(attempt_path, canonical_path)
        for canonical_path in FULL_SUITE_RESOURCE_ATTEMPT_PATHS
    )
    if not recognized_lock_name and not canonical_attempt_path:
        return
    binding_root = lock_path.parent if recognized_lock_name else attempt_path.parent
    expected_lock_path, expected_attempt_path = full_suite_resource_paths(
        resource_ref,
        root=binding_root,
    )
    if (
        lock_path.name != expected_lock_path.name
        or not _same_full_suite_path(lock_path.parent, binding_root)
    ):
        raise ValueError("full-suite lock path does not match resource ref")
    if (
        attempt_path.name != expected_attempt_path.name
        or not _same_full_suite_path(attempt_path.parent, lock_path.parent)
    ):
        raise ValueError("full-suite attempt path does not match resource ref")


def _prepare_shared_full_suite_directory(path: Path) -> None:
    try:
        path.mkdir(mode=SHARED_FULL_SUITE_DIRECTORY_MODE, parents=True, exist_ok=True)
        info = path.lstat()
        if info.st_uid == os.getuid():
            os.chown(path, -1, os.getgid())
            os.chmod(path, SHARED_FULL_SUITE_DIRECTORY_MODE)
            info = path.lstat()
    except OSError as exc:
        raise FullSuiteLockUnavailableError(
            "host-wide full-suite coordination is unavailable"
        ) from exc
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_gid != os.getgid()
        or stat.S_IMODE(info.st_mode) != SHARED_FULL_SUITE_DIRECTORY_MODE
    ):
        raise FullSuiteLockUnavailableError(
            "host-wide full-suite coordination is unsafe"
        )


def _open_shared_full_suite_file(path: Path) -> int:
    common_flags = os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0
    try:
        descriptor = os.open(
            path,
            os.O_RDWR | os.O_CREAT | common_flags,
            SHARED_FULL_SUITE_FILE_MODE,
        )
        info = os.fstat(descriptor)
        if info.st_uid == os.getuid():
            os.fchown(descriptor, -1, os.getgid())
            os.fchmod(descriptor, SHARED_FULL_SUITE_FILE_MODE)
            info = os.fstat(descriptor)
    except OSError as exc:
        raise FullSuiteLockUnavailableError(
            "host-wide full-suite coordination is unavailable"
        ) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_gid != os.getgid()
        or stat.S_IMODE(info.st_mode) != SHARED_FULL_SUITE_FILE_MODE
    ):
        os.close(descriptor)
        raise FullSuiteLockUnavailableError(
            "host-wide full-suite coordination is unsafe"
        )
    return descriptor


class AttemptLedger:
    _ALLOWED_EVENT_FIELDS = frozenset(
        {
            "event",
            "repository_sha",
            "series_ref",
            "run_ref",
            "status",
            "reason_ref",
            "observed_at",
            "manifest_version",
            "manifest_fingerprint",
            "manifest_attested",
            "observation_source",
            "run_created_at",
            "machine_profile_ref",
            "queue_duration_ms",
            "install_duration_ms",
            "test_duration_ms",
            "release_lane_duration_ms",
            "duration_ms",
            "base_sha",
            "source_branch_binding_ref",
            "authoritative_plan_fingerprint",
            "plan_fingerprint",
            "dependency_state_fingerprint",
            "selected_unit_refs",
            "diagnostic_unit_refs",
            "deferred_unit_refs",
            "github_gate_satisfied",
            "merge_gate_satisfied",
            "receipt_ref",
            "timings_ms",
        }
    )

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.path = directory / "attempts.v1.json"
        self.lock_path = directory / "attempts.v1.lock"

    def _prepare_directory(self) -> None:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ValueError("CI attempt ledger parent must be a real directory")
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise ValueError("CI attempt ledger parent ownership or mode is unsafe")

    def _open_lock(self) -> int:
        self._prepare_directory()
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.lock_path, flags, 0o600)
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            os.close(descriptor)
            raise ValueError("CI attempt ledger lock is unsafe")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return descriptor

    @staticmethod
    def _record_ref(record: dict[str, Any]) -> str:
        payload = {key: value for key, value in record.items() if key != "record_ref"}
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return f"ledger-ref:ci:{digest}"

    @classmethod
    def _validate_event(
        cls,
        event: dict[str, Any],
        *,
        allow_legacy_unbound_private: bool = False,
    ) -> None:
        if set(event) - cls._ALLOWED_EVENT_FIELDS:
            raise ValueError("CI attempt ledger event contains forbidden fields")
        sha = event.get("repository_sha")
        if sha is not None and not SHA_PATTERN.fullmatch(str(sha)):
            raise ValueError("CI attempt ledger event contains an unsafe SHA")
        base_sha = event.get("base_sha")
        if base_sha is not None and not SHA_PATTERN.fullmatch(str(base_sha)):
            raise ValueError("CI attempt ledger event contains an unsafe base SHA")
        source_branch_binding_ref = event.get("source_branch_binding_ref")
        if source_branch_binding_ref is not None and re.fullmatch(
            r"branch-binding-ref:private-ci:[0-9a-f]{64}",
            str(source_branch_binding_ref),
        ) is None:
            raise ValueError("CI attempt ledger branch binding is unsafe")
        for key in (
            "event",
            "series_ref",
            "run_ref",
            "status",
            "reason_ref",
            "manifest_version",
            "machine_profile_ref",
            "receipt_ref",
            "observation_source",
        ):
            value = event.get(key)
            if value is not None and not SAFE_REF_PATTERN.fullmatch(str(value)):
                raise ValueError("CI attempt ledger event contains an unsafe ref")
        manifest_attested = event.get("manifest_attested")
        if manifest_attested is not None and not isinstance(manifest_attested, bool):
            raise ValueError("CI attempt ledger attestation posture is unsafe")
        for key in (
            "manifest_fingerprint",
            "authoritative_plan_fingerprint",
            "plan_fingerprint",
            "dependency_state_fingerprint",
        ):
            value = event.get(key)
            if value is not None and not re.fullmatch(r"[0-9a-f]{64}", str(value)):
                raise ValueError("CI attempt ledger event contains an unsafe fingerprint")
        for key, limit in (
            ("selected_unit_refs", 128),
            ("diagnostic_unit_refs", 8),
            ("deferred_unit_refs", 128),
        ):
            refs = event.get(key, [])
            if (
                not isinstance(refs, list)
                or len(refs) > limit
                or len(refs) != len(set(refs))
                or any(SAFE_REF_PATTERN.fullmatch(str(ref)) is None for ref in refs)
            ):
                raise ValueError("CI attempt ledger scope refs are unsafe")
        for key in ("github_gate_satisfied", "merge_gate_satisfied"):
            posture = event.get(key)
            if posture is not None and posture is not False:
                raise ValueError("private CI attempt cannot satisfy an authoritative gate")
        for key in (
            "queue_duration_ms",
            "install_duration_ms",
            "test_duration_ms",
            "release_lane_duration_ms",
            "duration_ms",
        ):
            value = event.get(key)
            if value is not None and (
                not isinstance(value, int) or value < 0 or value > MAX_DURATION_MS
            ):
                raise ValueError("CI attempt ledger event contains an unsafe duration")
        timings = event.get("timings_ms", [])
        if not isinstance(timings, list) or len(timings) > MAX_LEDGER_RECORDS:
            raise ValueError("CI attempt ledger timing data is invalid")
        for timing in timings:
            if (
                not isinstance(timing, list)
                or len(timing) != 2
                or not SAFE_REF_PATTERN.fullmatch(str(timing[0]))
                or not isinstance(timing[1], int)
                or timing[1] < 0
                or timing[1] > MAX_DURATION_MS
            ):
                raise ValueError("CI attempt ledger timing data is invalid")
        observed_at = event.get("observed_at")
        if observed_at is not None:
            validate_utc_timestamp(str(observed_at))
        run_created_at = event.get("run_created_at")
        if run_created_at is not None:
            validate_utc_timestamp(str(run_created_at))
        if event.get("event") in {"private_start", "private_terminal"} and (
            source_branch_binding_ref is None
        ) and not allow_legacy_unbound_private:
            raise ValueError("private CI ledger event requires a branch binding")

    @classmethod
    def _migrate_legacy_unbound_private_records(
        cls,
        records: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], bool]:
        migrated = False
        normalized: list[dict[str, Any]] = []
        previous_ref = "ledger-ref:ci:genesis"
        for sequence, record in enumerate(records, start=1):
            event = {
                key: value
                for key, value in record.items()
                if key not in {"sequence", "previous_record_ref", "record_ref"}
            }
            is_legacy_unbound = (
                event.get("event") in {"private_start", "private_terminal"}
                and event.get("source_branch_binding_ref") is None
            )
            cls._validate_event(
                event,
                allow_legacy_unbound_private=is_legacy_unbound,
            )
            if is_legacy_unbound:
                migrated = True
                event = {
                    **event,
                    "event": f"legacy_{event['event']}",
                    "status": "legacy_non_authoritative",
                    "reason_ref": "reason-ref:private-ci:legacy-unbound-history",
                }
                cls._validate_event(event)
            normalized_record = {
                **event,
                "sequence": sequence,
                "previous_record_ref": previous_ref,
            }
            normalized_record["record_ref"] = cls._record_ref(normalized_record)
            previous_ref = normalized_record["record_ref"]
            normalized.append(normalized_record)
        return normalized, migrated

    def _read_locked(self) -> list[dict[str, Any]]:
        try:
            self.path.lstat()
        except FileNotFoundError:
            return []
        flags = os.O_RDONLY | os.O_NONBLOCK
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.path, flags)
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
                raise ValueError("CI attempt ledger file is unsafe")
            raw = os.read(descriptor, MAX_LEDGER_BYTES + 1)
        finally:
            os.close(descriptor)
        if len(raw) > MAX_LEDGER_BYTES:
            raise ValueError("CI attempt ledger exceeds its byte bound")
        if not raw:
            return []
        try:
            records = json.loads(raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("CI attempt ledger is corrupt") from exc
        if not isinstance(records, list) or len(records) > MAX_LEDGER_RECORDS:
            raise ValueError("CI attempt ledger exceeds its record bound")
        previous_ref = "ledger-ref:ci:genesis"
        for sequence, record in enumerate(records, start=1):
            if (
                not isinstance(record, dict)
                or record.get("sequence") != sequence
                or record.get("previous_record_ref") != previous_ref
                or record.get("record_ref") != self._record_ref(record)
            ):
                raise ValueError("CI attempt ledger hash chain is invalid")
            previous_ref = record["record_ref"]
        records, migrated = self._migrate_legacy_unbound_private_records(records)
        if migrated:
            self._atomic_write(records)
        return records

    def _atomic_write(self, records: list[dict[str, Any]]) -> None:
        encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > MAX_LEDGER_BYTES:
            raise ValueError("CI attempt ledger append exceeds its byte bound")
        descriptor, temp_name = tempfile.mkstemp(
            prefix="attempts.v1.", suffix=".tmp", dir=self.directory
        )
        temp_path = Path(temp_name)
        try:
            os.fchmod(descriptor, 0o600)
            os.write(descriptor, encoded)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temp_path, self.path)
            directory_descriptor = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temp_path.unlink(missing_ok=True)

    def read(self) -> list[dict[str, Any]]:
        descriptor = self._open_lock()
        try:
            return self._read_locked()
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        self._validate_event(event)
        descriptor = self._open_lock()
        try:
            records = self._read_locked()
            if len(records) >= MAX_LEDGER_RECORDS:
                records = records[-(MAX_LEDGER_RECORDS - 1) :]
                for index, record in enumerate(records, start=1):
                    record["sequence"] = index
                    record["previous_record_ref"] = (
                        "ledger-ref:ci:genesis"
                        if index == 1
                        else records[index - 2]["record_ref"]
                    )
                    record["record_ref"] = self._record_ref(record)
            record = {
                **event,
                "sequence": len(records) + 1,
                "previous_record_ref": (
                    records[-1]["record_ref"]
                    if records
                    else "ledger-ref:ci:genesis"
                ),
            }
            record["record_ref"] = self._record_ref(record)
            records.append(record)
            self._atomic_write(records)
            return record
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


class FullSuiteLock:
    def __init__(
        self,
        path: Path | None = None,
        *,
        wait_seconds: float = 0,
        repository_sha: str | None = None,
        attempt_scope: str = "private",
        resource_attempt_fingerprint: str | None = None,
        attempt_path: Path | None = None,
        shared_across_accounts: bool | None = None,
        resource_ref: str = "resource-ref:complete-pytest",
    ) -> None:
        if resource_ref not in FULL_SUITE_RESOURCE_REFS:
            raise ValueError("full-suite resource ref is invalid")
        resource_lock_path, resource_attempt_path = full_suite_resource_paths(
            resource_ref
        )
        if path is None:
            path = resource_lock_path
        elif any(
            _same_full_suite_path(path, canonical_path)
            for canonical_path in {
                FULL_SUITE_LOCK_PATH,
                TYPESCRIPT_TYPECHECK_LOCK_PATH,
            }
        ) and (
            not _same_full_suite_path(path, resource_lock_path)
        ):
            raise ValueError("full-suite lock path does not match resource ref")
        if attempt_path is None:
            if _same_full_suite_path(path, resource_lock_path):
                attempt_path = resource_attempt_path
            elif path.name in FULL_SUITE_RESOURCE_LOCK_NAMES:
                _, attempt_path = full_suite_resource_paths(
                    resource_ref,
                    root=path.parent,
                )
            else:
                attempt_path = path.with_name(f"{path.name}.attempts.json")
        elif any(
            _same_full_suite_path(attempt_path, canonical_path)
            for canonical_path in {
                FULL_SUITE_ATTEMPT_PATH,
                TYPESCRIPT_TYPECHECK_ATTEMPT_PATH,
            }
        ) and (
            not _same_full_suite_path(attempt_path, resource_attempt_path)
        ):
            raise ValueError("full-suite attempt path does not match resource ref")
        _validate_full_suite_resource_path_binding(
            resource_ref=resource_ref,
            lock_path=path,
            attempt_path=attempt_path,
        )
        self.path = path
        self.wait_seconds = wait_seconds
        self.repository_sha = repository_sha
        self.attempt_scope = attempt_scope
        self.resource_attempt_fingerprint = resource_attempt_fingerprint
        self.attempt_path = attempt_path
        self.resource_ref = resource_ref
        self.shared_across_accounts = (
            any(
                _same_full_suite_path(path, canonical_path)
                for canonical_path in {
                    FULL_SUITE_LOCK_PATH,
                    TYPESCRIPT_TYPECHECK_LOCK_PATH,
                }
            )
            if shared_across_accounts is None
            else shared_across_accounts
        )
        self.descriptor: int | None = None

    def __enter__(self) -> FullSuiteLock:
        if self.shared_across_accounts:
            _prepare_shared_full_suite_directory(self.path.parent)
            descriptor = _open_shared_full_suite_file(self.path)
        else:
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(self.path, flags, 0o600)
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
                os.close(descriptor)
                raise ValueError("private full-suite lock is unsafe")
        deadline = time.monotonic() + self.wait_seconds
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    os.close(descriptor)
                    raise FullSuiteLockUnavailableError(
                        "a full-suite run is already active"
                    ) from None
                time.sleep(min(0.25, max(0.01, deadline - time.monotonic())))
        self.descriptor = descriptor
        return self

    def _validate_attempt_identity(self) -> None:
        if self.descriptor is None:
            raise RuntimeError("full-suite lock must be held before start")
        if self.repository_sha is None:
            if self.resource_attempt_fingerprint is not None:
                raise ValueError(
                    "full-suite resource attempt requires an exact SHA"
                )
            return
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("full-suite attempt requires an exact SHA")
        if self.attempt_scope not in {"github", "local", "private"}:
            raise ValueError("full-suite attempt scope is invalid")
        if (
            not isinstance(self.resource_attempt_fingerprint, str)
            or re.fullmatch(
                r"[0-9a-f]{64}",
                self.resource_attempt_fingerprint,
            )
            is None
        ):
            raise ValueError(
                "full-suite attempt requires an exact resource fingerprint"
            )

    def _read_attempt_records(self) -> list[dict[str, str]]:
        if self.shared_across_accounts:
            _prepare_shared_full_suite_directory(self.attempt_path.parent)
            descriptor = _open_shared_full_suite_file(self.attempt_path)
        else:
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(self.attempt_path, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            private_file_unsafe = (
                not self.shared_across_accounts
                and (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or info.st_uid != os.getuid()
                    or info.st_mode & 0o077
                )
            )
            if private_file_unsafe:
                raise ValueError("full-suite attempt ledger is unsafe")
            raw = os.read(descriptor, MAX_LEDGER_BYTES + 1)
            if len(raw) > MAX_LEDGER_BYTES:
                raise ValueError("full-suite attempt ledger exceeds its byte bound")
            try:
                records = json.loads(raw.decode()) if raw else []
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("full-suite attempt ledger is corrupt") from exc
            if not isinstance(records, list) or len(records) > MAX_LEDGER_RECORDS:
                raise ValueError("full-suite attempt ledger exceeds its record bound")
            for record in records:
                if not isinstance(record, dict):
                    raise ValueError("full-suite attempt ledger is corrupt")
                recorded_resource_ref = record.get("resource_ref")
                legacy_complete_pytest_record = (
                    recorded_resource_ref is None
                    and self.resource_ref == "resource-ref:complete-pytest"
                    and set(record)
                    == {
                        "repository_sha",
                        "attempt_scope",
                        "resource_attempt_fingerprint",
                        "attempt_ref",
                    }
                )
                current_resource_record = (
                    recorded_resource_ref == self.resource_ref
                    and set(record)
                    == {
                        "repository_sha",
                        "attempt_scope",
                        "resource_ref",
                        "resource_attempt_fingerprint",
                        "attempt_ref",
                    }
                )
                if not legacy_complete_pytest_record and not current_resource_record:
                    raise ValueError("full-suite attempt ledger is corrupt")
                base = {
                    "repository_sha": record.get("repository_sha"),
                    "attempt_scope": record.get("attempt_scope"),
                    "resource_attempt_fingerprint": record.get(
                        "resource_attempt_fingerprint"
                    ),
                }
                if current_resource_record:
                    base["resource_ref"] = recorded_resource_ref
                expected = "attempt-ref:ci:" + hashlib.sha256(
                    json.dumps(base, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                if (
                    not SHA_PATTERN.fullmatch(str(base["repository_sha"]))
                    or base["attempt_scope"] not in {"github", "local", "private"}
                    or re.fullmatch(
                        r"[0-9a-f]{64}",
                        str(base["resource_attempt_fingerprint"]),
                    )
                    is None
                    or record.get("attempt_ref") != expected
                ):
                    raise ValueError("full-suite attempt ledger is corrupt")
            return records
        finally:
            os.close(descriptor)

    def _assert_attempt_available(self, records: list[dict[str, str]]) -> None:
        key = (self.repository_sha, self.resource_attempt_fingerprint)
        if any(
            (
                record.get("repository_sha"),
                record.get("resource_attempt_fingerprint"),
            )
            == key
            for record in records
        ):
            raise FullSuiteAttemptAlreadyRecordedError(
                "full suite resource was already attempted for this exact state"
            )

    def ensure_start_available(self) -> None:
        self._validate_attempt_identity()
        if self.repository_sha is None:
            return
        self._assert_attempt_available(self._read_attempt_records())

    def record_start(self) -> None:
        self._validate_attempt_identity()
        if self.repository_sha is None:
            return
        records = self._read_attempt_records()
        self._assert_attempt_available(records)
        record = {
            "repository_sha": self.repository_sha,
            "attempt_scope": self.attempt_scope,
            "resource_attempt_fingerprint": self.resource_attempt_fingerprint,
        }
        if self.resource_ref != "resource-ref:complete-pytest":
            record["resource_ref"] = self.resource_ref
        record["attempt_ref"] = "attempt-ref:ci:" + hashlib.sha256(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        records = [*records[-(MAX_LEDGER_RECORDS - 1) :], record]
        encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
        descriptor, temp_name = tempfile.mkstemp(
            prefix=f"{self.attempt_path.name}.",
            suffix=".tmp",
            dir=self.attempt_path.parent,
        )
        temp_path = Path(temp_name)
        try:
            if self.shared_across_accounts:
                os.fchown(descriptor, -1, os.getgid())
                os.fchmod(descriptor, SHARED_FULL_SUITE_FILE_MODE)
            else:
                os.fchmod(descriptor, 0o600)
            os.write(descriptor, encoded)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temp_path, self.attempt_path)
            directory_descriptor = os.open(self.attempt_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temp_path.unlink(missing_ok=True)

    def __exit__(self, *_args: object) -> None:
        if self.descriptor is not None:
            fcntl.flock(self.descriptor, fcntl.LOCK_UN)
            os.close(self.descriptor)
            self.descriptor = None
