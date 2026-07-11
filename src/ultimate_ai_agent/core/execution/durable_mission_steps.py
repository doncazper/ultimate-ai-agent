from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.authority.contracts import authority_state_lock_manager
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchReceipt,
    AuthorityDispatchStatus,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.time import utc_now


MISSION_STEP_SCHEMA_VERSION = "uaa-mission-step.v1"
MISSION_STEP_LEDGER_FILE = "mission_step_receipts.jsonl"
MISSION_STEP_LOCK_KEY = "authority-mission-steps"
MISSION_STEP_LEDGER_MAX_BYTES = 8 * 1024 * 1024
MISSION_STEP_LEDGER_MAX_RECEIPTS = 10_000


class MissionStepError(RuntimeError):
    pass


class MissionStepConflictError(MissionStepError):
    pass


class MissionStepCorruptionError(MissionStepError):
    pass


class MissionStepStatus(str, Enum):
    pending = "pending"
    claimed = "claimed"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    recovery_required = "recovery_required"


TERMINAL_MISSION_STEP_STATUSES = {
    MissionStepStatus.succeeded.value,
    MissionStepStatus.failed.value,
    MissionStepStatus.cancelled.value,
    MissionStepStatus.recovery_required.value,
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _safe_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))[:24]}"


class _MissionStepModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class MissionStepDefinition(_MissionStepModel):
    schema_version: Literal["uaa-mission-step.v1"] = MISSION_STEP_SCHEMA_VERSION
    mission_ref: str
    run_ref: str
    step_ref: str
    capability_ref: str
    adapter_ref: str
    lease_ref: str
    dependency_step_refs: list[str] = Field(default_factory=list)
    max_attempts: Literal[1] = 1
    deadline: datetime
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_definition(self) -> "MissionStepDefinition":
        for value, name in [
            (self.mission_ref, "mission_ref"),
            (self.run_ref, "run_ref"),
            (self.step_ref, "step_ref"),
            (self.capability_ref, "capability_ref"),
            (self.adapter_ref, "adapter_ref"),
            (self.lease_ref, "lease_ref"),
            *[(ref, "dependency_step_ref") for ref in self.dependency_step_refs],
        ]:
            validate_task_ref(value, name)
        if self.step_ref in self.dependency_step_refs:
            raise ValueError("MISSION_STEP_SELF_DEPENDENCY_DENIED")
        if len(self.dependency_step_refs) != len(set(self.dependency_step_refs)):
            raise ValueError("MISSION_STEP_DUPLICATE_DEPENDENCY_DENIED")
        if self.deadline.tzinfo is None:
            raise ValueError("MISSION_STEP_DEADLINE_TIMEZONE_REQUIRED")
        validate_safe_task_text(self.safe_summary, "mission_step_safe_summary")
        return self

    @property
    def fingerprint_ref(self) -> str:
        return _safe_ref("mission-step-fingerprint-ref", self.model_dump(mode="json"))


class MissionStepReceipt(_MissionStepModel):
    schema_version: Literal["uaa-mission-step.v1"] = MISSION_STEP_SCHEMA_VERSION
    sequence: StrictInt = Field(..., ge=1)
    receipt_ref: str
    entry_hash_ref: str
    previous_entry_hash_ref: str | None = None
    definition: MissionStepDefinition
    definition_fingerprint_ref: str
    status: MissionStepStatus
    generation: StrictInt = Field(default=0, ge=0)
    attempt_no: Literal[1] = 1
    owner_ref: str | None = None
    claim_ref: str | None = None
    claim_expires_at: datetime | None = None
    dispatch_ref: str | None = None
    dispatch_request_fingerprint_ref: str | None = None
    dispatch_receipt_ref: str | None = None
    dispatch_entry_hash_ref: str | None = None
    reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=utc_now)
    safe_summary: str = Field(..., min_length=1, max_length=320)

    @model_validator(mode="after")
    def validate_receipt(self) -> "MissionStepReceipt":
        for value, name in [
            (self.receipt_ref, "mission_step_receipt_ref"),
            (self.entry_hash_ref, "mission_step_entry_hash_ref"),
            (self.previous_entry_hash_ref, "mission_step_previous_hash_ref"),
            (self.definition_fingerprint_ref, "mission_step_fingerprint_ref"),
            (self.owner_ref, "mission_step_owner_ref"),
            (self.claim_ref, "mission_step_claim_ref"),
            (self.dispatch_ref, "mission_step_dispatch_ref"),
            (
                self.dispatch_request_fingerprint_ref,
                "mission_step_dispatch_request_fingerprint_ref",
            ),
            (self.dispatch_receipt_ref, "mission_step_dispatch_receipt_ref"),
            (self.dispatch_entry_hash_ref, "mission_step_dispatch_entry_hash_ref"),
            *[(ref, "mission_step_reason_ref") for ref in self.reason_refs],
            *[(ref, "mission_step_evidence_ref") for ref in self.evidence_refs],
        ]:
            if value is not None:
                validate_task_ref(value, name)
        validate_safe_task_text(self.safe_summary, "mission_step_safe_summary")
        claimed = self.status == MissionStepStatus.claimed.value
        if claimed != bool(self.owner_ref and self.claim_ref and self.claim_expires_at):
            raise ValueError("MISSION_STEP_CLAIM_POSTURE_INVALID")
        if self.status in TERMINAL_MISSION_STEP_STATUSES and not self.reason_refs:
            raise ValueError("MISSION_STEP_TERMINAL_REASON_REQUIRED")
        if self.definition_fingerprint_ref != self.definition.fingerprint_ref:
            raise ValueError("MISSION_STEP_DEFINITION_FINGERPRINT_INVALID")
        return self


class MissionStepReadModel(_MissionStepModel):
    step_ref: str
    status: MissionStepStatus
    generation: StrictInt
    attempt_no: Literal[1]
    owner_ref: str | None
    claim_ref: str | None
    claim_expires_at: datetime | None
    dispatch_ref: str | None
    dispatch_request_fingerprint_ref: str | None
    dispatch_receipt_ref: str | None
    dispatch_entry_hash_ref: str | None
    reason_refs: list[str]
    evidence_refs: list[str]
    receipt_ref: str
    execution_authority_granted: Literal[False] = False
    autonomous_retry_enabled: Literal[False] = False


class _MissionStepInspectionSource(_MissionStepModel):
    mission_ref: str
    run_ref: str
    step_ref: str
    capability_ref: str
    adapter_ref: str
    lease_ref: str
    dependency_step_refs: list[str]
    deadline: datetime
    status: MissionStepStatus
    generation: StrictInt
    attempt_no: Literal[1]
    owner_ref: str | None
    claim_ref: str | None
    claim_expires_at: datetime | None
    dispatch_ref: str | None
    dispatch_request_fingerprint_ref: str | None
    dispatch_receipt_ref: str | None
    reason_refs: list[str]
    evidence_refs: list[str]
    receipt_ref: str
    checked_at: datetime


def _entry_hash(receipt: MissionStepReceipt) -> str:
    return _safe_ref(
        "mission-step-entry-hash-ref",
        receipt.model_dump(mode="json", exclude={"entry_hash_ref"}),
    )


DispatchReceiptResolver = Callable[[str], AuthorityDispatchReceipt | None]


class MissionStepStore:
    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.state_dir = state_dir
        self.receipts_path = state_dir / MISSION_STEP_LEDGER_FILE
        self.lock_manager = authority_state_lock_manager(str(state_dir.resolve()))
        self._clock = clock
        self._dispatch_receipt_resolver: DispatchReceiptResolver | None = None

    def current_time(self) -> datetime:
        current = self._clock()
        if current.tzinfo is None:
            raise ValueError("MISSION_STEP_TRUSTED_CLOCK_TIMEZONE_REQUIRED")
        return current

    def _bind_dispatch_receipt_resolver(
        self,
        resolver: DispatchReceiptResolver,
    ) -> None:
        if self._dispatch_receipt_resolver is not None:
            raise ValueError("MISSION_STEP_DISPATCH_RESOLVER_ALREADY_BOUND")
        self._dispatch_receipt_resolver = resolver

    def create(self, definition: MissionStepDefinition) -> MissionStepReceipt:
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            existing = self._latest(receipts, definition.step_ref)
            if existing is not None:
                if existing.definition_fingerprint_ref != definition.fingerprint_ref:
                    raise MissionStepConflictError("MISSION_STEP_DEFINITION_CONFLICT")
                return existing
            receipt = self._build(
                receipts,
                definition=definition,
                status=MissionStepStatus.pending,
                generation=0,
                checked_at=self.current_time(),
                safe_summary="Mission step is pending a fenced owner claim.",
            )
            self._append(receipt)
            return receipt

    def claim(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        ttl_seconds: int,
        dispatch_ref: str | None = None,
        dispatch_request_fingerprint_ref: str | None = None,
    ) -> MissionStepReceipt:
        validate_task_ref(owner_ref, "mission_step_owner_ref")
        if (dispatch_ref is None) != (dispatch_request_fingerprint_ref is None):
            raise ValueError("MISSION_STEP_DISPATCH_INTENT_INCOMPLETE")
        if dispatch_ref is not None:
            validate_task_ref(dispatch_ref, "mission_step_dispatch_ref")
            validate_task_ref(
                dispatch_request_fingerprint_ref or "",
                "mission_step_dispatch_request_fingerprint_ref",
            )
        self._validate_ttl(ttl_seconds)
        current = self.current_time()
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.definition.deadline <= current:
                if latest.dispatch_ref is not None:
                    durable = (
                        self._dispatch_receipt_resolver(latest.dispatch_ref)
                        if self._dispatch_receipt_resolver is not None
                        else None
                    )
                    if durable is not None:
                        durable = self._validate_durable_dispatch(latest, durable)
                        if durable.status == AuthorityDispatchStatus.prepared.value:
                            raise MissionStepConflictError(
                                "MISSION_STEP_PREPARED_DEADLINE_EXPIRED"
                            )
                        status, reason_ref = self._expired_dispatch_posture(durable)
                        bind_terminal = status != MissionStepStatus.recovery_required
                        receipt = self._build_from(
                            receipts,
                            latest,
                            status=status,
                            generation=latest.generation,
                            dispatch_ref=latest.dispatch_ref,
                            dispatch_request_fingerprint_ref=(
                                latest.dispatch_request_fingerprint_ref
                            ),
                            dispatch_receipt_ref=(
                                durable.receipt_ref if bind_terminal else None
                            ),
                            dispatch_entry_hash_ref=(
                                durable.entry_hash_ref if bind_terminal else None
                            ),
                            reason_refs=[reason_ref, *durable.reason_refs],
                            evidence_refs=self._dispatch_evidence_refs(durable),
                            checked_at=current,
                            safe_summary=(
                                "Mission step reconciled durable dispatch truth "
                                "after deadline."
                            ),
                        )
                        self._append(receipt)
                        return receipt
                    return self._terminal_locked(
                        receipts,
                        latest,
                        MissionStepStatus.recovery_required,
                        reason_ref=(
                            "reason-ref:mission-step:deadline-expired-dispatch-unresolved"
                        ),
                        safe_summary=(
                            "Mission step deadline expired with unresolved dispatch truth."
                        ),
                        checked_at=current,
                    )
                return self._terminal_locked(
                    receipts,
                    latest,
                    MissionStepStatus.failed,
                    reason_ref="reason-ref:mission-step:deadline-expired",
                    safe_summary="Mission step deadline expired before claim.",
                    checked_at=current,
                )
            if latest.dispatch_ref is not None and (
                dispatch_ref != latest.dispatch_ref
                or dispatch_request_fingerprint_ref
                != latest.dispatch_request_fingerprint_ref
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_DISPATCH_FINGERPRINT_CONFLICT"
                )
            if (
                latest.status == MissionStepStatus.claimed.value
                and latest.claim_expires_at is not None
                and latest.claim_expires_at > current
            ):
                raise MissionStepConflictError("MISSION_STEP_ALREADY_CLAIMED")
            for dependency in latest.definition.dependency_step_refs:
                dep = self._latest(receipts, dependency)
                if (
                    dep is None
                    or dep.status != MissionStepStatus.succeeded.value
                    or dep.definition.mission_ref != latest.definition.mission_ref
                    or dep.definition.run_ref != latest.definition.run_ref
                ):
                    raise MissionStepConflictError("MISSION_STEP_DEPENDENCY_NOT_READY")
            generation = latest.generation + 1
            claim_ref = _safe_ref(
                "mission-step-claim-ref",
                {
                    "step_ref": step_ref,
                    "owner_ref": owner_ref,
                    "generation": generation,
                },
            )
            expires = min(
                current + timedelta(seconds=ttl_seconds),
                latest.definition.deadline,
            )
            bound_dispatch_ref = latest.dispatch_ref or dispatch_ref
            bound_fingerprint_ref = (
                latest.dispatch_request_fingerprint_ref
                or dispatch_request_fingerprint_ref
            )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.claimed,
                generation=generation,
                owner_ref=owner_ref,
                claim_ref=claim_ref,
                claim_expires_at=expires,
                dispatch_ref=bound_dispatch_ref,
                dispatch_request_fingerprint_ref=bound_fingerprint_ref,
                checked_at=current,
                safe_summary="Mission step ownership was fenced and claimed.",
            )
            self._append(receipt)
            return receipt

    def heartbeat(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        ttl_seconds: int,
    ) -> MissionStepReceipt:
        self._validate_ttl(ttl_seconds)
        current = self.current_time()
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            expires = min(
                current + timedelta(seconds=ttl_seconds),
                latest.definition.deadline,
            )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.claimed,
                generation=generation,
                owner_ref=owner_ref,
                claim_ref=claim_ref,
                claim_expires_at=expires,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                checked_at=current,
                safe_summary="Mission step owner heartbeat renewed the fenced claim.",
            )
            self._append(receipt)
            return receipt

    def record_dispatch_intent(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        dispatch_ref: str,
        dispatch_request_fingerprint_ref: str,
    ) -> MissionStepReceipt:
        validate_task_ref(dispatch_ref, "mission_step_dispatch_ref")
        validate_task_ref(
            dispatch_request_fingerprint_ref,
            "mission_step_dispatch_request_fingerprint_ref",
        )
        current = self.current_time()
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            if latest.dispatch_ref is not None and latest.dispatch_ref != dispatch_ref:
                raise MissionStepConflictError("MISSION_STEP_DISPATCH_INTENT_CONFLICT")
            if (
                latest.dispatch_request_fingerprint_ref is not None
                and latest.dispatch_request_fingerprint_ref
                != dispatch_request_fingerprint_ref
            ):
                raise MissionStepConflictError(
                    "MISSION_STEP_DISPATCH_FINGERPRINT_CONFLICT"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.claimed,
                generation=generation,
                owner_ref=owner_ref,
                claim_ref=claim_ref,
                claim_expires_at=latest.claim_expires_at,
                dispatch_ref=dispatch_ref,
                dispatch_request_fingerprint_ref=dispatch_request_fingerprint_ref,
                checked_at=current,
                safe_summary="Mission step recorded one immutable dispatch intent.",
            )
            self._append(receipt)
            return receipt

    def complete(
        self,
        step_ref: str,
        *,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        status: MissionStepStatus,
        reason_refs: list[str],
        evidence_refs: list[str] | None = None,
        dispatch_receipt: AuthorityDispatchReceipt | None = None,
    ) -> MissionStepReceipt:
        if status.value not in TERMINAL_MISSION_STEP_STATUSES:
            raise ValueError("MISSION_STEP_TERMINAL_STATUS_REQUIRED")
        current = self.current_time()
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            latest = self._require_owned(
                receipts, step_ref, owner_ref, claim_ref, generation, current
            )
            dispatch_receipt_ref = None
            dispatch_entry_hash_ref = None
            if status == MissionStepStatus.succeeded:
                dispatch_receipt = self._validate_succeeded_dispatch(
                    latest,
                    dispatch_receipt,
                )
                dispatch_receipt_ref = dispatch_receipt.receipt_ref
                dispatch_entry_hash_ref = dispatch_receipt.entry_hash_ref
            receipt = self._build_from(
                receipts,
                latest,
                status=status,
                generation=generation,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                dispatch_receipt_ref=dispatch_receipt_ref,
                dispatch_entry_hash_ref=dispatch_entry_hash_ref,
                reason_refs=reason_refs,
                evidence_refs=evidence_refs or [],
                checked_at=current,
                safe_summary="Mission step reached a durable terminal posture.",
            )
            self._append(receipt)
            return receipt

    def expire_deadline(
        self,
        step_ref: str,
        *,
        evidence_refs: list[str] | None = None,
    ) -> MissionStepReceipt:
        current = self.current_time()
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.definition.deadline > current:
                raise MissionStepConflictError("MISSION_STEP_DEADLINE_NOT_EXPIRED")
            if latest.dispatch_ref is not None:
                raise MissionStepConflictError(
                    "MISSION_STEP_DEADLINE_DISPATCH_RECONCILIATION_REQUIRED"
                )
            receipt = self._build_from(
                receipts,
                latest,
                status=MissionStepStatus.failed,
                generation=latest.generation,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                reason_refs=["reason-ref:mission-step:deadline-expired"],
                evidence_refs=evidence_refs or [],
                checked_at=current,
                safe_summary="Mission step deadline expired before dispatch start.",
            )
            self._append(receipt)
            return receipt

    def reconcile_expired_dispatch(
        self,
        step_ref: str,
        *,
        dispatch_receipt: AuthorityDispatchReceipt,
        evidence_refs: list[str],
    ) -> MissionStepReceipt:
        current = self.current_time()
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            receipts = self._load()
            latest = self._require_latest(receipts, step_ref)
            if latest.status in TERMINAL_MISSION_STEP_STATUSES:
                return latest
            if latest.definition.deadline > current:
                raise MissionStepConflictError("MISSION_STEP_DEADLINE_NOT_EXPIRED")
            durable = self._validate_durable_dispatch(latest, dispatch_receipt)
            status, reason_ref = self._expired_dispatch_posture(durable)
            bind_terminal = status != MissionStepStatus.recovery_required
            receipt = self._build_from(
                receipts,
                latest,
                status=status,
                generation=latest.generation,
                dispatch_ref=latest.dispatch_ref,
                dispatch_request_fingerprint_ref=(
                    latest.dispatch_request_fingerprint_ref
                ),
                dispatch_receipt_ref=(durable.receipt_ref if bind_terminal else None),
                dispatch_entry_hash_ref=(
                    durable.entry_hash_ref if bind_terminal else None
                ),
                reason_refs=[reason_ref, *durable.reason_refs],
                evidence_refs=evidence_refs,
                checked_at=current,
                safe_summary=(
                    "Mission step reconciled durable dispatch truth after deadline."
                ),
            )
            self._append(receipt)
            return receipt

    def read(self, step_ref: str) -> MissionStepReadModel:
        validate_task_ref(step_ref, "mission_step_ref")
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            latest = self._require_latest(self._load(), step_ref)
        return MissionStepReadModel(
            step_ref=latest.definition.step_ref,
            status=latest.status,
            generation=latest.generation,
            attempt_no=latest.attempt_no,
            owner_ref=latest.owner_ref,
            claim_ref=latest.claim_ref,
            claim_expires_at=latest.claim_expires_at,
            dispatch_ref=latest.dispatch_ref,
            dispatch_request_fingerprint_ref=(latest.dispatch_request_fingerprint_ref),
            dispatch_receipt_ref=latest.dispatch_receipt_ref,
            dispatch_entry_hash_ref=latest.dispatch_entry_hash_ref,
            reason_refs=latest.reason_refs,
            evidence_refs=latest.evidence_refs,
            receipt_ref=latest.receipt_ref,
        )

    def _read_inspection_source(self, step_ref: str) -> _MissionStepInspectionSource:
        validate_task_ref(step_ref, "mission_step_ref")
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            latest = self._require_latest(self._load(), step_ref)
        return _MissionStepInspectionSource(
            mission_ref=latest.definition.mission_ref,
            run_ref=latest.definition.run_ref,
            step_ref=latest.definition.step_ref,
            capability_ref=latest.definition.capability_ref,
            adapter_ref=latest.definition.adapter_ref,
            lease_ref=latest.definition.lease_ref,
            dependency_step_refs=list(latest.definition.dependency_step_refs),
            deadline=latest.definition.deadline,
            status=latest.status,
            generation=latest.generation,
            attempt_no=latest.attempt_no,
            owner_ref=latest.owner_ref,
            claim_ref=latest.claim_ref,
            claim_expires_at=latest.claim_expires_at,
            dispatch_ref=latest.dispatch_ref,
            dispatch_request_fingerprint_ref=(latest.dispatch_request_fingerprint_ref),
            dispatch_receipt_ref=latest.dispatch_receipt_ref,
            reason_refs=list(latest.reason_refs),
            evidence_refs=list(latest.evidence_refs),
            receipt_ref=latest.receipt_ref,
            checked_at=latest.checked_at,
        )

    def receipts(self) -> list[MissionStepReceipt]:
        with self.lock_manager.acquire(MISSION_STEP_LOCK_KEY):
            return self._load()

    def _terminal_locked(
        self,
        receipts: list[MissionStepReceipt],
        latest: MissionStepReceipt,
        status: MissionStepStatus,
        *,
        reason_ref: str,
        safe_summary: str,
        checked_at: datetime,
    ) -> MissionStepReceipt:
        receipt = self._build_from(
            receipts,
            latest,
            status=status,
            generation=latest.generation,
            dispatch_ref=latest.dispatch_ref,
            dispatch_request_fingerprint_ref=(latest.dispatch_request_fingerprint_ref),
            reason_refs=[reason_ref],
            checked_at=checked_at,
            safe_summary=safe_summary,
        )
        self._append(receipt)
        return receipt

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> None:
        if ttl_seconds < 1 or ttl_seconds > 300:
            raise ValueError("MISSION_STEP_CLAIM_TTL_INVALID")

    def _validate_succeeded_dispatch(
        self,
        latest: MissionStepReceipt,
        supplied: AuthorityDispatchReceipt | None,
    ) -> AuthorityDispatchReceipt:
        if supplied is None:
            raise MissionStepConflictError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_EVIDENCE_REQUIRED"
            )
        durable = self._validate_durable_dispatch(latest, supplied)
        if (
            durable.status != AuthorityDispatchStatus.succeeded.value
            or not durable.execution_started
            or not durable.adapter_invocation_performed
            or durable.budget_settlement_receipt_ref is None
        ):
            raise MissionStepConflictError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_BINDING_INVALID"
            )
        return durable

    def _validate_durable_dispatch(
        self,
        latest: MissionStepReceipt,
        supplied: AuthorityDispatchReceipt,
    ) -> AuthorityDispatchReceipt:
        if (
            latest.dispatch_ref is None
            or latest.dispatch_request_fingerprint_ref is None
            or self._dispatch_receipt_resolver is None
        ):
            raise MissionStepConflictError("MISSION_STEP_DISPATCH_EVIDENCE_REQUIRED")
        durable = self._dispatch_receipt_resolver(latest.dispatch_ref)
        if durable is None or durable != supplied:
            raise MissionStepConflictError("MISSION_STEP_DISPATCH_NOT_DURABLE")
        if (
            durable.dispatch_ref != latest.dispatch_ref
            or durable.request_fingerprint_ref
            != latest.dispatch_request_fingerprint_ref
            or durable.run_ref != latest.definition.run_ref
            or durable.lease_ref != latest.definition.lease_ref
            or durable.adapter_ref != latest.definition.adapter_ref
            or durable.capability_ref != latest.definition.capability_ref
        ):
            raise MissionStepConflictError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        return durable

    @staticmethod
    def _expired_dispatch_posture(
        receipt: AuthorityDispatchReceipt,
    ) -> tuple[MissionStepStatus, str]:
        if receipt.status == AuthorityDispatchStatus.succeeded.value:
            return MissionStepStatus.succeeded, "reason-ref:mission-step:succeeded"
        if receipt.status in {
            AuthorityDispatchStatus.failed.value,
            AuthorityDispatchStatus.denied.value,
        }:
            return MissionStepStatus.failed, "reason-ref:mission-step:dispatch-failed"
        if receipt.status == AuthorityDispatchStatus.cancelled_before_start.value:
            return (
                MissionStepStatus.failed,
                "reason-ref:mission-step:deadline-expired-before-dispatch",
            )
        return (
            MissionStepStatus.recovery_required,
            "reason-ref:mission-step:dispatch-recovery-required",
        )

    @staticmethod
    def _dispatch_evidence_refs(
        receipt: AuthorityDispatchReceipt,
    ) -> list[str]:
        values = [
            receipt.receipt_ref,
            receipt.entry_hash_ref,
            receipt.authority_decision_ref,
            receipt.authority_policy_receipt_ref,
            receipt.approval_validation_ref,
            receipt.budget_reservation_receipt_ref,
            receipt.budget_start_receipt_ref,
            receipt.budget_settlement_receipt_ref,
            receipt.budget_release_receipt_ref,
            receipt.execution_ref,
            *receipt.evidence_refs,
            *receipt.output_refs,
        ]
        return list(dict.fromkeys(value for value in values if value is not None))

    def _require_owned(
        self,
        receipts: list[MissionStepReceipt],
        step_ref: str,
        owner_ref: str,
        claim_ref: str,
        generation: int,
        current: datetime,
    ) -> MissionStepReceipt:
        latest = self._require_latest(receipts, step_ref)
        if (
            latest.status != MissionStepStatus.claimed.value
            or latest.owner_ref != owner_ref
            or latest.claim_ref != claim_ref
            or latest.generation != generation
        ):
            raise MissionStepConflictError("MISSION_STEP_STALE_FENCE")
        if latest.claim_expires_at is None or latest.claim_expires_at <= current:
            raise MissionStepConflictError("MISSION_STEP_CLAIM_EXPIRED")
        return latest

    @staticmethod
    def _latest(
        receipts: list[MissionStepReceipt], step_ref: str
    ) -> MissionStepReceipt | None:
        return next(
            (
                item
                for item in reversed(receipts)
                if item.definition.step_ref == step_ref
            ),
            None,
        )

    def _require_latest(
        self, receipts: list[MissionStepReceipt], step_ref: str
    ) -> MissionStepReceipt:
        latest = self._latest(receipts, step_ref)
        if latest is None:
            raise KeyError("MISSION_STEP_UNKNOWN")
        return latest

    def _build(
        self,
        receipts: list[MissionStepReceipt],
        *,
        definition: MissionStepDefinition,
        status: MissionStepStatus,
        generation: int,
        safe_summary: str,
        **updates: Any,
    ) -> MissionStepReceipt:
        sequence = len(receipts) + 1
        payload = dict(
            schema_version=MISSION_STEP_SCHEMA_VERSION,
            sequence=sequence,
            receipt_ref=f"mission-step-receipt-ref:{sequence}",
            entry_hash_ref="mission-step-entry-hash-ref:pending",
            previous_entry_hash_ref=receipts[-1].entry_hash_ref if receipts else None,
            definition=definition,
            definition_fingerprint_ref=definition.fingerprint_ref,
            status=status,
            generation=generation,
            safe_summary=safe_summary,
            **updates,
        )
        receipt = MissionStepReceipt.model_validate(payload)
        receipt = receipt.model_copy(update={"entry_hash_ref": _entry_hash(receipt)})
        self._validate_history_receipt(
            receipt,
            self._latest(receipts, definition.step_ref),
        )
        return receipt

    def _build_from(
        self,
        receipts: list[MissionStepReceipt],
        latest: MissionStepReceipt,
        **updates: Any,
    ) -> MissionStepReceipt:
        return self._build(receipts, definition=latest.definition, **updates)

    def _append(self, receipt: MissionStepReceipt) -> None:
        self.receipts_path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not self.receipts_path.exists()
        with self.receipts_path.open("a", encoding="utf-8") as stream:
            stream.write(receipt.model_dump_json() + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if new_file:
            directory_fd = os.open(self.receipts_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

    def _load(self) -> list[MissionStepReceipt]:
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
            raise MissionStepCorruptionError("MISSION_STEP_LEDGER_READ_FAILED") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise MissionStepCorruptionError(
                    "MISSION_STEP_LEDGER_REGULAR_FILE_REQUIRED"
                )
            if metadata.st_size > MISSION_STEP_LEDGER_MAX_BYTES:
                raise MissionStepCorruptionError(
                    "MISSION_STEP_LEDGER_SIZE_LIMIT_EXCEEDED"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                payload = stream.read(MISSION_STEP_LEDGER_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
        if len(payload) > MISSION_STEP_LEDGER_MAX_BYTES:
            raise MissionStepCorruptionError("MISSION_STEP_LEDGER_SIZE_LIMIT_EXCEEDED")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise MissionStepCorruptionError("MISSION_STEP_LEDGER_INVALID") from exc
        if len(lines) > MISSION_STEP_LEDGER_MAX_RECEIPTS:
            raise MissionStepCorruptionError(
                "MISSION_STEP_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        receipts = [
            MissionStepReceipt.model_validate_json(line)
            for line in lines
            if line.strip()
        ]
        previous: str | None = None
        latest_by_step: dict[str, MissionStepReceipt] = {}
        for index, receipt in enumerate(receipts, 1):
            if (
                receipt.sequence != index
                or receipt.previous_entry_hash_ref != previous
                or receipt.entry_hash_ref != _entry_hash(receipt)
            ):
                raise MissionStepCorruptionError("MISSION_STEP_HASH_CHAIN_INVALID")
            prior = latest_by_step.get(receipt.definition.step_ref)
            self._validate_history_receipt(receipt, prior)
            latest_by_step[receipt.definition.step_ref] = receipt
            previous = receipt.entry_hash_ref
        return receipts

    def _validate_history_receipt(
        self,
        receipt: MissionStepReceipt,
        prior: MissionStepReceipt | None,
    ) -> None:
        if receipt.checked_at.tzinfo is None:
            raise MissionStepCorruptionError("MISSION_STEP_CHECKED_AT_INVALID")
        if (receipt.dispatch_ref is None) != (
            receipt.dispatch_request_fingerprint_ref is None
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        if (receipt.dispatch_receipt_ref is None) != (
            receipt.dispatch_entry_hash_ref is None
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_DISPATCH_RECEIPT_BINDING_INVALID"
            )
        if receipt.status == MissionStepStatus.claimed.value:
            assert receipt.claim_expires_at is not None
            if (
                receipt.claim_expires_at.tzinfo is None
                or receipt.claim_expires_at <= receipt.checked_at
                or receipt.claim_expires_at > receipt.definition.deadline
                or receipt.claim_expires_at
                > receipt.checked_at + timedelta(seconds=300)
            ):
                raise MissionStepCorruptionError("MISSION_STEP_CLAIM_EXPIRY_INVALID")
        if prior is None:
            if (
                receipt.status != MissionStepStatus.pending.value
                or receipt.generation != 0
                or receipt.dispatch_ref is not None
                or receipt.reason_refs
                or receipt.evidence_refs
            ):
                raise MissionStepCorruptionError("MISSION_STEP_INITIAL_STATE_INVALID")
            return
        if (
            prior.definition_fingerprint_ref != receipt.definition_fingerprint_ref
            or prior.status in TERMINAL_MISSION_STEP_STATUSES
            or receipt.checked_at < prior.checked_at
        ):
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        if prior.dispatch_ref is not None and (
            receipt.dispatch_ref != prior.dispatch_ref
            or receipt.dispatch_request_fingerprint_ref
            != prior.dispatch_request_fingerprint_ref
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_BINDING_INVALID")
        if prior.status == MissionStepStatus.pending.value:
            allowed = (
                receipt.status == MissionStepStatus.claimed.value
                and receipt.generation == prior.generation + 1
            ) or (
                receipt.status == MissionStepStatus.failed.value
                and receipt.generation == prior.generation
            )
            if not allowed:
                raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        elif prior.status == MissionStepStatus.claimed.value:
            self._validate_claimed_transition(receipt, prior)
        else:
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        if receipt.dispatch_receipt_ref is not None:
            self._validate_persisted_dispatch(receipt)
        if receipt.status == MissionStepStatus.succeeded.value:
            self._validate_persisted_success(receipt)

    def _validate_claimed_transition(
        self,
        receipt: MissionStepReceipt,
        prior: MissionStepReceipt,
    ) -> None:
        if receipt.generation == prior.generation + 1:
            if (
                receipt.status != MissionStepStatus.claimed.value
                or prior.claim_expires_at is None
                or prior.claim_expires_at > receipt.checked_at
                or receipt.dispatch_ref != prior.dispatch_ref
                or receipt.dispatch_request_fingerprint_ref
                != prior.dispatch_request_fingerprint_ref
            ):
                raise MissionStepCorruptionError("MISSION_STEP_FENCE_ADVANCE_INVALID")
            return
        if receipt.generation != prior.generation:
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")
        if receipt.status == MissionStepStatus.claimed.value:
            if (
                receipt.owner_ref != prior.owner_ref
                or receipt.claim_ref != prior.claim_ref
                or receipt.claim_expires_at is None
                or prior.claim_expires_at is None
                or receipt.claim_expires_at < prior.claim_expires_at
            ):
                raise MissionStepCorruptionError("MISSION_STEP_CLAIM_BINDING_INVALID")
            return
        if receipt.status not in TERMINAL_MISSION_STEP_STATUSES:
            raise MissionStepCorruptionError("MISSION_STEP_TRANSITION_INVALID")

    def _validate_persisted_success(self, receipt: MissionStepReceipt) -> None:
        if (
            receipt.dispatch_ref is None
            or receipt.dispatch_request_fingerprint_ref is None
            or receipt.dispatch_receipt_ref is None
            or receipt.dispatch_entry_hash_ref is None
            or receipt.dispatch_receipt_ref not in receipt.evidence_refs
            or receipt.dispatch_entry_hash_ref not in receipt.evidence_refs
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_EVIDENCE_INVALID"
            )
        self._validate_persisted_dispatch(receipt)

    def _validate_persisted_dispatch(self, receipt: MissionStepReceipt) -> None:
        if (
            receipt.dispatch_ref is None
            or receipt.dispatch_receipt_ref is None
            or receipt.dispatch_entry_hash_ref is None
            or receipt.dispatch_receipt_ref not in receipt.evidence_refs
            or receipt.dispatch_entry_hash_ref not in receipt.evidence_refs
            or self._dispatch_receipt_resolver is None
        ):
            raise MissionStepCorruptionError("MISSION_STEP_DISPATCH_EVIDENCE_INVALID")
        durable = self._dispatch_receipt_resolver(receipt.dispatch_ref)
        if (
            durable is None
            or durable.receipt_ref != receipt.dispatch_receipt_ref
            or durable.entry_hash_ref != receipt.dispatch_entry_hash_ref
        ):
            raise MissionStepCorruptionError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_NOT_DURABLE"
            )
        try:
            self._validate_durable_dispatch(receipt, durable)
            if receipt.status == MissionStepStatus.succeeded.value:
                self._validate_succeeded_dispatch(receipt, durable)
        except MissionStepConflictError as exc:
            raise MissionStepCorruptionError(
                "MISSION_STEP_SUCCEEDED_DISPATCH_BINDING_INVALID"
            ) from exc
