from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import stat
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.authority.contracts import authority_state_lock_manager
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MISSION_PLAN_MATERIALIZATION_LOCK_KEY,
    MissionStepDefinition,
    MissionStepOrchestrationContext,
)


DURABLE_MISSION_PLAN_SCHEMA_VERSION = "uaa-durable-mission-plan.v1"
DURABLE_MISSION_PLAN_LEDGER_FILE = "durable_mission_plan_receipts.jsonl"
DURABLE_MISSION_PLAN_LOCK_KEY = "authority-durable-mission-plans"
DURABLE_MISSION_PLAN_MAX_STEPS = 16
DURABLE_MISSION_PLAN_MAX_DEPENDENCIES = 64
DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES = 4 * 1024 * 1024
DURABLE_MISSION_PLAN_LEDGER_MAX_RECEIPTS = 1_000


class DurableMissionPlanError(RuntimeError):
    pass


class DurableMissionPlanConflictError(DurableMissionPlanError):
    pass


class DurableMissionPlanCorruptionError(DurableMissionPlanError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _safe_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))[:24]}"


def _read_bounded(descriptor: int, maximum: int) -> bytes:
    chunks: list[bytes] = []
    remaining = maximum + 1
    while remaining > 0:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class _MissionPlanModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DurableMissionPlanRetryAttemptBinding(_MissionPlanModel):
    attempt_no: StrictInt = Field(..., ge=2, le=3)
    dispatch_ref: str
    dispatch_request_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_attempt(self) -> "DurableMissionPlanRetryAttemptBinding":
        validate_task_ref(self.dispatch_ref, "durable_mission_retry_dispatch_ref")
        validate_task_ref(
            self.dispatch_request_fingerprint_ref,
            "durable_mission_retry_dispatch_fingerprint_ref",
        )
        return self


class DurableMissionPlanStepBinding(_MissionPlanModel):
    step_ref: str
    definition_fingerprint_ref: str
    dispatch_ref: str
    dispatch_request_fingerprint_ref: str
    dependency_step_refs: list[str] = Field(default_factory=list, max_length=15)
    retry_attempts: list[DurableMissionPlanRetryAttemptBinding] = Field(
        default_factory=list,
        max_length=2,
    )

    @model_validator(mode="after")
    def validate_binding(self) -> "DurableMissionPlanStepBinding":
        for value, field_name in [
            (self.step_ref, "durable_mission_plan_step_ref"),
            (
                self.definition_fingerprint_ref,
                "durable_mission_plan_definition_fingerprint_ref",
            ),
            (self.dispatch_ref, "durable_mission_plan_dispatch_ref"),
            (
                self.dispatch_request_fingerprint_ref,
                "durable_mission_plan_dispatch_fingerprint_ref",
            ),
            *[
                (ref, "durable_mission_plan_dependency_ref")
                for ref in self.dependency_step_refs
            ],
        ]:
            validate_task_ref(value, field_name)
        if self.step_ref in self.dependency_step_refs:
            raise ValueError("DURABLE_MISSION_PLAN_SELF_DEPENDENCY_DENIED")
        if len(self.dependency_step_refs) != len(set(self.dependency_step_refs)):
            raise ValueError("DURABLE_MISSION_PLAN_DUPLICATE_DEPENDENCY_DENIED")
        if [attempt.attempt_no for attempt in self.retry_attempts] != list(
            range(2, len(self.retry_attempts) + 2)
        ):
            raise ValueError("DURABLE_MISSION_PLAN_RETRY_ATTEMPT_SEQUENCE_INVALID")
        return self


class DurableMissionPlan(_MissionPlanModel):
    schema_version: Literal["uaa-durable-mission-plan.v1"] = (
        DURABLE_MISSION_PLAN_SCHEMA_VERSION
    )
    plan_ref: str
    mission_ref: str
    run_ref: str
    ordered_steps: list[DurableMissionPlanStepBinding] = Field(
        ...,
        min_length=1,
        max_length=DURABLE_MISSION_PLAN_MAX_STEPS,
    )
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_plan(self) -> "DurableMissionPlan":
        for value, field_name in [
            (self.plan_ref, "durable_mission_plan_ref"),
            (self.mission_ref, "durable_mission_ref"),
            (self.run_ref, "durable_mission_run_ref"),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(self.safe_summary, "durable_mission_plan_summary")
        step_refs = [step.step_ref for step in self.ordered_steps]
        if len(step_refs) != len(set(step_refs)):
            raise ValueError("DURABLE_MISSION_PLAN_DUPLICATE_STEP_DENIED")
        known_steps = set(step_refs)
        dependency_count = sum(
            len(step.dependency_step_refs) for step in self.ordered_steps
        )
        if dependency_count > DURABLE_MISSION_PLAN_MAX_DEPENDENCIES:
            raise ValueError("DURABLE_MISSION_PLAN_DEPENDENCY_LIMIT_EXCEEDED")
        if any(
            dependency not in known_steps
            for step in self.ordered_steps
            for dependency in step.dependency_step_refs
        ):
            raise ValueError("DURABLE_MISSION_PLAN_DEPENDENCY_NOT_FOUND")
        self._validate_acyclic()
        return self

    def _validate_acyclic(self) -> None:
        dependencies = {
            step.step_ref: set(step.dependency_step_refs) for step in self.ordered_steps
        }
        ready = [
            step.step_ref
            for step in self.ordered_steps
            if not dependencies[step.step_ref]
        ]
        visited: list[str] = []
        while ready:
            current = ready.pop(0)
            visited.append(current)
            for step in self.ordered_steps:
                unresolved = dependencies[step.step_ref]
                if current in unresolved:
                    unresolved.remove(current)
                    if not unresolved and step.step_ref not in visited + ready:
                        ready.append(step.step_ref)
        if len(visited) != len(self.ordered_steps):
            raise ValueError("DURABLE_MISSION_PLAN_DEPENDENCY_CYCLE_DENIED")

    @property
    def fingerprint_ref(self) -> str:
        return _safe_ref(
            "durable-mission-plan-fingerprint-ref",
            _plan_payload(self),
        )

    @property
    def topological_step_refs(self) -> list[str]:
        dependencies = {
            step.step_ref: set(step.dependency_step_refs) for step in self.ordered_steps
        }
        order_index = {
            step.step_ref: index for index, step in enumerate(self.ordered_steps)
        }
        ready = sorted(
            [step_ref for step_ref, refs in dependencies.items() if not refs],
            key=order_index.__getitem__,
        )
        result: list[str] = []
        while ready:
            current = ready.pop(0)
            result.append(current)
            for step_ref, unresolved in dependencies.items():
                if current in unresolved:
                    unresolved.remove(current)
                    if not unresolved and step_ref not in result + ready:
                        ready.append(step_ref)
                        ready.sort(key=order_index.__getitem__)
        return result


def _plan_payload(plan: DurableMissionPlan) -> dict[str, Any]:
    payload = plan.model_dump(mode="json")
    for step in payload["ordered_steps"]:
        if not step.get("retry_attempts"):
            step.pop("retry_attempts", None)
    return payload


class DurableMissionPlanReceipt(_MissionPlanModel):
    schema_version: Literal["uaa-durable-mission-plan.v1"] = (
        DURABLE_MISSION_PLAN_SCHEMA_VERSION
    )
    sequence: int = Field(..., ge=1)
    receipt_ref: str
    plan: DurableMissionPlan
    plan_fingerprint_ref: str
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_receipt(self) -> "DurableMissionPlanReceipt":
        for value, field_name in [
            (self.receipt_ref, "durable_mission_plan_receipt_ref"),
            (
                self.plan_fingerprint_ref,
                "durable_mission_plan_fingerprint_ref",
            ),
            (
                self.previous_entry_hash_ref,
                "durable_mission_plan_previous_hash_ref",
            ),
            (self.entry_hash_ref, "durable_mission_plan_entry_hash_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        if self.created_at.tzinfo is None:
            raise ValueError("DURABLE_MISSION_PLAN_TIMESTAMP_TIMEZONE_REQUIRED")
        if self.plan_fingerprint_ref != self.plan.fingerprint_ref:
            raise ValueError("DURABLE_MISSION_PLAN_FINGERPRINT_INVALID")
        return self


def _entry_hash(receipt: DurableMissionPlanReceipt) -> str:
    payload = receipt.model_dump(mode="json", exclude={"entry_hash_ref"})
    payload["plan"] = _plan_payload(receipt.plan)
    return _safe_ref(
        "durable-mission-plan-entry-hash-ref",
        payload,
    )


class DurableMissionPlanStore:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.receipts_path = state_dir / DURABLE_MISSION_PLAN_LEDGER_FILE
        self.lock_manager = authority_state_lock_manager(str(state_dir.resolve()))

    def accept(self, plan: DurableMissionPlan) -> DurableMissionPlanReceipt:
        with self.lock_manager.acquire(MISSION_PLAN_MATERIALIZATION_LOCK_KEY):
            return self._accept_under_materialization_lock(plan)

    def _accept_under_materialization_lock(
        self,
        plan: DurableMissionPlan,
    ) -> DurableMissionPlanReceipt:
        with self.lock_manager.acquire(DURABLE_MISSION_PLAN_LOCK_KEY):
            receipts = self._load()
            existing = self._validate_acceptance(receipts, plan)
            if existing is not None:
                return existing
            if len(receipts) >= DURABLE_MISSION_PLAN_LEDGER_MAX_RECEIPTS:
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_RECEIPT_LIMIT_EXCEEDED"
                )
            sequence = len(receipts) + 1
            base = DurableMissionPlanReceipt(
                sequence=sequence,
                receipt_ref=f"durable-mission-plan-receipt-ref:{sequence}",
                plan=plan,
                plan_fingerprint_ref=plan.fingerprint_ref,
                previous_entry_hash_ref=(
                    receipts[-1].entry_hash_ref if receipts else None
                ),
                entry_hash_ref="durable-mission-plan-entry-hash-ref:pending",
            )
            receipt = base.model_copy(update={"entry_hash_ref": _entry_hash(base)})
            self._append(receipt)
            return receipt

    def preflight_acceptance(
        self,
        plan: DurableMissionPlan,
    ) -> DurableMissionPlanReceipt | None:
        with self.lock_manager.acquire(DURABLE_MISSION_PLAN_LOCK_KEY):
            return self._validate_acceptance(self._load(), plan)

    @staticmethod
    def _validate_acceptance(
        receipts: list[DurableMissionPlanReceipt],
        plan: DurableMissionPlan,
    ) -> DurableMissionPlanReceipt | None:
        for receipt in receipts:
            same_plan = receipt.plan.plan_ref == plan.plan_ref
            same_mission_run = (
                receipt.plan.mission_ref == plan.mission_ref
                and receipt.plan.run_ref == plan.run_ref
            )
            if same_plan or same_mission_run:
                if (
                    receipt.plan_fingerprint_ref == plan.fingerprint_ref
                    and same_plan
                    and same_mission_run
                ):
                    return receipt
                raise DurableMissionPlanConflictError(
                    "DURABLE_MISSION_PLAN_IMMUTABLE_CONFLICT"
                )
        return None

    def list_receipts(self) -> list[DurableMissionPlanReceipt]:
        with self.lock_manager.acquire(DURABLE_MISSION_PLAN_LOCK_KEY):
            return self._load()

    def resolve_definition_binding(
        self,
        definition: MissionStepDefinition,
    ) -> MissionStepOrchestrationContext | None:
        """Resolve exact accepted-plan membership without granting authority."""

        with self.lock_manager.acquire(DURABLE_MISSION_PLAN_LOCK_KEY):
            receipts = self._load()
        if definition.orchestration_plan_ref is None:
            reserved = next(
                (
                    receipt
                    for receipt in receipts
                    if any(
                        binding.step_ref == definition.step_ref
                        for binding in receipt.plan.ordered_steps
                    )
                ),
                None,
            )
            return self._execution_context(reserved) if reserved is not None else None
        if (
            definition.planned_dispatch_ref is None
            or definition.planned_dispatch_request_fingerprint_ref is None
        ):
            return None
        receipt = next(
            (
                item
                for item in receipts
                if item.plan.plan_ref == definition.orchestration_plan_ref
            ),
            None,
        )
        if receipt is None:
            return None
        binding = next(
            (
                item
                for item in receipt.plan.ordered_steps
                if item.step_ref == definition.step_ref
            ),
            None,
        )
        if (
            receipt.plan.mission_ref != definition.mission_ref
            or receipt.plan.run_ref != definition.run_ref
            or binding is None
            or binding.definition_fingerprint_ref != definition.fingerprint_ref
            or binding.dispatch_ref != definition.planned_dispatch_ref
            or binding.dispatch_request_fingerprint_ref
            != definition.planned_dispatch_request_fingerprint_ref
            or binding.dependency_step_refs != definition.dependency_step_refs
            or [
                attempt.model_dump(mode="json")
                for attempt in binding.retry_attempts
            ]
            != [
                attempt.model_dump(mode="json")
                for attempt in definition.planned_retry_attempts
            ]
        ):
            return None
        return self._execution_context(receipt)

    @staticmethod
    def _execution_context(
        receipt: DurableMissionPlanReceipt,
    ) -> MissionStepOrchestrationContext:
        return MissionStepOrchestrationContext(
            plan_ref=receipt.plan.plan_ref,
            plan_fingerprint_ref=receipt.plan_fingerprint_ref,
            plan_receipt_ref=receipt.receipt_ref,
            ordered_step_refs=[step.step_ref for step in receipt.plan.ordered_steps],
        )

    @staticmethod
    def _decode(payload: bytes) -> list[DurableMissionPlanReceipt]:
        if len(payload) > DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES:
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_SIZE_LIMIT_EXCEEDED"
            )
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_INVALID"
            ) from exc
        if len(lines) > DURABLE_MISSION_PLAN_LEDGER_MAX_RECEIPTS:
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        receipts: list[DurableMissionPlanReceipt] = []
        previous: str | None = None
        plan_refs: set[str] = set()
        mission_runs: set[tuple[str, str]] = set()
        for index, line in enumerate((line for line in lines if line.strip()), 1):
            try:
                receipt = DurableMissionPlanReceipt.model_validate_json(line)
            except ValueError as exc:
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_INVALID"
                ) from exc
            if (
                receipt.sequence != index
                or receipt.previous_entry_hash_ref != previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
                or receipt.plan.plan_ref in plan_refs
                or (receipt.plan.mission_ref, receipt.plan.run_ref) in mission_runs
            ):
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_HISTORY_INVALID"
                )
            receipts.append(receipt)
            previous = receipt.entry_hash_ref
            plan_refs.add(receipt.plan.plan_ref)
            mission_runs.add((receipt.plan.mission_ref, receipt.plan.run_ref))
        return receipts

    def _load(self) -> list[DurableMissionPlanReceipt]:
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
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_READ_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_REGULAR_FILE_REQUIRED"
                )
            if metadata.st_size > DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES:
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_SIZE_LIMIT_EXCEEDED"
                )
            payload = _read_bounded(
                descriptor,
                DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES,
            )
        finally:
            os.close(descriptor)
        return self._decode(payload)

    def _append(self, receipt: DurableMissionPlanReceipt) -> None:
        if receipt.sequence > DURABLE_MISSION_PLAN_LEDGER_MAX_RECEIPTS:
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        self.state_dir.mkdir(parents=True, exist_ok=True)
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
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_WRITE_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size > DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES
            ):
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_SIZE_OR_TYPE_INVALID"
                )
            os.lseek(descriptor, 0, os.SEEK_SET)
            existing_payload = _read_bounded(
                descriptor,
                DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES,
            )
            existing = self._decode(existing_payload)
            expected_sequence = len(existing) + 1
            expected_previous = existing[-1].entry_hash_ref if existing else None
            if (
                receipt.sequence != expected_sequence
                or receipt.previous_entry_hash_ref != expected_previous
            ):
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_APPEND_RACE"
                )
            encoded = (
                json.dumps(receipt.model_dump(mode="json"), sort_keys=True) + "\n"
            ).encode("utf-8")
            if metadata.st_size + len(encoded) > DURABLE_MISSION_PLAN_LEDGER_MAX_BYTES:
                raise DurableMissionPlanCorruptionError(
                    "DURABLE_MISSION_PLAN_LEDGER_SIZE_LIMIT_EXCEEDED"
                )
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("durable mission plan append failed")
                view = view[written:]
            os.fsync(descriptor)
            new_file = metadata.st_size == 0
        except OSError as exc:
            raise DurableMissionPlanCorruptionError(
                "DURABLE_MISSION_PLAN_LEDGER_WRITE_FAILED"
            ) from exc
        finally:
            os.close(descriptor)
        if new_file:
            directory_fd = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
