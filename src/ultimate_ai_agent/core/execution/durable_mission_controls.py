from __future__ import annotations

import json
import os
import stat
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.authority.contracts import authority_state_lock_manager
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


MISSION_CONTROL_SCHEMA_VERSION = "uaa-authority-mission-control.v1"
MISSION_CONTROL_LEDGER_FILE = "authority_mission_control_receipts.jsonl"
MISSION_CONTROL_LOCK_KEY = "authority-mission-control"
MISSION_CONTROL_LEDGER_MAX_BYTES = 2 * 1024 * 1024
MISSION_CONTROL_LEDGER_MAX_RECEIPTS = 2_000


class MissionControlError(RuntimeError):
    pass


class MissionControlConflictError(MissionControlError):
    pass


class MissionControlCorruptionError(MissionControlError):
    pass


class MissionControlEvent(str, Enum):
    cancellation_requested = "cancellation_requested"
    approval_decision_recorded = "approval_decision_recorded"
    dead_letter_recovery_requested = "dead_letter_recovery_requested"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _safe_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))[:24]}"


class _MissionControlModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class MissionControlRequest(_MissionControlModel):
    schema_version: Literal["uaa-authority-mission-control.v1"] = (
        MISSION_CONTROL_SCHEMA_VERSION
    )
    control_ref: str
    event: MissionControlEvent
    plan_ref: str
    plan_fingerprint_ref: str
    mission_ref: str
    run_ref: str
    lease_ref: str
    idempotency_ref: str
    reason_ref: str
    dead_letter_step_ref: str | None = None
    dead_letter_receipt_ref: str | None = None
    dead_letter_entry_hash_ref: str | None = None
    approval_step_ref: str | None = None
    approval_request_ref: str | None = None
    approval_ref: str | None = None
    approval_scope_fingerprint_ref: str | None = None
    approval_decision: Literal["approve", "deny"] | None = None
    approval_decision_fingerprint_ref: str | None = None
    operator_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=320)
    raw_request_persisted: Literal[False] = False
    raw_output_persisted: Literal[False] = False
    credentials_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_request(self) -> "MissionControlRequest":
        for value, field_name in [
            (self.control_ref, "mission_control_ref"),
            (self.plan_ref, "mission_control_plan_ref"),
            (self.plan_fingerprint_ref, "mission_control_plan_fingerprint_ref"),
            (self.mission_ref, "mission_control_mission_ref"),
            (self.run_ref, "mission_control_run_ref"),
            (self.lease_ref, "mission_control_lease_ref"),
            (self.idempotency_ref, "mission_control_idempotency_ref"),
            (self.reason_ref, "mission_control_reason_ref"),
            (self.dead_letter_step_ref, "mission_control_dead_letter_step_ref"),
            (self.dead_letter_receipt_ref, "mission_control_dead_letter_receipt_ref"),
            (
                self.dead_letter_entry_hash_ref,
                "mission_control_dead_letter_entry_hash_ref",
            ),
            (self.approval_step_ref, "mission_control_approval_step_ref"),
            (self.approval_request_ref, "mission_control_approval_request_ref"),
            (self.approval_ref, "mission_control_approval_ref"),
            (
                self.approval_scope_fingerprint_ref,
                "mission_control_approval_scope_fingerprint_ref",
            ),
            (
                self.approval_decision_fingerprint_ref,
                "mission_control_approval_decision_fingerprint_ref",
            ),
            (self.operator_ref, "mission_control_operator_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "mission_control_safe_summary")
        dead_letter_refs = (
            self.dead_letter_step_ref,
            self.dead_letter_receipt_ref,
            self.dead_letter_entry_hash_ref,
        )
        approval_values = (
            self.approval_step_ref,
            self.approval_request_ref,
            self.approval_ref,
            self.approval_scope_fingerprint_ref,
            self.approval_decision,
            self.approval_decision_fingerprint_ref,
            self.operator_ref,
        )
        if self.event == MissionControlEvent.cancellation_requested.value:
            if any(value is not None for value in (*dead_letter_refs, *approval_values)):
                raise ValueError("MISSION_CONTROL_CANCELLATION_BINDING_FORBIDDEN")
        elif self.event == MissionControlEvent.approval_decision_recorded.value:
            if any(value is not None for value in dead_letter_refs):
                raise ValueError("MISSION_CONTROL_APPROVAL_DEAD_LETTER_REF_FORBIDDEN")
            if not all(value is not None for value in approval_values):
                raise ValueError("MISSION_CONTROL_APPROVAL_BINDING_REQUIRED")
        elif any(value is not None for value in approval_values):
            raise ValueError("MISSION_CONTROL_DEAD_LETTER_APPROVAL_REF_FORBIDDEN")
        elif not all(value is not None for value in dead_letter_refs):
            raise ValueError("MISSION_CONTROL_DEAD_LETTER_BINDING_REQUIRED")
        return self

    @property
    def fingerprint_ref(self) -> str:
        return _safe_ref(
            "mission-control-request-fingerprint-ref",
            self.model_dump(mode="json"),
        )


class MissionControlReceipt(_MissionControlModel):
    schema_version: Literal["uaa-authority-mission-control.v1"] = (
        MISSION_CONTROL_SCHEMA_VERSION
    )
    sequence: int = Field(..., ge=1)
    receipt_ref: str
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str
    request: MissionControlRequest
    request_fingerprint_ref: str
    checked_at: datetime = Field(default_factory=utc_now)
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_receipt(self) -> "MissionControlReceipt":
        for value, field_name in [
            (self.receipt_ref, "mission_control_receipt_ref"),
            (self.previous_entry_hash_ref, "mission_control_previous_hash_ref"),
            (self.entry_hash_ref, "mission_control_entry_hash_ref"),
            (self.request_fingerprint_ref, "mission_control_request_fingerprint_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        if self.request_fingerprint_ref != self.request.fingerprint_ref:
            raise ValueError("MISSION_CONTROL_REQUEST_FINGERPRINT_INVALID")
        if self.checked_at.tzinfo is None:
            raise ValueError("MISSION_CONTROL_TIMESTAMP_TIMEZONE_REQUIRED")
        validate_safe_task_text(self.safe_summary, "mission_control_receipt_summary")
        return self


def _entry_hash(receipt: MissionControlReceipt) -> str:
    return _safe_ref(
        "mission-control-entry-hash-ref",
        receipt.model_dump(mode="json", exclude={"entry_hash_ref"}),
    )


class MissionControlStore:
    """Append-only mission-scoped operator fences; never execution authority."""

    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.state_dir = state_dir
        self.receipts_path = state_dir / MISSION_CONTROL_LEDGER_FILE
        self.lock_manager = authority_state_lock_manager(str(state_dir.resolve()))
        self._clock = clock
        self._request_validators: list[
            Callable[[MissionControlRequest], None]
        ] = []

    def bind_request_validator(
        self,
        validator: Callable[[MissionControlRequest], None],
    ) -> None:
        self._request_validators.append(validator)

    def current_time(self) -> datetime:
        current = self._clock()
        if current.tzinfo is None:
            raise ValueError("MISSION_CONTROL_TRUSTED_CLOCK_TIMEZONE_REQUIRED")
        return current

    def append(self, request: MissionControlRequest) -> MissionControlReceipt:
        validated = MissionControlRequest.model_validate(
            request.model_dump(mode="python")
        )
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY),
        ):
            for validator in self._request_validators:
                validator(validated)
            receipts = self._load()
            existing = self._preflight(receipts, validated)
            if existing is not None:
                return existing
            sequence = len(receipts) + 1
            receipt = MissionControlReceipt(
                sequence=sequence,
                receipt_ref=f"mission-control-receipt-ref:{sequence}",
                previous_entry_hash_ref=(
                    receipts[-1].entry_hash_ref if receipts else None
                ),
                entry_hash_ref="mission-control-entry-hash-ref:pending",
                request=validated,
                request_fingerprint_ref=validated.fingerprint_ref,
                checked_at=self.current_time(),
                safe_summary=(
                    "Mission cancellation fence was appended before reconciliation."
                    if validated.event
                    == MissionControlEvent.cancellation_requested.value
                    else (
                        "Approval decision evidence was recorded without granting authority."
                        if validated.event
                        == MissionControlEvent.approval_decision_recorded.value
                        else "Dead-letter recovery intent was appended without replay."
                    )
                ),
            )
            receipt = receipt.model_copy(
                update={"entry_hash_ref": _entry_hash(receipt)}
            )
            self._append(receipt)
            return receipt

    def cancellation_for(
        self,
        *,
        plan_ref: str,
        plan_fingerprint_ref: str,
        mission_ref: str,
        run_ref: str,
    ) -> MissionControlReceipt | None:
        for value, field_name in [
            (plan_ref, "mission_control_plan_ref"),
            (plan_fingerprint_ref, "mission_control_plan_fingerprint_ref"),
            (mission_ref, "mission_control_mission_ref"),
            (run_ref, "mission_control_run_ref"),
        ]:
            validate_task_ref(value, field_name)
        with self.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY):
            return self._cancellation_for_loaded(
                self._load(),
                plan_ref=plan_ref,
                plan_fingerprint_ref=plan_fingerprint_ref,
                mission_ref=mission_ref,
                run_ref=run_ref,
            )

    def receipts(self) -> list[MissionControlReceipt]:
        with self.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY):
            return self._load()

    def approval_decision_for(
        self,
        *,
        plan_ref: str,
        step_ref: str,
    ) -> MissionControlReceipt | None:
        validate_task_ref(plan_ref, "mission_control_plan_ref")
        validate_task_ref(step_ref, "mission_control_approval_step_ref")
        with self.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY):
            return next(
                (
                    receipt
                    for receipt in reversed(self._load())
                    if receipt.request.event
                    == MissionControlEvent.approval_decision_recorded.value
                    and receipt.request.plan_ref == plan_ref
                    and receipt.request.approval_step_ref == step_ref
                ),
                None,
            )

    @staticmethod
    def _cancellation_for_loaded(
        receipts: list[MissionControlReceipt],
        *,
        plan_ref: str,
        plan_fingerprint_ref: str,
        mission_ref: str,
        run_ref: str,
    ) -> MissionControlReceipt | None:
        return next(
            (
                receipt
                for receipt in reversed(receipts)
                if receipt.request.event
                == MissionControlEvent.cancellation_requested.value
                and receipt.request.plan_ref == plan_ref
                and receipt.request.plan_fingerprint_ref == plan_fingerprint_ref
                and receipt.request.mission_ref == mission_ref
                and receipt.request.run_ref == run_ref
            ),
            None,
        )

    @staticmethod
    def _preflight(
        receipts: list[MissionControlReceipt],
        request: MissionControlRequest,
    ) -> MissionControlReceipt | None:
        for receipt in receipts:
            existing = receipt.request
            same_idempotency = existing.idempotency_ref == request.idempotency_ref
            same_control = existing.control_ref == request.control_ref
            same_plan_event = (
                existing.plan_ref == request.plan_ref
                and existing.event == request.event
                and existing.dead_letter_step_ref == request.dead_letter_step_ref
                and existing.approval_step_ref == request.approval_step_ref
            )
            if same_idempotency or same_control or same_plan_event:
                if existing.fingerprint_ref != request.fingerprint_ref:
                    raise MissionControlConflictError(
                        "MISSION_CONTROL_IDEMPOTENCY_OR_SCOPE_CONFLICT"
                    )
                return receipt
        return None

    def _append(self, receipt: MissionControlReceipt) -> None:
        if receipt.sequence > MISSION_CONTROL_LEDGER_MAX_RECEIPTS:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        self._validate_state_dir(create=True)
        encoded = (receipt.model_dump_json() + "\n").encode("utf-8")
        flags = (
            os.O_RDWR
            | os.O_APPEND
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(self.receipts_path, flags, 0o600)
        except OSError as exc:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_WRITE_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(self.receipts_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
                or metadata.st_size + len(encoded) > MISSION_CONTROL_LEDGER_MAX_BYTES
            ):
                raise MissionControlCorruptionError(
                    "MISSION_CONTROL_LEDGER_SIZE_OR_TYPE_INVALID"
                )
            existing = self._decode(os.pread(descriptor, metadata.st_size, 0))
            if (
                receipt.sequence != len(existing) + 1
                or receipt.previous_entry_hash_ref
                != (existing[-1].entry_hash_ref if existing else None)
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionControlCorruptionError(
                    "MISSION_CONTROL_LEDGER_APPEND_BINDING_INVALID"
                )
            self._preflight(existing, receipt.request)
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("mission control append failed")
                view = view[written:]
            os.fsync(descriptor)
            new_file = metadata.st_size == 0
        except OSError as exc:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_WRITE_FAILED"
            ) from exc
        finally:
            os.close(descriptor)
        if new_file:
            directory_fd = os.open(self.receipts_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

    def _load(self) -> list[MissionControlReceipt]:
        if not self._validate_state_dir(create=False):
            return []
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            descriptor = os.open(self.receipts_path, flags)
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_READ_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(self.receipts_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
                or metadata.st_size > MISSION_CONTROL_LEDGER_MAX_BYTES
            ):
                raise MissionControlCorruptionError(
                    "MISSION_CONTROL_LEDGER_SIZE_OR_TYPE_INVALID"
                )
            payload = os.read(descriptor, MISSION_CONTROL_LEDGER_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
        if len(payload) > MISSION_CONTROL_LEDGER_MAX_BYTES:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_SIZE_INVALID"
            )
        return self._decode(payload)

    def _validate_state_dir(self, *, create: bool) -> bool:
        if create:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            metadata = os.lstat(self.state_dir)
        except FileNotFoundError:
            return False
        if not stat.S_ISDIR(metadata.st_mode):
            raise MissionControlCorruptionError("MISSION_CONTROL_STATE_DIR_INVALID")
        return True

    @staticmethod
    def _decode(payload: bytes) -> list[MissionControlReceipt]:
        if not payload:
            return []
        if not payload.endswith(b"\n"):
            raise MissionControlCorruptionError("MISSION_CONTROL_LEDGER_TRUNCATED")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_DECODE_FAILED"
            ) from exc
        if len(lines) > MISSION_CONTROL_LEDGER_MAX_RECEIPTS:
            raise MissionControlCorruptionError(
                "MISSION_CONTROL_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        receipts: list[MissionControlReceipt] = []
        previous: str | None = None
        for sequence, line in enumerate(lines, start=1):
            try:
                receipt = MissionControlReceipt.model_validate_json(line)
            except Exception as exc:
                raise MissionControlCorruptionError(
                    "MISSION_CONTROL_LEDGER_INVALID"
                ) from exc
            if (
                receipt.sequence != sequence
                or receipt.previous_entry_hash_ref != previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionControlCorruptionError(
                    "MISSION_CONTROL_LEDGER_HASH_CHAIN_INVALID"
                )
            MissionControlStore._preflight(receipts, receipt.request)
            receipts.append(receipt)
            previous = receipt.entry_hash_ref
        return receipts
