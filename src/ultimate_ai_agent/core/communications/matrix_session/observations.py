from __future__ import annotations

import fcntl
import json
import os
import stat
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchReceipt,
)

from .target_policy import (
    matrix_discovery_freshness_ref,
    matrix_homeserver_observation_ref,
)
from .constants import MatrixSessionOperation, matrix_session_lane


MATRIX_DISCOVERY_OBSERVATION_TTL = timedelta(minutes=10)
MATRIX_DISCOVERY_LEDGER_MAX_BYTES = 256 * 1024
MATRIX_DISCOVERY_LEDGER_MAX_RECORDS = 128
MATRIX_DISCOVERY_RECORD_MAX_BYTES = 4 * 1024


class MatrixDiscoveryObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_version: Literal["uaa-matrix-discovery-observation.v1"] = (
        "uaa-matrix-discovery-observation.v1"
    )
    observation_ref: str
    freshness_ref: str
    source_discovery_origin_ref: str
    dispatch_receipt_ref: str
    checked_at: datetime
    expires_at: datetime
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"
    raw_target_persisted: Literal[False] = False
    provider_payload_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_observation(self) -> "MatrixDiscoveryObservation":
        for name in (
            "observation_ref",
            "freshness_ref",
            "source_discovery_origin_ref",
            "dispatch_receipt_ref",
        ):
            validate_execution_ref(str(getattr(self, name)), f"matrix_discovery_{name}")
        if self.freshness_ref != matrix_discovery_freshness_ref(self.observation_ref):
            raise ValueError("MATRIX_DISCOVERY_FRESHNESS_BINDING_MISMATCH")
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("MATRIX_DISCOVERY_CHECKED_AT_TIMEZONE_REQUIRED")
        if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
            raise ValueError("MATRIX_DISCOVERY_EXPIRY_TIMEZONE_REQUIRED")
        if self.expires_at != self.checked_at + MATRIX_DISCOVERY_OBSERVATION_TTL:
            raise ValueError("MATRIX_DISCOVERY_EXPIRY_BINDING_MISMATCH")
        return self


class MatrixDiscoveryObservationStore:
    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._path = state_dir / "matrix_discovery_observations.jsonl"

    def record_success(
        self,
        *,
        observation_ref: str,
        freshness_ref: str,
        source_discovery_origin_ref: str,
        dispatch_receipt_ref: str,
        checked_at: datetime,
    ) -> MatrixDiscoveryObservation:
        item = MatrixDiscoveryObservation(
            observation_ref=observation_ref,
            freshness_ref=freshness_ref,
            source_discovery_origin_ref=source_discovery_origin_ref,
            dispatch_receipt_ref=dispatch_receipt_ref,
            checked_at=checked_at,
            expires_at=checked_at + MATRIX_DISCOVERY_OBSERVATION_TTL,
        )
        descriptor = self._open_for_append()
        locked = False
        try:
            self._validate_metadata(os.fstat(descriptor))
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            locked = True
            metadata = os.fstat(descriptor)
            self._validate_metadata(metadata)
            records = self._read_descriptor(descriptor)
            for existing in reversed(records):
                if existing.dispatch_receipt_ref == dispatch_receipt_ref:
                    if existing != item:
                        raise ValueError("MATRIX_DISCOVERY_RECEIPT_REPLAY_MISMATCH")
                    return existing
            encoded = (
                json.dumps(
                    item.model_dump(mode="json"),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
                + "\n"
            ).encode("utf-8")
            if len(encoded) > MATRIX_DISCOVERY_RECORD_MAX_BYTES:
                raise ValueError("MATRIX_DISCOVERY_RECORD_SIZE_LIMIT")
            retained = self._retained(records, now=item.checked_at)
            retained = retained[-(MATRIX_DISCOVERY_LEDGER_MAX_RECORDS - 1) :]
            retained_payload = self._encode_records(retained)
            while (
                retained
                and len(retained_payload) + len(encoded)
                > MATRIX_DISCOVERY_LEDGER_MAX_BYTES
            ):
                retained.pop(0)
                retained_payload = self._encode_records(retained)
            if len(retained_payload) + len(encoded) > MATRIX_DISCOVERY_LEDGER_MAX_BYTES:
                raise ValueError("MATRIX_DISCOVERY_LEDGER_SIZE_LIMIT")
            if retained != records:
                os.lseek(descriptor, 0, os.SEEK_SET)
                os.ftruncate(descriptor, 0)
                os.write(descriptor, retained_payload)
            os.lseek(descriptor, 0, os.SEEK_END)
            os.write(descriptor, encoded)
            os.fsync(descriptor)
        finally:
            try:
                if locked:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        return item

    def prepare_for_discovery(self, *, now: datetime | None = None) -> list[str]:
        descriptor = self._open_for_append()
        locked = False
        try:
            self._validate_metadata(os.fstat(descriptor))
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            locked = True
            self._validate_metadata(os.fstat(descriptor))
            records = self._read_descriptor(descriptor)
            current = now or datetime.now(timezone.utc)
            retained = self._retained(records, now=current)
            encoded = self._encode_records(retained)
            if len(retained) != len(records):
                os.lseek(descriptor, 0, os.SEEK_SET)
                os.ftruncate(descriptor, 0)
                os.write(descriptor, encoded)
                os.fsync(descriptor)
            return []
        finally:
            try:
                if locked:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    def validate_current(
        self,
        *,
        observation_ref: str,
        freshness_ref: str,
        endpoint_url: str,
        dispatch_receipts: Sequence[AuthorityDispatchReceipt],
        now: datetime | None = None,
    ) -> list[str]:
        expected_observation_ref = matrix_homeserver_observation_ref(endpoint_url)
        if observation_ref != expected_observation_ref:
            return ["reason-ref:matrix-session:discovery-target-mismatch"]
        if freshness_ref != matrix_discovery_freshness_ref(observation_ref):
            return ["reason-ref:matrix-session:discovery-freshness-mismatch"]
        item = self._latest(observation_ref)
        if item is None:
            return ["reason-ref:matrix-session:discovery-evidence-missing"]
        if item.freshness_ref != freshness_ref:
            return ["reason-ref:matrix-session:discovery-freshness-mismatch"]
        discovery_lane = matrix_session_lane(MatrixSessionOperation.discovery_read)
        receipt = next(
            (
                candidate
                for candidate in dispatch_receipts
                if candidate.receipt_ref == item.dispatch_receipt_ref
            ),
            None,
        )
        if (
            receipt is None
            or receipt.status != "succeeded"
            or receipt.adapter_ref != discovery_lane.adapter_ref
            or receipt.capability_ref != discovery_lane.capability_ref
            or receipt.created_at != item.checked_at
            or not {item.observation_ref, item.freshness_ref}.issubset(
                receipt.evidence_refs
            )
            or receipt.raw_paths_included
            or receipt.raw_prompt_included
            or receipt.raw_response_included
            or receipt.raw_provider_payload_included
        ):
            return ["reason-ref:matrix-session:discovery-receipt-invalid"]
        observed_now = now or datetime.now(timezone.utc)
        if observed_now >= item.expires_at:
            return ["reason-ref:matrix-session:discovery-stale"]
        return []

    def _latest(self, observation_ref: str) -> MatrixDiscoveryObservation | None:
        try:
            descriptor = os.open(
                self._path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise ValueError("MATRIX_DISCOVERY_LEDGER_OPEN_FAILED") from exc
        locked = False
        try:
            self._validate_metadata(os.fstat(descriptor))
            fcntl.flock(descriptor, fcntl.LOCK_SH)
            locked = True
            self._validate_metadata(os.fstat(descriptor))
            records = self._read_descriptor(descriptor)
        finally:
            try:
                if locked:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        matches = [item for item in records if item.observation_ref == observation_ref]
        return matches[-1] if matches else None

    def _open_for_append(self) -> int:
        try:
            self._state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            state_metadata = self._state_dir.lstat()
            if (
                self._state_dir.is_symlink()
                or not stat.S_ISDIR(state_metadata.st_mode)
                or state_metadata.st_uid != os.geteuid()
                or stat.S_IMODE(state_metadata.st_mode) & 0o077
            ):
                raise OSError("unsafe state directory")
            return os.open(
                self._path,
                os.O_RDWR
                | os.O_CREAT
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except OSError as exc:
            raise ValueError("MATRIX_DISCOVERY_LEDGER_OPEN_FAILED") from exc

    @staticmethod
    def _validate_metadata(metadata: os.stat_result) -> None:
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) & 0o077
            or metadata.st_size > MATRIX_DISCOVERY_LEDGER_MAX_BYTES
        ):
            raise ValueError("MATRIX_DISCOVERY_LEDGER_UNSAFE")

    @staticmethod
    def _read_descriptor(descriptor: int) -> list[MatrixDiscoveryObservation]:
        os.lseek(descriptor, 0, os.SEEK_SET)
        payload = os.read(descriptor, MATRIX_DISCOVERY_LEDGER_MAX_BYTES + 1)
        if len(payload) > MATRIX_DISCOVERY_LEDGER_MAX_BYTES:
            raise ValueError("MATRIX_DISCOVERY_LEDGER_SIZE_LIMIT")
        lines = payload.splitlines()
        if len(lines) > MATRIX_DISCOVERY_LEDGER_MAX_RECORDS:
            raise ValueError("MATRIX_DISCOVERY_LEDGER_RECORD_LIMIT")
        try:
            return [
                MatrixDiscoveryObservation.model_validate_json(line)
                for line in lines
                if line
            ]
        except ValueError as exc:
            raise ValueError("MATRIX_DISCOVERY_LEDGER_CORRUPT") from exc

    @staticmethod
    def _encode_records(records: list[MatrixDiscoveryObservation]) -> bytes:
        return b"".join(
            (
                json.dumps(
                    item.model_dump(mode="json"),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                )
                + "\n"
            ).encode("utf-8")
            for item in records
        )

    @staticmethod
    def _retained(
        records: list[MatrixDiscoveryObservation], *, now: datetime
    ) -> list[MatrixDiscoveryObservation]:
        latest_by_observation: dict[str, MatrixDiscoveryObservation] = {}
        for item in records:
            if item.expires_at > now:
                latest_by_observation[item.observation_ref] = item
        return sorted(latest_by_observation.values(), key=lambda item: item.checked_at)
