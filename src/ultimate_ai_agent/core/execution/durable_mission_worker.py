from __future__ import annotations

import json
import os
import platform
import stat
import threading
from contextlib import nullcontext
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityLeaseScope,
    authority_lease_kill_switch_engaged,
    authority_state_lock_manager,
)
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    authority_dispatch_request_fingerprint,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchExecutionFence,
    AuthorityDispatchStatus,
    AuthorityDispatchWorkerClaimFence,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepStatus,
)
from ultimate_ai_agent.core.execution.durable_mission_controls import (
    MISSION_CONTROL_LOCK_KEY,
    MissionControlEvent,
    MissionControlRequest,
    MissionControlStore,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationRequest,
    AuthorityMissionOrchestrationResult,
    MissionCancellationExecutionFenceValidator,
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


MISSION_WORKER_SCHEMA_VERSION = "uaa-local-mission-worker.v1"
MISSION_WORKER_LEDGER_FILE = "local_mission_worker_receipts.jsonl"
MISSION_WORKER_LOCK_KEY = "authority-local-mission-worker"
MISSION_WORKER_LEDGER_MAX_BYTES = 4 * 1024 * 1024
MISSION_WORKER_LEDGER_MAX_RECEIPTS = 5_000
MISSION_WORKER_QUEUE_MAX_ITEMS = 32
MISSION_WORKER_CLAIM_TTL_MIN_SECONDS = 5
MISSION_WORKER_CLAIM_TTL_MAX_SECONDS = 300
MISSION_WORKER_HEARTBEAT_MIN_SECONDS = 1
MISSION_WORKER_ENABLED_ENV = "UAA_LOCAL_MISSION_WORKER_ENABLED"


class MissionWorkerError(RuntimeError):
    pass


class MissionWorkerConflictError(MissionWorkerError):
    pass


class MissionWorkerCorruptionError(MissionWorkerError):
    pass


class MissionWorkerDisabledError(MissionWorkerError):
    pass


class MissionWorkerPlatform(str, Enum):
    macos = "macos"
    linux_placeholder = "linux_placeholder"
    windows_placeholder = "windows_placeholder"
    unsupported = "unsupported"


class MissionWorkerEvent(str, Enum):
    enqueued = "enqueued"
    claimed = "claimed"
    heartbeat = "heartbeat"
    deferred = "deferred"
    completed = "completed"
    shutdown = "shutdown"


class MissionWorkerJobStatus(str, Enum):
    pending = "pending"
    claimed = "claimed"
    approval_wait = "approval_wait"
    retry_pending = "retry_pending"
    succeeded = "succeeded"
    failed = "failed"
    recovery_required = "recovery_required"
    cancelled = "cancelled"


class MissionWorkerRecoveryStatus(str, Enum):
    pending = "pending"
    actively_claimed = "actively_claimed"
    approval_wait = "approval_wait"
    retry_pending = "retry_pending"
    stale_claim = "stale_claim"
    prepared_dispatch = "prepared_dispatch"
    started_unknown_terminal = "started_unknown_terminal"
    succeeded = "succeeded"
    failed = "failed"
    dependency_blocked = "dependency_blocked"
    recovery_required = "recovery_required"
    cancelled = "cancelled"


def current_mission_worker_platform() -> MissionWorkerPlatform:
    system = platform.system().lower()
    if system == "darwin":
        return MissionWorkerPlatform.macos
    if system == "linux":
        return MissionWorkerPlatform.linux_placeholder
    if system == "windows":
        return MissionWorkerPlatform.windows_placeholder
    return MissionWorkerPlatform.unsupported


def local_mission_worker_configuration_from_environment() -> (
    LocalMissionWorkerConfiguration
):
    enabled_requested = os.environ.get(
        MISSION_WORKER_ENABLED_ENV, ""
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }
    observed_platform = current_mission_worker_platform()
    return LocalMissionWorkerConfiguration(
        enabled=(
            enabled_requested and observed_platform == MissionWorkerPlatform.macos
        ),
        observed_platform=observed_platform,
    )


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _safe_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))[:24]}"


def mission_worker_identity_ref(value: str) -> str:
    validate_task_ref(value, "mission_worker_identity_source_ref")
    return f"mission-worker-ref:sha256:{hash_text(value)[:24]}"


def _validate_opaque_worker_ref(value: str) -> None:
    prefix = "mission-worker-ref:sha256:"
    suffix = value.removeprefix(prefix)
    if (
        not value.startswith(prefix)
        or len(suffix) != 24
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise ValueError("MISSION_WORKER_OPAQUE_IDENTITY_REQUIRED")


class _WorkerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class LocalMissionWorkerConfiguration(_WorkerModel):
    schema_version: Literal["uaa-local-mission-worker.v1"] = (
        MISSION_WORKER_SCHEMA_VERSION
    )
    enabled: bool = False
    canonical_platform: Literal["macos"] = "macos"
    observed_platform: MissionWorkerPlatform = Field(
        default_factory=current_mission_worker_platform
    )
    queue_capacity: StrictInt = Field(
        default=16, ge=1, le=MISSION_WORKER_QUEUE_MAX_ITEMS
    )
    claim_ttl_seconds: StrictInt = Field(
        default=30,
        ge=MISSION_WORKER_CLAIM_TTL_MIN_SECONDS,
        le=MISSION_WORKER_CLAIM_TTL_MAX_SECONDS,
    )
    heartbeat_interval_seconds: StrictInt = Field(
        default=5,
        ge=MISSION_WORKER_HEARTBEAT_MIN_SECONDS,
        le=60,
    )
    local_only: Literal[True] = True
    remote_queue_enabled: Literal[False] = False
    daemon_enabled: Literal[False] = False
    production_scheduler_enabled: Literal[False] = False
    request_payload_persistence_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_configuration(self) -> "LocalMissionWorkerConfiguration":
        if self.heartbeat_interval_seconds * 2 >= self.claim_ttl_seconds:
            raise ValueError("MISSION_WORKER_HEARTBEAT_INTERVAL_UNSAFE")
        actual_platform = current_mission_worker_platform()
        if self.observed_platform != actual_platform.value:
            raise ValueError("MISSION_WORKER_OBSERVED_PLATFORM_MISMATCH")
        if self.enabled and actual_platform != MissionWorkerPlatform.macos:
            raise ValueError("MISSION_WORKER_MACOS_PLATFORM_REQUIRED")
        return self


class MissionWorkerJobBinding(_WorkerModel):
    job_ref: str
    plan_ref: str
    plan_fingerprint_ref: str
    mission_ref: str
    run_ref: str
    ordered_step_refs: list[str] = Field(..., min_length=1, max_length=16)
    dispatch_request_fingerprint_refs: list[str] = Field(
        ..., min_length=1, max_length=48
    )
    deadline: datetime

    @model_validator(mode="after")
    def validate_binding(self) -> "MissionWorkerJobBinding":
        for value, name in [
            (self.job_ref, "mission_worker_job_ref"),
            (self.plan_ref, "mission_worker_plan_ref"),
            (self.plan_fingerprint_ref, "mission_worker_plan_fingerprint_ref"),
            (self.mission_ref, "mission_worker_mission_ref"),
            (self.run_ref, "mission_worker_run_ref"),
            *[(ref, "mission_worker_step_ref") for ref in self.ordered_step_refs],
            *[
                (ref, "mission_worker_dispatch_fingerprint_ref")
                for ref in self.dispatch_request_fingerprint_refs
            ],
        ]:
            validate_task_ref(value, name)
        if len(self.ordered_step_refs) != len(set(self.ordered_step_refs)):
            raise ValueError("MISSION_WORKER_DUPLICATE_STEP_DENIED")
        if not (
            len(self.ordered_step_refs)
            <= len(self.dispatch_request_fingerprint_refs)
            <= len(self.ordered_step_refs) * 3
        ):
            raise ValueError("MISSION_WORKER_DISPATCH_BINDING_INCOMPLETE")
        if len(self.dispatch_request_fingerprint_refs) != len(
            set(self.dispatch_request_fingerprint_refs)
        ):
            raise ValueError("MISSION_WORKER_DUPLICATE_DISPATCH_BINDING")
        if self.deadline.tzinfo is None:
            raise ValueError("MISSION_WORKER_DEADLINE_TIMEZONE_REQUIRED")
        return self


def mission_worker_job_binding(
    request: AuthorityMissionOrchestrationRequest,
) -> MissionWorkerJobBinding:
    plan = request.build_durable_plan()
    return MissionWorkerJobBinding(
        job_ref=_safe_ref(
            "mission-worker-job-ref",
            {
                "plan_ref": plan.plan_ref,
                "plan_fingerprint_ref": plan.fingerprint_ref,
            },
        ),
        plan_ref=plan.plan_ref,
        plan_fingerprint_ref=plan.fingerprint_ref,
        mission_ref=plan.mission_ref,
        run_ref=plan.run_ref,
        ordered_step_refs=plan.topological_step_refs,
        dispatch_request_fingerprint_refs=[
            fingerprint
            for binding in plan.ordered_steps
            for fingerprint in [
                binding.dispatch_request_fingerprint_ref,
                *[
                    attempt.dispatch_request_fingerprint_ref
                    for attempt in binding.retry_attempts
                ],
            ]
        ],
        deadline=max(step.definition.deadline for step in request.steps),
    )


class MissionWorkerRequestResolver(Protocol):
    def resolve(
        self, binding: MissionWorkerJobBinding
    ) -> AuthorityMissionOrchestrationRequest | None: ...


class MissionWorkerReceipt(_WorkerModel):
    schema_version: Literal["uaa-local-mission-worker.v1"] = (
        MISSION_WORKER_SCHEMA_VERSION
    )
    sequence: StrictInt = Field(..., ge=1)
    receipt_ref: str
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str
    event: MissionWorkerEvent
    status: MissionWorkerJobStatus
    binding: MissionWorkerJobBinding
    generation: StrictInt = Field(default=0, ge=0)
    worker_ref: str | None = None
    claim_ref: str | None = None
    claim_expires_at: datetime | None = None
    retry_not_before: datetime | None = None
    reason_refs: list[str] = Field(default_factory=list, max_length=32)
    evidence_refs: list[str] = Field(default_factory=list, max_length=64)
    checked_at: datetime = Field(default_factory=utc_now)
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_receipt(self) -> "MissionWorkerReceipt":
        for value, name in [
            (self.receipt_ref, "mission_worker_receipt_ref"),
            (self.previous_entry_hash_ref, "mission_worker_previous_hash_ref"),
            (self.entry_hash_ref, "mission_worker_entry_hash_ref"),
            (self.claim_ref, "mission_worker_claim_ref"),
            *[(ref, "mission_worker_reason_ref") for ref in self.reason_refs],
            *[(ref, "mission_worker_evidence_ref") for ref in self.evidence_refs],
        ]:
            if value is not None:
                validate_task_ref(value, name)
        if self.worker_ref is not None:
            _validate_opaque_worker_ref(self.worker_ref)
        validate_safe_task_text(self.safe_summary, "mission_worker_safe_summary")
        claimed = self.status == MissionWorkerJobStatus.claimed.value
        if claimed != bool(
            self.worker_ref and self.claim_ref and self.claim_expires_at
        ):
            raise ValueError("MISSION_WORKER_CLAIM_POSTURE_INVALID")
        retry_pending = self.status == MissionWorkerJobStatus.retry_pending.value
        if retry_pending != (self.retry_not_before is not None):
            raise ValueError("MISSION_WORKER_RETRY_POSTURE_INVALID")
        if self.retry_not_before is not None and self.retry_not_before.tzinfo is None:
            raise ValueError("MISSION_WORKER_RETRY_TIMEZONE_REQUIRED")
        if self.checked_at.tzinfo is None:
            raise ValueError("MISSION_WORKER_TIMESTAMP_TIMEZONE_REQUIRED")
        if claimed:
            assert self.claim_expires_at is not None
            if (
                self.claim_expires_at.tzinfo is None
                or self.claim_expires_at <= self.checked_at
                or self.claim_expires_at > self.binding.deadline
                or self.claim_expires_at
                > self.checked_at
                + timedelta(seconds=MISSION_WORKER_CLAIM_TTL_MAX_SECONDS)
            ):
                raise ValueError("MISSION_WORKER_CLAIM_EXPIRY_INVALID")
        if (
            self.status
            in {
                MissionWorkerJobStatus.succeeded.value,
                MissionWorkerJobStatus.failed.value,
                MissionWorkerJobStatus.recovery_required.value,
                MissionWorkerJobStatus.cancelled.value,
            }
            and not self.reason_refs
        ):
            raise ValueError("MISSION_WORKER_TERMINAL_REASON_REQUIRED")
        return self


def _entry_hash(receipt: MissionWorkerReceipt) -> str:
    payload = receipt.model_dump(mode="json", exclude={"entry_hash_ref"})
    if receipt.retry_not_before is None:
        payload.pop("retry_not_before", None)
    return _safe_ref(
        "mission-worker-entry-hash-ref",
        payload,
    )


class MissionWorkerStore:
    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.state_dir = state_dir
        self.receipts_path = state_dir / MISSION_WORKER_LEDGER_FILE
        self.lock_manager = authority_state_lock_manager(str(state_dir.resolve()))
        self._clock = clock
        self._control_store: MissionControlStore | None = None

    def bind_control_store(self, control_store: MissionControlStore) -> None:
        if control_store.state_dir.resolve() != self.state_dir.resolve():
            raise ValueError("MISSION_WORKER_CONTROL_STATE_DIR_MISMATCH")
        self._control_store = control_store

    def current_time(self) -> datetime:
        current = self._clock()
        if current.tzinfo is None:
            raise ValueError("MISSION_WORKER_TRUSTED_CLOCK_TIMEZONE_REQUIRED")
        return current

    def enqueue(
        self,
        binding: MissionWorkerJobBinding,
        *,
        queue_capacity: int,
    ) -> MissionWorkerReceipt:
        if not 1 <= queue_capacity <= MISSION_WORKER_QUEUE_MAX_ITEMS:
            raise ValueError("MISSION_WORKER_QUEUE_CAPACITY_INVALID")
        control_lock = (
            self._control_store.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY)
            if self._control_store is not None
            else nullcontext()
        )
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            control_lock,
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            receipts = self._load()
            existing = self._preflight_enqueue_loaded(
                receipts,
                binding,
                queue_capacity=queue_capacity,
            )
            return existing or self._append_enqueue_loaded(receipts, binding)

    def _preflight_enqueue_loaded(
        self,
        receipts: list[MissionWorkerReceipt],
        binding: MissionWorkerJobBinding,
        *,
        queue_capacity: int,
    ) -> MissionWorkerReceipt | None:
        latest = self._latest(receipts, binding.job_ref)
        if latest is not None:
            if latest.binding != binding:
                raise MissionWorkerConflictError("MISSION_WORKER_JOB_BINDING_CONFLICT")
            return latest
        active = {
            item.binding.job_ref
            for item in self._latest_by_job(receipts).values()
            if item.status
            in {
                MissionWorkerJobStatus.pending.value,
                MissionWorkerJobStatus.claimed.value,
                MissionWorkerJobStatus.approval_wait.value,
                MissionWorkerJobStatus.retry_pending.value,
            }
        }
        if len(active) >= queue_capacity:
            raise MissionWorkerConflictError("MISSION_WORKER_QUEUE_CAPACITY_EXCEEDED")
        return None

    def _append_enqueue_loaded(
        self,
        receipts: list[MissionWorkerReceipt],
        binding: MissionWorkerJobBinding,
    ) -> MissionWorkerReceipt:
        receipt = self._build(
            receipts,
            event=MissionWorkerEvent.enqueued,
            status=MissionWorkerJobStatus.pending,
            binding=binding,
            checked_at=self.current_time(),
            safe_summary="Mission work was durably queued without request payloads.",
        )
        self._append(receipt)
        return receipt

    def claim(
        self,
        job_ref: str,
        *,
        worker_ref: str,
        ttl_seconds: int,
    ) -> MissionWorkerReceipt:
        validate_task_ref(job_ref, "mission_worker_job_ref")
        _validate_opaque_worker_ref(worker_ref)
        self._validate_ttl(ttl_seconds)
        control_lock = (
            self._control_store.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY)
            if self._control_store is not None
            else nullcontext()
        )
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            control_lock,
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            if authority_lease_kill_switch_engaged():
                raise MissionWorkerConflictError("MISSION_WORKER_KILL_SWITCH_ENGAGED")
            latest = self._require_latest(receipts, job_ref)
            if latest.status in {
                MissionWorkerJobStatus.succeeded.value,
                MissionWorkerJobStatus.failed.value,
                MissionWorkerJobStatus.recovery_required.value,
                MissionWorkerJobStatus.cancelled.value,
            }:
                return latest
            if self._control_store is not None:
                cancellation = self._control_store._cancellation_for_loaded(  # noqa: SLF001
                    self._control_store._load(),  # noqa: SLF001
                    plan_ref=latest.binding.plan_ref,
                    plan_fingerprint_ref=latest.binding.plan_fingerprint_ref,
                    mission_ref=latest.binding.mission_ref,
                    run_ref=latest.binding.run_ref,
                )
                if cancellation is not None:
                    receipt = self._build_from(
                        receipts,
                        latest,
                        event=MissionWorkerEvent.completed,
                        status=MissionWorkerJobStatus.cancelled,
                        generation=latest.generation,
                        reason_refs=[
                            "reason-ref:mission-worker:mission-cancellation-fenced"
                        ],
                        evidence_refs=[
                            cancellation.receipt_ref,
                            cancellation.entry_hash_ref,
                        ],
                        checked_at=current,
                        safe_summary=(
                            "Mission work was cancelled before a new worker claim."
                        ),
                    )
                    self._append(receipt)
                    return receipt
            if latest.binding.deadline <= current:
                receipt = self._build_from(
                    receipts,
                    latest,
                    event=MissionWorkerEvent.completed,
                    status=MissionWorkerJobStatus.failed,
                    generation=latest.generation,
                    reason_refs=["reason-ref:mission-worker:deadline-expired"],
                    checked_at=current,
                    safe_summary="Mission work expired before a local worker claim.",
                )
                self._append(receipt)
                return receipt
            if (
                latest.status == MissionWorkerJobStatus.retry_pending.value
                and (
                    latest.retry_not_before is None
                    or latest.retry_not_before > current
                )
            ):
                raise MissionWorkerConflictError(
                    "MISSION_WORKER_RETRY_BACKOFF_ACTIVE"
                )
            if (
                latest.status == MissionWorkerJobStatus.claimed.value
                and latest.claim_expires_at is not None
                and latest.claim_expires_at > current
            ):
                raise MissionWorkerConflictError("MISSION_WORKER_JOB_ALREADY_CLAIMED")
            generation = latest.generation + 1
            claim_ref = _safe_ref(
                "mission-worker-claim-ref",
                {
                    "job_ref": job_ref,
                    "worker_ref": worker_ref,
                    "generation": generation,
                },
            )
            receipt = self._build_from(
                receipts,
                latest,
                event=MissionWorkerEvent.claimed,
                status=MissionWorkerJobStatus.claimed,
                generation=generation,
                worker_ref=worker_ref,
                claim_ref=claim_ref,
                claim_expires_at=min(
                    current + timedelta(seconds=ttl_seconds), latest.binding.deadline
                ),
                checked_at=current,
                safe_summary="A local mission worker acquired a fenced job claim.",
            )
            self._append(receipt)
            return receipt

    def heartbeat(
        self,
        job_ref: str,
        *,
        worker_ref: str,
        claim_ref: str,
        generation: int,
        ttl_seconds: int,
    ) -> MissionWorkerReceipt:
        self._validate_ttl(ttl_seconds)
        _validate_opaque_worker_ref(worker_ref)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, job_ref, worker_ref, claim_ref, generation, current
            )
            receipt = self._build_from(
                receipts,
                latest,
                event=MissionWorkerEvent.heartbeat,
                status=MissionWorkerJobStatus.claimed,
                generation=generation,
                worker_ref=worker_ref,
                claim_ref=claim_ref,
                claim_expires_at=min(
                    current + timedelta(seconds=ttl_seconds), latest.binding.deadline
                ),
                checked_at=current,
                safe_summary="A local mission worker renewed its fenced job claim.",
            )
            self._append(receipt)
            return receipt

    def complete(
        self,
        job_ref: str,
        *,
        worker_ref: str,
        claim_ref: str,
        generation: int,
        status: MissionWorkerJobStatus,
        reason_refs: list[str],
        evidence_refs: list[str],
        execution_started: bool = False,
    ) -> MissionWorkerReceipt:
        if status not in {
            MissionWorkerJobStatus.succeeded,
            MissionWorkerJobStatus.failed,
            MissionWorkerJobStatus.recovery_required,
            MissionWorkerJobStatus.cancelled,
        }:
            raise ValueError("MISSION_WORKER_TERMINAL_STATUS_REQUIRED")
        _validate_opaque_worker_ref(worker_ref)
        control_lock = (
            self._control_store.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY)
            if self._control_store is not None
            else nullcontext()
        )
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            control_lock,
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, job_ref, worker_ref, claim_ref, generation, current
            )
            if self._control_store is not None:
                cancellation = self._control_store._cancellation_for_loaded(  # noqa: SLF001
                    self._control_store._load(),  # noqa: SLF001
                    plan_ref=latest.binding.plan_ref,
                    plan_fingerprint_ref=latest.binding.plan_fingerprint_ref,
                    mission_ref=latest.binding.mission_ref,
                    run_ref=latest.binding.run_ref,
                )
                if cancellation is not None:
                    status = (
                        MissionWorkerJobStatus.recovery_required
                        if execution_started
                        else MissionWorkerJobStatus.cancelled
                    )
                    reason_refs = [
                        *reason_refs,
                        (
                            "reason-ref:mission-worker:"
                            "cancellation-after-start-unsupported"
                            if execution_started
                            else "reason-ref:mission-worker:cancelled-before-start"
                        ),
                    ]
                    evidence_refs = [
                        *evidence_refs,
                        cancellation.receipt_ref,
                        cancellation.entry_hash_ref,
                    ]
            receipt = self._build_from(
                receipts,
                latest,
                event=MissionWorkerEvent.completed,
                status=status,
                generation=generation,
                reason_refs=list(dict.fromkeys(reason_refs)),
                evidence_refs=list(dict.fromkeys(evidence_refs)),
                checked_at=current,
                safe_summary="Local mission work reached a durable terminal posture.",
            )
            self._append(receipt)
            return receipt

    def defer_for_approval(
        self,
        job_ref: str,
        *,
        worker_ref: str,
        claim_ref: str,
        generation: int,
        reason_refs: list[str],
        evidence_refs: list[str],
    ) -> MissionWorkerReceipt:
        _validate_opaque_worker_ref(worker_ref)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, job_ref, worker_ref, claim_ref, generation, current
            )
            receipt = self._build_from(
                receipts,
                latest,
                event=MissionWorkerEvent.deferred,
                status=MissionWorkerJobStatus.approval_wait,
                generation=generation,
                reason_refs=list(dict.fromkeys(reason_refs)),
                evidence_refs=list(dict.fromkeys(evidence_refs)),
                checked_at=current,
                safe_summary=(
                    "Mission work released its claim while waiting for approval."
                ),
            )
            self._append(receipt)
            return receipt

    def defer_for_retry(
        self,
        job_ref: str,
        *,
        worker_ref: str,
        claim_ref: str,
        generation: int,
        retry_not_before: datetime,
        reason_refs: list[str],
        evidence_refs: list[str],
    ) -> MissionWorkerReceipt:
        _validate_opaque_worker_ref(worker_ref)
        if retry_not_before.tzinfo is None:
            raise ValueError("MISSION_WORKER_RETRY_TIMEZONE_REQUIRED")
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, job_ref, worker_ref, claim_ref, generation, current
            )
            effective_retry_not_before = max(retry_not_before, current)
            if effective_retry_not_before >= latest.binding.deadline:
                raise MissionWorkerConflictError(
                    "MISSION_WORKER_RETRY_WINDOW_INVALID"
                )
            receipt = self._build_from(
                receipts,
                latest,
                event=MissionWorkerEvent.deferred,
                status=MissionWorkerJobStatus.retry_pending,
                generation=generation,
                retry_not_before=effective_retry_not_before,
                reason_refs=list(dict.fromkeys(reason_refs)),
                evidence_refs=list(dict.fromkeys(evidence_refs)),
                checked_at=current,
                safe_summary=(
                    "Mission work released its claim for bounded retry backoff."
                ),
            )
            self._append(receipt)
            return receipt

    def record_shutdown(
        self,
        job_ref: str,
        *,
        worker_ref: str,
        claim_ref: str,
        generation: int,
    ) -> MissionWorkerReceipt:
        _validate_opaque_worker_ref(worker_ref)
        with (
            self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            current = self.current_time()
            receipts = self._load()
            latest = self._require_owned(
                receipts, job_ref, worker_ref, claim_ref, generation, current
            )
            receipt = self._build_from(
                receipts,
                latest,
                event=MissionWorkerEvent.shutdown,
                status=MissionWorkerJobStatus.pending,
                generation=generation,
                reason_refs=["reason-ref:mission-worker:graceful-shutdown"],
                checked_at=current,
                safe_summary="Local mission work was released for graceful shutdown.",
            )
            self._append(receipt)
            return receipt

    def receipts(self) -> list[MissionWorkerReceipt]:
        with self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY):
            return self._load()

    def latest(self) -> list[MissionWorkerReceipt]:
        with self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY):
            return list(self._latest_by_job(self._load()).values())

    def inspection_receipts(self) -> list[MissionWorkerReceipt]:
        try:
            os.lstat(self.receipts_path)
        except FileNotFoundError:
            return []
        with self.lock_manager.acquire(MISSION_WORKER_LOCK_KEY):
            return self._load()

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> None:
        if (
            not MISSION_WORKER_CLAIM_TTL_MIN_SECONDS
            <= ttl_seconds
            <= MISSION_WORKER_CLAIM_TTL_MAX_SECONDS
        ):
            raise ValueError("MISSION_WORKER_CLAIM_TTL_INVALID")

    @staticmethod
    def _latest(
        receipts: list[MissionWorkerReceipt], job_ref: str
    ) -> MissionWorkerReceipt | None:
        return next(
            (item for item in reversed(receipts) if item.binding.job_ref == job_ref),
            None,
        )

    @classmethod
    def _require_latest(
        cls, receipts: list[MissionWorkerReceipt], job_ref: str
    ) -> MissionWorkerReceipt:
        latest = cls._latest(receipts, job_ref)
        if latest is None:
            raise KeyError("MISSION_WORKER_JOB_UNKNOWN")
        return latest

    @staticmethod
    def _latest_by_job(
        receipts: list[MissionWorkerReceipt],
    ) -> dict[str, MissionWorkerReceipt]:
        result: dict[str, MissionWorkerReceipt] = {}
        for receipt in receipts:
            result[receipt.binding.job_ref] = receipt
        return result

    @classmethod
    def _require_owned(
        cls,
        receipts: list[MissionWorkerReceipt],
        job_ref: str,
        worker_ref: str,
        claim_ref: str,
        generation: int,
        current: datetime,
    ) -> MissionWorkerReceipt:
        latest = cls._require_latest(receipts, job_ref)
        if (
            latest.status != MissionWorkerJobStatus.claimed.value
            or latest.worker_ref != worker_ref
            or latest.claim_ref != claim_ref
            or latest.generation != generation
        ):
            raise MissionWorkerConflictError("MISSION_WORKER_STALE_OWNER_FENCED")
        if latest.claim_expires_at is None or latest.claim_expires_at <= current:
            raise MissionWorkerConflictError("MISSION_WORKER_CLAIM_EXPIRED")
        return latest

    def _build(
        self,
        receipts: list[MissionWorkerReceipt],
        *,
        event: MissionWorkerEvent,
        status: MissionWorkerJobStatus,
        binding: MissionWorkerJobBinding,
        safe_summary: str,
        **updates: Any,
    ) -> MissionWorkerReceipt:
        sequence = len(receipts) + 1
        receipt = MissionWorkerReceipt(
            sequence=sequence,
            receipt_ref=f"mission-worker-receipt-ref:{sequence}",
            previous_entry_hash_ref=receipts[-1].entry_hash_ref if receipts else None,
            entry_hash_ref="mission-worker-entry-hash-ref:pending",
            event=event,
            status=status,
            binding=binding,
            safe_summary=safe_summary,
            **updates,
        )
        return receipt.model_copy(update={"entry_hash_ref": _entry_hash(receipt)})

    def _build_from(
        self,
        receipts: list[MissionWorkerReceipt],
        latest: MissionWorkerReceipt,
        **updates: Any,
    ) -> MissionWorkerReceipt:
        return self._build(receipts, binding=latest.binding, **updates)

    def _append(self, receipt: MissionWorkerReceipt) -> None:
        if receipt.sequence > MISSION_WORKER_LEDGER_MAX_RECEIPTS:
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_RECEIPT_LIMIT_EXCEEDED"
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
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_WRITE_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(self.receipts_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
                or metadata.st_size + len(encoded) > MISSION_WORKER_LEDGER_MAX_BYTES
            ):
                raise MissionWorkerCorruptionError(
                    "MISSION_WORKER_LEDGER_SIZE_OR_TYPE_INVALID"
                )
            existing = self._decode(os.pread(descriptor, metadata.st_size, 0))
            expected_previous = existing[-1].entry_hash_ref if existing else None
            if (
                receipt.sequence != len(existing) + 1
                or receipt.previous_entry_hash_ref != expected_previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionWorkerCorruptionError(
                    "MISSION_WORKER_LEDGER_APPEND_BINDING_INVALID"
                )
            self._validate_transition(
                self._latest(existing, receipt.binding.job_ref), receipt
            )
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("mission worker append failed")
                view = view[written:]
            os.fsync(descriptor)
            new_file = metadata.st_size == 0
        except OSError as exc:
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_WRITE_FAILED"
            ) from exc
        finally:
            os.close(descriptor)
        if new_file:
            directory_fd = os.open(self.receipts_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

    def _load(self) -> list[MissionWorkerReceipt]:
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
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_READ_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            path_metadata = os.lstat(self.receipts_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise MissionWorkerCorruptionError("MISSION_WORKER_LEDGER_TYPE_INVALID")
            if metadata.st_size > MISSION_WORKER_LEDGER_MAX_BYTES:
                raise MissionWorkerCorruptionError("MISSION_WORKER_LEDGER_SIZE_INVALID")
            payload = os.read(descriptor, MISSION_WORKER_LEDGER_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
        if len(payload) > MISSION_WORKER_LEDGER_MAX_BYTES:
            raise MissionWorkerCorruptionError("MISSION_WORKER_LEDGER_SIZE_INVALID")
        return self._decode(payload)

    def _validate_state_dir(self, *, create: bool) -> bool:
        if create:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            metadata = os.lstat(self.state_dir)
        except FileNotFoundError:
            return False
        if not stat.S_ISDIR(metadata.st_mode):
            raise MissionWorkerCorruptionError("MISSION_WORKER_STATE_DIR_INVALID")
        return True

    @staticmethod
    def _decode(payload: bytes) -> list[MissionWorkerReceipt]:
        if not payload:
            return []
        if not payload.endswith(b"\n"):
            raise MissionWorkerCorruptionError("MISSION_WORKER_LEDGER_TRUNCATED")
        receipts: list[MissionWorkerReceipt] = []
        previous: str | None = None
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_DECODE_FAILED"
            ) from exc
        if len(lines) > MISSION_WORKER_LEDGER_MAX_RECEIPTS:
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        for sequence, line in enumerate(lines, start=1):
            try:
                receipt = MissionWorkerReceipt.model_validate_json(line)
            except Exception as exc:
                raise MissionWorkerCorruptionError(
                    "MISSION_WORKER_LEDGER_INVALID"
                ) from exc
            if (
                receipt.sequence != sequence
                or receipt.previous_entry_hash_ref != previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionWorkerCorruptionError(
                    "MISSION_WORKER_LEDGER_HASH_CHAIN_INVALID"
                )
            prior = MissionWorkerStore._latest(receipts, receipt.binding.job_ref)
            if prior is not None and prior.binding != receipt.binding:
                raise MissionWorkerCorruptionError("MISSION_WORKER_JOB_BINDING_CHANGED")
            MissionWorkerStore._validate_transition(prior, receipt)
            receipts.append(receipt)
            previous = receipt.entry_hash_ref
        return receipts

    @staticmethod
    def _validate_transition(
        prior: MissionWorkerReceipt | None,
        current: MissionWorkerReceipt,
    ) -> None:
        if prior is not None and current.checked_at < prior.checked_at:
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_TRANSITION_INVALID"
            )
        if prior is None:
            valid = (
                current.event == MissionWorkerEvent.enqueued.value
                and current.status == MissionWorkerJobStatus.pending.value
                and current.generation == 0
            )
        elif prior.status in {
            MissionWorkerJobStatus.succeeded.value,
            MissionWorkerJobStatus.failed.value,
            MissionWorkerJobStatus.recovery_required.value,
            MissionWorkerJobStatus.cancelled.value,
        }:
            valid = False
        elif current.event == MissionWorkerEvent.claimed.value:
            valid = (
                current.status == MissionWorkerJobStatus.claimed.value
                and current.generation == prior.generation + 1
                and (
                    prior.status == MissionWorkerJobStatus.pending.value
                    or prior.status == MissionWorkerJobStatus.approval_wait.value
                    or prior.status == MissionWorkerJobStatus.retry_pending.value
                    or (
                        prior.status == MissionWorkerJobStatus.claimed.value
                        and prior.claim_expires_at is not None
                        and prior.claim_expires_at <= current.checked_at
                    )
                )
            )
        elif current.event == MissionWorkerEvent.heartbeat.value:
            valid = (
                prior.status == MissionWorkerJobStatus.claimed.value
                and current.status == MissionWorkerJobStatus.claimed.value
                and current.generation == prior.generation
                and current.worker_ref == prior.worker_ref
                and current.claim_ref == prior.claim_ref
                and prior.claim_expires_at is not None
                and prior.claim_expires_at > current.checked_at
                and current.claim_expires_at is not None
                and current.claim_expires_at >= prior.claim_expires_at
            )
        elif current.event == MissionWorkerEvent.deferred.value:
            valid = (
                prior.status == MissionWorkerJobStatus.claimed.value
                and current.status
                in {
                    MissionWorkerJobStatus.approval_wait.value,
                    MissionWorkerJobStatus.retry_pending.value,
                }
                and current.generation == prior.generation
                and prior.claim_expires_at is not None
                and prior.claim_expires_at > current.checked_at
                and bool(current.reason_refs)
                and (
                    current.status != MissionWorkerJobStatus.retry_pending.value
                    or (
                        current.retry_not_before is not None
                        and current.retry_not_before >= current.checked_at
                    )
                )
            )
        elif current.event == MissionWorkerEvent.completed.value:
            valid = (
                (
                    prior.status == MissionWorkerJobStatus.claimed.value
                    or (
                        prior.status == MissionWorkerJobStatus.pending.value
                        and (
                            (
                                current.status
                                == MissionWorkerJobStatus.failed.value
                                and current.reason_refs
                                == ["reason-ref:mission-worker:deadline-expired"]
                            )
                            or current.status
                            == MissionWorkerJobStatus.cancelled.value
                        )
                    )
                )
                and current.status
                in {
                    MissionWorkerJobStatus.succeeded.value,
                    MissionWorkerJobStatus.failed.value,
                    MissionWorkerJobStatus.recovery_required.value,
                    MissionWorkerJobStatus.cancelled.value,
                }
                and current.generation == prior.generation
                and (
                    prior.status != MissionWorkerJobStatus.claimed.value
                    or (
                        prior.claim_expires_at is not None
                        and prior.claim_expires_at > current.checked_at
                    )
                    or (
                        current.status == MissionWorkerJobStatus.failed.value
                        and current.reason_refs
                        == ["reason-ref:mission-worker:deadline-expired"]
                        and current.checked_at >= current.binding.deadline
                    )
                )
            )
        elif current.event == MissionWorkerEvent.shutdown.value:
            valid = (
                prior.status == MissionWorkerJobStatus.claimed.value
                and current.status == MissionWorkerJobStatus.pending.value
                and current.generation == prior.generation
                and prior.claim_expires_at is not None
                and prior.claim_expires_at > current.checked_at
            )
        else:
            valid = False
        if not valid:
            raise MissionWorkerCorruptionError(
                "MISSION_WORKER_LEDGER_TRANSITION_INVALID"
            )


class MissionWorkerStepRecovery(_WorkerModel):
    step_safe_ref: str
    status: MissionWorkerRecoveryStatus
    claim_freshness: Literal["active", "stale", "not_claimed", "unknown"]
    generation: StrictInt = Field(..., ge=0)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    evidence_refs: list[str] = Field(default_factory=list, max_length=32)
    adapter_reinvocation_allowed: Literal[False] = False


class MissionWorkerJobReadModel(_WorkerModel):
    job_safe_ref: str
    plan_safe_ref: str
    mission_safe_ref: str
    run_safe_ref: str
    durable_status: MissionWorkerJobStatus
    recovery_status: MissionWorkerRecoveryStatus
    generation: StrictInt = Field(..., ge=0)
    latest_event: MissionWorkerEvent
    latest_event_at: datetime
    last_heartbeat_at: datetime | None = None
    heartbeat_freshness: Literal["active", "stale", "not_observed"]
    worker_safe_ref: str | None = None
    claim_safe_ref: str | None = None
    claim_expires_at: datetime | None = None
    deadline: datetime
    steps: list[MissionWorkerStepRecovery] = Field(default_factory=list, max_length=16)
    reason_refs: list[str] = Field(default_factory=list, max_length=32)
    evidence_refs: list[str] = Field(default_factory=list, max_length=64)
    request_payload_persisted: Literal[False] = False
    request_scoped_authority_required_before_resume: Literal[True] = True


class MissionWorkerReadModel(_WorkerModel):
    schema_version: Literal["uaa-local-mission-worker.v1"] = (
        MISSION_WORKER_SCHEMA_VERSION
    )
    inspection_ref: str
    configuration_enabled: bool
    canonical_platform: Literal["macos"] = "macos"
    observed_platform: MissionWorkerPlatform
    platform_execution_supported: bool
    linux_surface_posture: Literal["render_placeholder"] = "render_placeholder"
    windows_surface_posture: Literal["render_placeholder"] = "render_placeholder"
    queue_capacity: StrictInt
    queued_job_count: StrictInt = Field(..., ge=0)
    total_job_count: StrictInt = Field(..., ge=0)
    omitted_terminal_job_count: StrictInt = Field(..., ge=0)
    active_claim_count: StrictInt = Field(..., ge=0)
    stale_claim_count: StrictInt = Field(..., ge=0)
    kill_switch_engaged: bool
    jobs: list[MissionWorkerJobReadModel] = Field(default_factory=list, max_length=32)
    checked_at: datetime
    operator_summary: str
    local_only: Literal[True] = True
    execution_authority_granted: Literal[False] = False
    approval_or_lease_minted: Literal[False] = False
    remote_queue_enabled: Literal[False] = False
    daemon_enabled: Literal[False] = False
    raw_task_input_persisted: Literal[False] = False
    raw_paths_included: Literal[False] = False
    raw_logs_included: Literal[False] = False
    raw_provider_payloads_included: Literal[False] = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "raw_task_inputs",
            "raw_paths",
            "raw_logs",
            "raw_provider_payloads",
            "worker_identity_refs",
        ]
    )


def _identity_ref(prefix: str, value: str) -> str:
    return f"{prefix}:sha256:{hash_text(value)[:24]}"


def build_mission_worker_read_model(
    *,
    store: MissionWorkerStore,
    orchestrator: SynchronousAuthorityMissionOrchestrator,
    configuration: LocalMissionWorkerConfiguration | None = None,
) -> MissionWorkerReadModel:
    config = configuration or LocalMissionWorkerConfiguration()
    now = store.current_time()
    receipts = store.inspection_receipts()
    all_latest_jobs = sorted(
        store._latest_by_job(receipts).values(),  # noqa: SLF001
        key=lambda item: item.sequence,
    )
    active_jobs = [
        item
        for item in all_latest_jobs
        if item.status
        in {
            MissionWorkerJobStatus.pending.value,
            MissionWorkerJobStatus.claimed.value,
            MissionWorkerJobStatus.approval_wait.value,
            MissionWorkerJobStatus.retry_pending.value,
        }
    ]
    terminal_jobs = [item for item in all_latest_jobs if item not in active_jobs]
    terminal_slots = 32 - len(active_jobs)
    latest_jobs = [
        *active_jobs,
        *(terminal_jobs[-terminal_slots:] if terminal_slots else []),
    ]
    jobs: list[MissionWorkerJobReadModel] = []
    for latest in latest_jobs:
        job_history = [
            item for item in receipts if item.binding.job_ref == latest.binding.job_ref
        ]
        last_heartbeat = next(
            (
                item
                for item in reversed(job_history)
                if item.event == MissionWorkerEvent.heartbeat.value
            ),
            None,
        )
        step_models: list[MissionWorkerStepRecovery] = []
        for step_ref in latest.binding.ordered_step_refs:
            step_models.append(_step_recovery(orchestrator, step_ref, now))
        recovery = _job_recovery(latest, step_models, now)
        jobs.append(
            MissionWorkerJobReadModel(
                job_safe_ref=_identity_ref(
                    "mission-worker-job-safe-ref", latest.binding.job_ref
                ),
                plan_safe_ref=_identity_ref(
                    "mission-worker-plan-safe-ref", latest.binding.plan_ref
                ),
                mission_safe_ref=_identity_ref(
                    "mission-worker-mission-safe-ref", latest.binding.mission_ref
                ),
                run_safe_ref=_identity_ref(
                    "mission-worker-run-safe-ref", latest.binding.run_ref
                ),
                durable_status=latest.status,
                recovery_status=recovery,
                generation=latest.generation,
                latest_event=latest.event,
                latest_event_at=latest.checked_at,
                last_heartbeat_at=(
                    last_heartbeat.checked_at if last_heartbeat is not None else None
                ),
                heartbeat_freshness=(
                    "active"
                    if recovery == MissionWorkerRecoveryStatus.actively_claimed
                    else "stale"
                    if recovery == MissionWorkerRecoveryStatus.stale_claim
                    else "not_observed"
                ),
                worker_safe_ref=(
                    _identity_ref("mission-worker-safe-ref", latest.worker_ref)
                    if latest.worker_ref
                    else None
                ),
                claim_safe_ref=(
                    _identity_ref("mission-worker-claim-safe-ref", latest.claim_ref)
                    if latest.claim_ref
                    else None
                ),
                claim_expires_at=latest.claim_expires_at,
                deadline=latest.binding.deadline,
                steps=step_models,
                reason_refs=latest.reason_refs,
                evidence_refs=latest.evidence_refs,
            )
        )
    active = sum(
        item.status == MissionWorkerJobStatus.claimed.value
        and item.claim_expires_at is not None
        and item.claim_expires_at > now
        for item in latest_jobs
    )
    stale = sum(
        item.status == MissionWorkerJobStatus.claimed.value
        and item.claim_expires_at is not None
        and item.claim_expires_at <= now
        for item in latest_jobs
    )
    return MissionWorkerReadModel(
        inspection_ref=_safe_ref(
            "mission-worker-inspection-ref",
            {"receipts": [item.entry_hash_ref for item in receipts]},
        ),
        configuration_enabled=config.enabled,
        observed_platform=config.observed_platform,
        platform_execution_supported=(
            config.observed_platform == MissionWorkerPlatform.macos.value
        ),
        queue_capacity=config.queue_capacity,
        queued_job_count=sum(
            job.durable_status
            in {
                MissionWorkerJobStatus.pending.value,
                MissionWorkerJobStatus.claimed.value,
                MissionWorkerJobStatus.approval_wait.value,
                MissionWorkerJobStatus.retry_pending.value,
            }
            for job in jobs
        ),
        total_job_count=len(all_latest_jobs),
        omitted_terminal_job_count=len(all_latest_jobs) - len(latest_jobs),
        active_claim_count=active,
        stale_claim_count=stale,
        kill_switch_engaged=authority_lease_kill_switch_engaged(),
        jobs=jobs,
        checked_at=now,
        operator_summary=(
            "Local background mission execution is disabled by default and remains "
            "request-scoped; inspection never grants authority."
        ),
    )


def _step_recovery(
    orchestrator: SynchronousAuthorityMissionOrchestrator,
    step_ref: str,
    now: datetime,
) -> MissionWorkerStepRecovery:
    try:
        step = orchestrator.step_store.read(step_ref)
    except KeyError:
        return MissionWorkerStepRecovery(
            step_safe_ref=_identity_ref("mission-worker-step-safe-ref", step_ref),
            status=MissionWorkerRecoveryStatus.recovery_required,
            claim_freshness="unknown",
            generation=0,
            reason_refs=["reason-ref:mission-worker:step-materialization-missing"],
        )
    receipt = next(
        item
        for item in reversed(orchestrator.step_store.receipts())
        if item.definition.step_ref == step_ref
    )
    dispatch = None
    if receipt.dispatch_ref is not None:
        dispatch = next(
            (
                item
                for item in reversed(orchestrator.runner.dispatcher.list_receipts())
                if item.dispatch_ref == receipt.dispatch_ref
            ),
            None,
        )
    if dispatch is not None and dispatch.status in {
        AuthorityDispatchStatus.started.value,
        AuthorityDispatchStatus.cancellation_pending.value,
    }:
        status = MissionWorkerRecoveryStatus.started_unknown_terminal
    elif (
        dispatch is not None
        and dispatch.status == AuthorityDispatchStatus.prepared.value
    ):
        status = MissionWorkerRecoveryStatus.prepared_dispatch
    elif step.status == MissionStepStatus.succeeded.value:
        status = MissionWorkerRecoveryStatus.succeeded
    elif step.status == MissionStepStatus.dependency_blocked.value:
        status = MissionWorkerRecoveryStatus.dependency_blocked
    elif step.status == MissionStepStatus.recovery_required.value:
        status = MissionWorkerRecoveryStatus.recovery_required
    elif step.status == MissionStepStatus.approval_wait.value:
        status = MissionWorkerRecoveryStatus.approval_wait
    elif step.status == MissionStepStatus.retry_pending.value:
        status = MissionWorkerRecoveryStatus.retry_pending
    elif step.status in {
        MissionStepStatus.failed.value,
        MissionStepStatus.fail_fast_halted.value,
        MissionStepStatus.dead_lettered.value,
    }:
        status = MissionWorkerRecoveryStatus.failed
    elif step.status == MissionStepStatus.cancelled.value:
        status = MissionWorkerRecoveryStatus.cancelled
    elif (
        step.status == MissionStepStatus.claimed.value
        and step.claim_expires_at is not None
    ):
        status = (
            MissionWorkerRecoveryStatus.actively_claimed
            if step.claim_expires_at > now
            else MissionWorkerRecoveryStatus.stale_claim
        )
    else:
        status = MissionWorkerRecoveryStatus.pending
    if step.status != MissionStepStatus.claimed.value:
        freshness = "not_claimed"
    elif step.claim_expires_at is None:
        freshness = "unknown"
    elif step.claim_expires_at > now:
        freshness = "active"
    else:
        freshness = "stale"
    return MissionWorkerStepRecovery(
        step_safe_ref=_identity_ref("mission-worker-step-safe-ref", step_ref),
        status=status,
        claim_freshness=freshness,
        generation=step.generation,
        reason_refs=step.reason_refs,
        evidence_refs=step.evidence_refs,
    )


def _job_recovery(
    latest: MissionWorkerReceipt,
    steps: list[MissionWorkerStepRecovery],
    now: datetime,
) -> MissionWorkerRecoveryStatus:
    priority = [
        MissionWorkerRecoveryStatus.started_unknown_terminal,
        MissionWorkerRecoveryStatus.recovery_required,
        MissionWorkerRecoveryStatus.prepared_dispatch,
        MissionWorkerRecoveryStatus.dependency_blocked,
    ]
    statuses = {step.status for step in steps}
    for status in priority:
        if (
            status == MissionWorkerRecoveryStatus.recovery_required
            and latest.status == MissionWorkerJobStatus.failed.value
            and all(
                step.reason_refs
                == ["reason-ref:mission-worker:step-materialization-missing"]
                for step in steps
                if step.status == MissionWorkerRecoveryStatus.recovery_required.value
            )
        ):
            continue
        if status.value in statuses:
            return status
    if latest.status == MissionWorkerJobStatus.recovery_required.value:
        return MissionWorkerRecoveryStatus.recovery_required
    if latest.status == MissionWorkerJobStatus.approval_wait.value:
        return MissionWorkerRecoveryStatus.approval_wait
    if latest.status == MissionWorkerJobStatus.retry_pending.value:
        return MissionWorkerRecoveryStatus.retry_pending
    if latest.status == MissionWorkerJobStatus.failed.value:
        return MissionWorkerRecoveryStatus.failed
    if latest.status == MissionWorkerJobStatus.cancelled.value:
        return MissionWorkerRecoveryStatus.cancelled
    if latest.status == MissionWorkerJobStatus.succeeded.value and not all(
        step.status == MissionWorkerRecoveryStatus.succeeded.value for step in steps
    ):
        return MissionWorkerRecoveryStatus.recovery_required
    if MissionWorkerRecoveryStatus.failed.value in statuses:
        return MissionWorkerRecoveryStatus.failed
    if steps and all(
        step.status == MissionWorkerRecoveryStatus.succeeded.value for step in steps
    ):
        return MissionWorkerRecoveryStatus.succeeded
    if latest.status == MissionWorkerJobStatus.claimed.value:
        if latest.claim_expires_at is None:
            return MissionWorkerRecoveryStatus.recovery_required
        return (
            MissionWorkerRecoveryStatus.actively_claimed
            if latest.claim_expires_at > now
            else MissionWorkerRecoveryStatus.stale_claim
        )
    return MissionWorkerRecoveryStatus.pending


class LocalMissionWorker:
    """One local bounded worker; it never persists dispatch request payloads."""

    def __init__(
        self,
        *,
        orchestrator: SynchronousAuthorityMissionOrchestrator,
        store: MissionWorkerStore,
        control_store: MissionControlStore | None = None,
        configuration: LocalMissionWorkerConfiguration | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.store = store
        self.control_store = control_store or orchestrator.control_store
        self.store.bind_control_store(self.control_store)
        self.control_store.bind_request_validator(
            self._validate_control_request_locked
        )
        self.configuration = configuration or LocalMissionWorkerConfiguration()
        self._shutdown = threading.Event()
        if not (
            self.orchestrator.runner.dispatcher.state_dir.resolve()
            == self.orchestrator.step_store.state_dir.resolve()
            == self.store.state_dir.resolve()
            == self.control_store.state_dir.resolve()
        ):
            raise ValueError("MISSION_WORKER_SHARED_AUTHORITY_STATE_REQUIRED")
        validator = MissionWorkerExecutionFenceValidator(
            store=self.store,
            orchestrator=self.orchestrator,
            control_store=self.control_store,
        )
        existing = self.orchestrator.runner.dispatcher.execution_fence_validator
        if (
            existing is not None
            and type(existing)
            not in {
                MissionCancellationExecutionFenceValidator,
                MissionWorkerExecutionFenceValidator,
            }
        ):
            raise ValueError("MISSION_WORKER_EXECUTION_FENCE_ALREADY_BOUND")
        self.orchestrator.runner.dispatcher.execution_fence_validator = validator

    def _validate_control_request_locked(
        self,
        request: MissionControlRequest,
    ) -> None:
        self.orchestrator._validate_control_request_locked(request)  # noqa: SLF001
        matching_plans = [
            receipt
            for receipt in self.orchestrator.plan_store.list_receipts()
            if receipt.plan.plan_ref == request.plan_ref
        ]
        if len(matching_plans) != 1:
            raise MissionWorkerConflictError(
                "MISSION_CONTROL_ACCEPTED_PLAN_REQUIRED"
            )
        plan_receipt = matching_plans[0]
        if (
            plan_receipt.plan_fingerprint_ref != request.plan_fingerprint_ref
            or plan_receipt.plan.mission_ref != request.mission_ref
            or plan_receipt.plan.run_ref != request.run_ref
        ):
            raise MissionWorkerConflictError(
                "MISSION_CONTROL_ACCEPTED_PLAN_BINDING_INVALID"
            )
        matching_leases = [
            lease
            for lease in self.orchestrator.runner.dispatcher.lease_store._list_leases(  # noqa: SLF001
                active_only=True
            )
            if lease.lease_ref == request.lease_ref
        ]
        if (
            len(matching_leases) != 1
            or matching_leases[0].scope != AuthorityLeaseScope.mission.value
            or matching_leases[0].mission_ref != request.mission_ref
        ):
            raise MissionWorkerConflictError(
                "MISSION_CONTROL_ACTIVE_MISSION_LEASE_REQUIRED"
            )
        if request.event == MissionControlEvent.cancellation_requested.value:
            terminal_jobs = [
                job
                for job in self.store._latest_by_job(self.store._load()).values()  # noqa: SLF001
                if job.binding.plan_ref == request.plan_ref
                and job.status
                in {
                    MissionWorkerJobStatus.succeeded.value,
                    MissionWorkerJobStatus.failed.value,
                    MissionWorkerJobStatus.recovery_required.value,
                    MissionWorkerJobStatus.cancelled.value,
                }
            ]
            if terminal_jobs:
                raise MissionWorkerConflictError(
                    "MISSION_CONTROL_MISSION_ALREADY_TERMINAL"
                )

    def request_shutdown(self) -> None:
        self._shutdown.set()

    def enqueue(
        self,
        request: AuthorityMissionOrchestrationRequest,
    ) -> MissionWorkerReceipt:
        if not self.configuration.enabled:
            raise MissionWorkerDisabledError("MISSION_WORKER_DISABLED_BY_DEFAULT")
        validated = AuthorityMissionOrchestrationRequest.model_validate(
            request.model_dump(mode="python")
        )
        binding = mission_worker_job_binding(validated)
        with (
            self.store.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.store.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
        ):
            receipts = self.store._load()  # noqa: SLF001
            existing = self.store._preflight_enqueue_loaded(  # noqa: SLF001
                receipts,
                binding,
                queue_capacity=self.configuration.queue_capacity,
            )
            if existing is not None:
                return existing
            self.orchestrator.materialize(validated)
            return self.store._append_enqueue_loaded(  # noqa: SLF001
                receipts,
                binding,
            )

    def resume_next(
        self,
        resolver: MissionWorkerRequestResolver,
        *,
        worker_ref: str,
    ) -> AuthorityMissionOrchestrationResult | None:
        now = self.store.current_time()
        candidates = [
            item
            for item in self.store.latest()
            if item.status
            in {
                MissionWorkerJobStatus.pending.value,
                MissionWorkerJobStatus.approval_wait.value,
            }
            or (
                item.status == MissionWorkerJobStatus.retry_pending.value
                and item.retry_not_before is not None
                and item.retry_not_before <= now
            )
            or (
                item.status == MissionWorkerJobStatus.claimed.value
                and item.claim_expires_at is not None
                and item.claim_expires_at <= now
            )
        ]
        if not candidates:
            return None
        for selected in sorted(candidates, key=lambda item: item.sequence):
            request = resolver.resolve(selected.binding)
            if request is None:
                continue
            validated = AuthorityMissionOrchestrationRequest.model_validate(
                request.model_dump(mode="python")
            )
            if mission_worker_job_binding(validated) != selected.binding:
                raise MissionWorkerConflictError(
                    "MISSION_WORKER_REQUEST_RESOLVER_FINGERPRINT_MISMATCH"
                )
            if selected.status == MissionWorkerJobStatus.approval_wait.value:
                waiting_steps = [
                    step
                    for step in validated.steps
                    if self.orchestrator.step_store.read(
                        step.definition.step_ref
                    ).status
                    == MissionStepStatus.approval_wait.value
                ]
                if waiting_steps and all(
                    step.definition.deadline
                    > self.orchestrator.step_store.current_time()
                    and self.orchestrator.runner.evaluate_approval_posture(
                        step.request
                    ).posture
                    == "wait"
                    for step in waiting_steps
                ):
                    continue
            return self.run_once(validated, worker_ref=worker_ref)
        return None

    def run_once(
        self,
        request: AuthorityMissionOrchestrationRequest,
        *,
        worker_ref: str,
    ) -> AuthorityMissionOrchestrationResult | None:
        if not self.configuration.enabled:
            raise MissionWorkerDisabledError("MISSION_WORKER_DISABLED_BY_DEFAULT")
        if self.configuration.observed_platform != MissionWorkerPlatform.macos.value:
            raise MissionWorkerDisabledError("MISSION_WORKER_MACOS_PLATFORM_REQUIRED")
        validate_task_ref(worker_ref, "mission_worker_ref")
        durable_worker_ref = mission_worker_identity_ref(worker_ref)
        request = AuthorityMissionOrchestrationRequest.model_validate(
            request.model_dump(mode="python")
        )
        if self._shutdown.is_set() or authority_lease_kill_switch_engaged():
            return None
        bound = {
            step.definition.step_ref: request.bound_definition(step)
            for step in request.steps
        }
        self.orchestrator._preflight(request, bound)  # noqa: SLF001
        binding = mission_worker_job_binding(request)
        enqueued = self.enqueue(request)
        if enqueued.status == MissionWorkerJobStatus.approval_wait.value:
            waiting_steps = [
                step
                for step in request.steps
                if self.orchestrator.step_store.read(
                    step.definition.step_ref
                ).status
                == MissionStepStatus.approval_wait.value
            ]
            if waiting_steps and all(
                step.definition.deadline
                > self.orchestrator.step_store.current_time()
                and self.orchestrator.runner.evaluate_approval_posture(
                    step.request
                ).posture
                == "wait"
                for step in waiting_steps
            ):
                return None
        if (
            enqueued.status == MissionWorkerJobStatus.retry_pending.value
            and enqueued.retry_not_before is not None
            and enqueued.retry_not_before > self.store.current_time()
        ):
            return None
        claim = self.store.claim(
            binding.job_ref,
            worker_ref=durable_worker_ref,
            ttl_seconds=self.configuration.claim_ttl_seconds,
        )
        if claim.status != MissionWorkerJobStatus.claimed.value:
            if (
                claim.status == MissionWorkerJobStatus.failed.value
                and claim.reason_refs
                == ["reason-ref:mission-worker:deadline-expired"]
            ):
                return self.orchestrator.run(
                    request,
                    owner_ref=durable_worker_ref,
                    claim_ttl_seconds=self.configuration.claim_ttl_seconds,
                    max_step_count=1,
                    heartbeat_interval_seconds=None,
                    worker_claim_fence=None,
                )
            return None
        worker_claim_fence = AuthorityDispatchWorkerClaimFence(
            job_ref=binding.job_ref,
            worker_ref=durable_worker_ref,
            job_claim_ref=claim.claim_ref or "",
            job_generation=claim.generation,
        )
        if self._shutdown.is_set():
            self.store.record_shutdown(
                binding.job_ref,
                worker_ref=durable_worker_ref,
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
            )
            return None
        if authority_lease_kill_switch_engaged():
            self.store.record_shutdown(
                binding.job_ref,
                worker_ref=durable_worker_ref,
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
            )
            return None
        stop_heartbeat = threading.Event()
        heartbeat_error: list[BaseException] = []

        def renew() -> None:
            while not stop_heartbeat.wait(
                self.configuration.heartbeat_interval_seconds
            ):
                try:
                    self.store.heartbeat(
                        binding.job_ref,
                        worker_ref=durable_worker_ref,
                        claim_ref=claim.claim_ref or "",
                        generation=claim.generation,
                        ttl_seconds=self.configuration.claim_ttl_seconds,
                    )
                except BaseException as exc:  # pragma: no cover - asserted after join
                    heartbeat_error.append(exc)
                    return

        thread = threading.Thread(
            target=renew,
            name="uaa-local-mission-heartbeat",
            daemon=True,
        )
        thread.start()
        result: AuthorityMissionOrchestrationResult | None = None
        try:
            while True:
                result = self.orchestrator.run(
                    request,
                    owner_ref=durable_worker_ref,
                    claim_ttl_seconds=self.configuration.claim_ttl_seconds,
                    max_step_count=1,
                    heartbeat_interval_seconds=(
                        self.configuration.heartbeat_interval_seconds
                    ),
                    worker_claim_fence=worker_claim_fence,
                )
                if result.status != "in_progress":
                    break
                if self._shutdown.is_set() or authority_lease_kill_switch_engaged():
                    self.store.record_shutdown(
                        binding.job_ref,
                        worker_ref=durable_worker_ref,
                        claim_ref=claim.claim_ref or "",
                        generation=claim.generation,
                    )
                    return result
                self.orchestrator._preflight(request, bound)  # noqa: SLF001
        finally:
            stop_heartbeat.set()
            thread.join(timeout=self.configuration.heartbeat_interval_seconds + 1)
        if heartbeat_error:
            raise MissionWorkerConflictError(
                "MISSION_WORKER_HEARTBEAT_FAILED"
            ) from heartbeat_error[0]
        assert result is not None
        if result.status == "waiting_for_approval":
            self.store.defer_for_approval(
                binding.job_ref,
                worker_ref=durable_worker_ref,
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
                reason_refs=result.reason_refs,
                evidence_refs=result.evidence_refs,
            )
            return result
        if result.status == "waiting_for_retry":
            retry_times = [
                step.retry_not_before
                for step in result.steps
                if step.status == MissionStepStatus.retry_pending.value
                and step.retry_not_before is not None
            ]
            if len(retry_times) != 1:
                raise MissionWorkerConflictError(
                    "MISSION_WORKER_RETRY_TIME_BINDING_INVALID"
                )
            self.store.defer_for_retry(
                binding.job_ref,
                worker_ref=durable_worker_ref,
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
                retry_not_before=retry_times[0],
                reason_refs=result.reason_refs,
                evidence_refs=result.evidence_refs,
            )
            return result
        status = {
            "succeeded": MissionWorkerJobStatus.succeeded,
            "failed": MissionWorkerJobStatus.failed,
            "recovery_required": MissionWorkerJobStatus.recovery_required,
            "in_progress": MissionWorkerJobStatus.recovery_required,
        }[result.status]
        completed = self.store.complete(
            binding.job_ref,
            worker_ref=durable_worker_ref,
            claim_ref=claim.claim_ref or "",
            generation=claim.generation,
            status=status,
            reason_refs=result.reason_refs,
            evidence_refs=result.evidence_refs,
            execution_started=result.started_step_count > 0,
        )
        if completed.status != status.value:
            result = result.model_copy(
                update={
                    "status": (
                        "recovery_required"
                        if completed.status
                        == MissionWorkerJobStatus.recovery_required.value
                        else "failed"
                    ),
                    "reason_refs": completed.reason_refs,
                    "evidence_refs": completed.evidence_refs,
                    "mission_cancellation_claimed": True,
                }
            )
        return result


class MissionWorkerExecutionFenceValidator:
    """Consumes queue and step ownership inside the dispatcher's start lock."""

    def __init__(
        self,
        *,
        store: MissionWorkerStore,
        orchestrator: SynchronousAuthorityMissionOrchestrator,
        control_store: MissionControlStore,
    ) -> None:
        self.store = store
        self.orchestrator = orchestrator
        self.control_store = control_store

    def validate_prestart_fence(
        self,
        request: Any,
        execution_fence: AuthorityDispatchExecutionFence | None,
        *,
        current_time: Callable[[], datetime],
    ) -> tuple[list[str], str | None, datetime]:
        fingerprint = authority_dispatch_request_fingerprint(request)
        with self.control_store.lock_manager.acquire(MISSION_CONTROL_LOCK_KEY):
            control_receipts = self.control_store._load()  # noqa: SLF001
            with (
                self.store.lock_manager.acquire(MISSION_WORKER_LOCK_KEY),
                self.orchestrator.step_store.lock_manager.acquire(
                    "authority-mission-steps"
                ),
            ):
                admission_time = current_time()
                if admission_time.tzinfo is None:
                    raise ValueError("AUTHORITY_DISPATCH_ADMISSION_TIMEZONE_REQUIRED")
                matches = [
                    item
                    for item in self.store._latest_by_job(self.store._load()).values()  # noqa: SLF001
                    if fingerprint in item.binding.dispatch_request_fingerprint_refs
                ]
                if not matches:
                    if execution_fence is not None:
                        return (
                            ["reason-ref:authority-dispatch:worker-fence-unbound"],
                            None,
                            admission_time,
                        )
                    return [], None, admission_time
                if len(matches) != 1:
                    return (
                        ["reason-ref:authority-dispatch:worker-fence-ambiguous"],
                        None,
                        admission_time,
                    )
                job = matches[0]
                cancellation = self.control_store._cancellation_for_loaded(  # noqa: SLF001
                    control_receipts,
                    plan_ref=job.binding.plan_ref,
                    plan_fingerprint_ref=job.binding.plan_fingerprint_ref,
                    mission_ref=job.binding.mission_ref,
                    run_ref=job.binding.run_ref,
                )
                if cancellation is not None:
                    return (
                        [
                            "reason-ref:authority-dispatch:mission-cancellation-fenced"
                        ],
                        cancellation.receipt_ref,
                        admission_time,
                    )
                if (
                    execution_fence is None
                    or execution_fence.job_ref != job.binding.job_ref
                    or execution_fence.worker_ref != job.worker_ref
                    or execution_fence.job_claim_ref != job.claim_ref
                    or execution_fence.job_generation != job.generation
                    or job.status != MissionWorkerJobStatus.claimed.value
                    or job.claim_expires_at is None
                    or job.claim_expires_at <= admission_time
                    or job.worker_ref is None
                    or job.claim_ref is None
                ):
                    return (
                        ["reason-ref:authority-dispatch:worker-fence-inactive"],
                        None,
                        admission_time,
                    )
                step_receipts = self.orchestrator.step_store._load()  # noqa: SLF001
                step = next(
                    (
                        item
                        for item in reversed(step_receipts)
                        if item.dispatch_ref == request.dispatch_ref
                    ),
                    None,
                )
                if (
                    step is None
                    or execution_fence.step_ref != step.definition.step_ref
                    or execution_fence.step_claim_ref != step.claim_ref
                    or execution_fence.step_generation != step.generation
                    or step.status != MissionStepStatus.claimed.value
                    or step.owner_ref != job.worker_ref
                    or step.claim_expires_at is None
                    or step.claim_expires_at <= admission_time
                    or step.claim_ref is None
                ):
                    return (
                        ["reason-ref:authority-dispatch:mission-step-fence-inactive"],
                        None,
                        admission_time,
                    )
                fence_ref = _safe_ref(
                    "authority-dispatch-execution-fence-ref",
                    {
                        "job_ref": job.binding.job_ref,
                        "job_claim_ref": job.claim_ref,
                        "job_generation": job.generation,
                        "step_ref": step.definition.step_ref,
                        "step_claim_ref": step.claim_ref,
                        "step_generation": step.generation,
                        "request_fingerprint_ref": fingerprint,
                    },
                )
                return [], fence_ref, admission_time
