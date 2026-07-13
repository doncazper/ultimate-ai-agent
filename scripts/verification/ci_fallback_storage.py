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


FULL_SUITE_LOCK_PATH = Path("/tmp/uaa-private-ci-full-suite.v1.lock")
FULL_SUITE_ATTEMPT_PATH = Path("/tmp/uaa-ci-full-suite-attempts.v1.json")


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
            "plan_fingerprint",
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
    def _validate_event(cls, event: dict[str, Any]) -> None:
        if set(event) - cls._ALLOWED_EVENT_FIELDS:
            raise ValueError("CI attempt ledger event contains forbidden fields")
        sha = event.get("repository_sha")
        if sha is not None and not SHA_PATTERN.fullmatch(str(sha)):
            raise ValueError("CI attempt ledger event contains an unsafe SHA")
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
        for key in ("manifest_fingerprint", "plan_fingerprint"):
            value = event.get(key)
            if value is not None and not re.fullmatch(r"[0-9a-f]{64}", str(value)):
                raise ValueError("CI attempt ledger event contains an unsafe fingerprint")
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
            self._validate_event(
                {
                    key: value
                    for key, value in record.items()
                    if key not in {"sequence", "previous_record_ref", "record_ref"}
                }
            )
            previous_ref = record["record_ref"]
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
        path: Path = FULL_SUITE_LOCK_PATH,
        *,
        wait_seconds: float = 0,
        repository_sha: str | None = None,
        attempt_scope: str = "private",
        attempt_path: Path = FULL_SUITE_ATTEMPT_PATH,
    ) -> None:
        self.path = path
        self.wait_seconds = wait_seconds
        self.repository_sha = repository_sha
        self.attempt_scope = attempt_scope
        self.attempt_path = attempt_path
        self.descriptor: int | None = None

    def __enter__(self) -> FullSuiteLock:
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
                    raise RuntimeError("a full-suite run is already active") from None
                time.sleep(min(0.25, max(0.01, deadline - time.monotonic())))
        self.descriptor = descriptor
        return self

    def _validate_attempt_identity(self) -> None:
        if self.descriptor is None:
            raise RuntimeError("full-suite lock must be held before start")
        if self.repository_sha is None:
            return
        if not SHA_PATTERN.fullmatch(self.repository_sha):
            raise ValueError("full-suite attempt requires an exact SHA")
        if self.attempt_scope not in {"github", "private"}:
            raise ValueError("full-suite attempt scope is invalid")

    def _read_attempt_records(self) -> list[dict[str, str]]:
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.attempt_path, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
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
                base = {
                    "repository_sha": record.get("repository_sha"),
                    "attempt_scope": record.get("attempt_scope"),
                }
                expected = "attempt-ref:ci:" + hashlib.sha256(
                    json.dumps(base, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                if (
                    not SHA_PATTERN.fullmatch(str(base["repository_sha"]))
                    or base["attempt_scope"] not in {"github", "private"}
                    or record.get("attempt_ref") != expected
                ):
                    raise ValueError("full-suite attempt ledger is corrupt")
            return records
        finally:
            os.close(descriptor)

    def _assert_attempt_available(self, records: list[dict[str, str]]) -> None:
        key = (self.repository_sha, self.attempt_scope)
        if any(
            (record.get("repository_sha"), record.get("attempt_scope")) == key
            for record in records
        ):
            raise RuntimeError("full suite was already attempted for this exact SHA")

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
        }
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
