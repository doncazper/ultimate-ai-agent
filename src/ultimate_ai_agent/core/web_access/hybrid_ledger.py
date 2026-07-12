"""Atomic free-credit ledger with optional bounded crash-safe journaling.

The provider credit snapshot is authoritative for account balance. This local
ledger coordinates only UAA-owned in-flight reservations and never opens a
network connection or grants provider authority.
"""

from __future__ import annotations

import fcntl
import json
import os
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Iterator

from ultimate_ai_agent.core.capability_availability.contracts import (
    CapabilityInvocationDecision,
    InvocationDecisionOutcome,
)

from .hybrid_contracts import (
    WebCreditReceiptCompleteness,
    WebCreditReservationStatus,
    WebCreditSnapshotFreshness,
    WebProviderCreditReservation,
    WebProviderCreditReservationRequest,
    WebProviderCreditSnapshot,
    WebProviderPlanKind,
    stable_web_hybrid_ref,
)


WEB_HYBRID_EFFECTIVE_CLOUD_CONCURRENCY = 1
WEB_CREDIT_LEDGER_MAX_BYTES = 2_000_000
WEB_CREDIT_LEDGER_MAX_RECORDS = 1_000
WEB_CREDIT_LEDGER_MAX_RESERVATIONS = 256
WEB_CREDIT_LEDGER_MAX_SNAPSHOTS = 16


class WebCreditLedgerConflictError(RuntimeError):
    """Raised when an idempotency ref is reused for different semantics."""


class WebCreditReservationInProgressError(RuntimeError):
    """Raised when another caller owns the active idempotent reservation."""


class WebCreditLedgerTransitionError(RuntimeError):
    """Raised when a reservation transition is invalid."""


@dataclass
class InMemoryWebCreditLedger:
    """Thread-safe ledger; ``state_path`` enables bounded durable recovery."""

    state_path: Path | None = field(default=None, repr=False)

    _lock: RLock = field(default_factory=RLock, init=False, repr=False)
    _snapshots: dict[str, WebProviderCreditSnapshot] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _reservations: dict[str, WebProviderCreditReservation] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _idempotency_index: dict[str, str] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _fingerprints: dict[str, str] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _snapshot_fingerprints: dict[str, str] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _start_claimed_refs: set[str] = field(default_factory=set, init=False, repr=False)
    _sequence: int = field(default=0, init=False, repr=False)
    _last_record_ref: str | None = field(default=None, init=False, repr=False)
    _poisoned: bool = field(default=False, init=False, repr=False)
    _durable_parent_fd: int | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.state_path is not None:
            self.state_path = Path(self.state_path)
            with self._lock, self._durable_lock():
                pass

    @property
    def crash_recovery_enabled(self) -> bool:
        return self.state_path is not None

    def recovery_required_reservation_refs(self) -> tuple[str, ...]:
        """Return starts lacking a durable terminal settlement."""

        with self._read_context():
            return tuple(sorted(self._start_claimed_refs))

    def reconcile(
        self, snapshot: WebProviderCreditSnapshot
    ) -> WebProviderCreditSnapshot:
        fingerprint = stable_web_hybrid_ref(
            "snapshot-fingerprint-ref:web-credit",
            snapshot.model_dump(mode="json"),
        )
        with self._mutation_context():
            prior_fingerprint = self._snapshot_fingerprints.get(snapshot.snapshot_ref)
            if prior_fingerprint is not None and prior_fingerprint != fingerprint:
                raise WebCreditLedgerConflictError(
                    "WEB_CREDIT_SNAPSHOT_REF_SEMANTIC_CONFLICT"
                )
            prior = self._snapshots.get(snapshot.provider_ref)
            if prior is not None and snapshot.fetched_at < prior.fetched_at:
                raise WebCreditLedgerConflictError("WEB_CREDIT_SNAPSHOT_STALE_REPLAY")
            self._snapshots[snapshot.provider_ref] = snapshot
            self._snapshot_fingerprints[snapshot.snapshot_ref] = fingerprint
            self._persist_state("snapshot_reconciled")
            return snapshot

    def latest_snapshot(self, provider_ref: str) -> WebProviderCreditSnapshot | None:
        with self._read_context():
            return self._snapshots.get(provider_ref)

    def reservation_snapshot(
        self, reservation_ref: str
    ) -> WebProviderCreditReservation | None:
        """Return current reservation truth without granting or mutating budget."""

        with self._read_context():
            return self._reservations.get(reservation_ref)

    @contextmanager
    def hold_reservation_start(self, reservation_ref: str) -> Iterator[None]:
        """Fence reservation validation through the provider start boundary."""

        with self._lock, self._durable_lock():
            self._ensure_usable()
            reservation = self._reservations.get(reservation_ref)
            if (
                reservation is None
                or reservation.status != WebCreditReservationStatus.reserved
            ):
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_START_FENCE_MISSING"
                )
            if reservation_ref in self._start_claimed_refs:
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_START_ALREADY_CLAIMED"
                )
            prior = self._capture_state()
            self._start_claimed_refs.add(reservation_ref)
            try:
                self._persist_state("start_claimed")
            except Exception:
                self._restore_state(prior)
                raise
            yield

    def abort_unstarted(
        self,
        reservation_ref: str,
        *,
        authorized_decision: CapabilityInvocationDecision,
        final_decision: CapabilityInvocationDecision,
        network_call_performed: bool,
    ) -> None:
        """Clear a claim only with typed proof that final authority blocked start."""

        with self._mutation_context():
            current = self._reservations.get(reservation_ref)
            if current is None or current.status != WebCreditReservationStatus.reserved:
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_NOT_ACTIVE"
                )
            if reservation_ref not in self._start_claimed_refs:
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_START_FENCE_MISSING"
                )
            if (
                network_call_performed
                or authorized_decision.outcome != InvocationDecisionOutcome.allow
                or final_decision.outcome == InvocationDecisionOutcome.allow
                or final_decision.request_ref != current.request_ref
                or authorized_decision.request_ref != current.request_ref
                or not final_decision.blocker_codes
                or not authorized_decision.budget_decision_ref
                or not final_decision.budget_decision_ref
                or not authorized_decision.budget_decision_ref.startswith(
                    "budget-decision-ref:firecrawl-cloud-cost-decision:"
                )
                or not final_decision.budget_decision_ref.startswith(
                    "budget-decision-ref:firecrawl-cloud-cost-decision:"
                )
                or any(
                    getattr(final_decision, field_name)
                    != getattr(authorized_decision, field_name)
                    for field_name in (
                        "capability_ref",
                        "provider_ref",
                        "adapter_ref",
                        "expected_execution_receipt_ref",
                    )
                )
            ):
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_UNSTARTED_ABORT_PROOF_INVALID"
                )
            self._start_claimed_refs.remove(reservation_ref)
            self._persist_state("start_aborted_before_transport")

    def reserve(
        self,
        request: WebProviderCreditReservationRequest,
        *,
        now: datetime | None = None,
    ) -> WebProviderCreditReservation:
        now = now or datetime.now(timezone.utc)
        if now.utcoffset() is None:
            raise ValueError("WEB_CREDIT_NOW_TIMEZONE_REQUIRED")
        fingerprint = stable_web_hybrid_ref(
            "request-fingerprint-ref:web-credit-reservation",
            request.model_dump(mode="json"),
        )
        with self._mutation_context():
            existing_ref = self._idempotency_index.get(request.idempotency_ref)
            if existing_ref is not None:
                if self._fingerprints[request.idempotency_ref] != fingerprint:
                    raise WebCreditLedgerConflictError(
                        "WEB_CREDIT_IDEMPOTENCY_SEMANTIC_CONFLICT"
                    )
                existing = self._reservations[existing_ref]
                if (
                    existing.status == WebCreditReservationStatus.reserved
                    and existing.in_flight
                ):
                    raise WebCreditReservationInProgressError(
                        "CLOUD_IDEMPOTENT_RESERVATION_IN_PROGRESS"
                    )
                return existing

            snapshot = self._snapshots.get(request.provider_ref)
            reasons: list[str] = []
            if snapshot is None:
                reasons.append("CLOUD_CREDIT_SNAPSHOT_MISSING")
            elif snapshot.snapshot_ref != request.snapshot_ref:
                reasons.append("CLOUD_CREDIT_SNAPSHOT_REF_MISMATCH")
            elif snapshot.billing_period_ref != request.billing_period_ref:
                reasons.append("CLOUD_CREDIT_BILLING_PERIOD_MISMATCH")
            else:
                if snapshot.plan_kind != WebProviderPlanKind.free:
                    reasons.append("CLOUD_FREE_PLAN_NOT_PROVEN")
                if snapshot.freshness != WebCreditSnapshotFreshness.current:
                    reasons.append("CLOUD_CREDIT_SNAPSHOT_NOT_CURRENT")
                if snapshot.expires_at <= now:
                    reasons.append("CLOUD_CREDIT_SNAPSHOT_EXPIRED")
                if (
                    not snapshot.billing_period_start
                    <= now
                    < snapshot.billing_period_end
                ):
                    reasons.append("CLOUD_CREDIT_BILLING_PERIOD_INACTIVE")

            active = [
                item
                for item in self._reservations.values()
                if item.provider_ref == request.provider_ref
                and item.billing_period_ref == request.billing_period_ref
                and item.status == WebCreditReservationStatus.reserved
                and item.in_flight
            ]
            if any(
                item.provider_ref == request.provider_ref
                and item.billing_period_ref == request.billing_period_ref
                and item.status == WebCreditReservationStatus.incomplete
                for item in self._reservations.values()
            ):
                reasons.append("CLOUD_PRIOR_USAGE_RECEIPT_INCOMPLETE")
            if snapshot is not None:
                if snapshot.max_concurrency is None:
                    reasons.append("CLOUD_PLAN_CONCURRENCY_UNKNOWN")
                elif len(active) >= min(
                    snapshot.max_concurrency,
                    WEB_HYBRID_EFFECTIVE_CLOUD_CONCURRENCY,
                ):
                    reasons.append(
                        "CLOUD_UAA_USAGE_ATTRIBUTION_CONCURRENCY_EXHAUSTED"
                    )
            in_flight_credits = sum(item.reserved_credits for item in active)
            run_committed_credits = sum(
                item.reserved_credits
                for item in self._reservations.values()
                if item.provider_ref == request.provider_ref
                and item.billing_period_ref == request.billing_period_ref
                and item.status
                in {
                    WebCreditReservationStatus.reserved,
                    WebCreditReservationStatus.settled,
                    WebCreditReservationStatus.incomplete,
                }
            )
            if (
                run_committed_credits + request.estimated_credits
                > request.run_credit_ceiling
            ):
                reasons.append("CLOUD_RUN_CREDIT_CEILING_EXHAUSTED")
            spendable = (
                snapshot.remaining_credits
                - in_flight_credits
                - request.safety_reserve_credits
                if snapshot is not None
                else 0
            )
            if spendable < request.estimated_credits:
                reasons.append("CLOUD_CREDIT_BUDGET_EXHAUSTED")

            status = (
                WebCreditReservationStatus.denied
                if reasons
                else WebCreditReservationStatus.reserved
            )
            reservation_ref = stable_web_hybrid_ref(
                "web-credit-reservation-ref",
                {
                    "idempotency_ref": request.idempotency_ref,
                    "fingerprint": fingerprint,
                },
            )
            reservation = WebProviderCreditReservation(
                reservation_ref=reservation_ref,
                request_ref=request.request_ref,
                idempotency_ref=request.idempotency_ref,
                request_fingerprint_ref=fingerprint,
                provider_ref=request.provider_ref,
                snapshot_ref=request.snapshot_ref,
                billing_period_ref=request.billing_period_ref,
                routing_decision_ref=request.routing_decision_ref,
                cost_policy_ref=request.cost_policy_ref,
                estimated_credits=request.estimated_credits,
                reserved_credits=(request.estimated_credits if not reasons else 0),
                status=status,
                receipt_completeness=(
                    WebCreditReceiptCompleteness.unknown
                    if not reasons
                    else WebCreditReceiptCompleteness.complete
                ),
                attempt_number=request.attempt_number,
                fallback_parent_ref=request.fallback_parent_ref,
                reason_codes=tuple(dict.fromkeys(reasons)),
                in_flight=not reasons,
            )
            self._reservations[reservation_ref] = reservation
            self._idempotency_index[request.idempotency_ref] = reservation_ref
            self._fingerprints[request.idempotency_ref] = fingerprint
            self._persist_state("reservation_recorded")
            return reservation

    def settle(
        self,
        reservation_ref: str,
        *,
        actual_credits: int | None,
        actual_usage_ref: str | None,
    ) -> WebProviderCreditReservation:
        if actual_credits is not None and actual_credits < 0:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_ACTUAL_USAGE_INVALID")
        with self._mutation_context():
            current = self._reservations.get(reservation_ref)
            if current is None or current.status != WebCreditReservationStatus.reserved:
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_NOT_ACTIVE"
                )
            complete = (
                actual_credits is not None
                and actual_usage_ref is not None
                and actual_credits <= current.reserved_credits
            )
            updated = current.model_copy(
                update={
                    "status": (
                        WebCreditReservationStatus.settled
                        if complete
                        else WebCreditReservationStatus.incomplete
                    ),
                    "receipt_completeness": (
                        WebCreditReceiptCompleteness.complete
                        if complete
                        else WebCreditReceiptCompleteness.incomplete
                    ),
                    "actual_usage_ref": actual_usage_ref,
                    "reason_codes": (
                        () if complete else ("CLOUD_ACTUAL_USAGE_OR_COST_INCOMPLETE",)
                    ),
                    "in_flight": False,
                }
            )
            self._reservations[reservation_ref] = updated
            self._start_claimed_refs.discard(reservation_ref)
            self._persist_state("reservation_settled")
            return updated

    def release(self, reservation_ref: str) -> WebProviderCreditReservation:
        with self._mutation_context():
            if reservation_ref in self._start_claimed_refs:
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_STARTED_RELEASE_DENIED"
                )
            current = self._reservations.get(reservation_ref)
            if current is None or current.status != WebCreditReservationStatus.reserved:
                raise WebCreditLedgerTransitionError(
                    "WEB_CREDIT_RESERVATION_NOT_ACTIVE"
                )
            updated = current.model_copy(
                update={
                    "status": WebCreditReservationStatus.released,
                    "receipt_completeness": WebCreditReceiptCompleteness.complete,
                    "in_flight": False,
                    "reason_codes": ("CLOUD_RESERVATION_RELEASED_PRE_DISPATCH",),
                }
            )
            self._reservations[reservation_ref] = updated
            self._persist_state("reservation_released")
            return updated

    def list_reservations(self) -> tuple[WebProviderCreditReservation, ...]:
        with self._read_context():
            return tuple(self._reservations.values())

    @contextmanager
    def _mutation_context(self) -> Iterator[None]:
        with self._lock:
            self._ensure_usable()
            with self._durable_lock():
                prior = self._capture_state()
                try:
                    yield
                except Exception:
                    self._restore_state(prior)
                    raise

    @contextmanager
    def _read_context(self) -> Iterator[None]:
        with self._lock:
            self._ensure_usable()
            with self._durable_lock():
                yield

    @contextmanager
    def _durable_lock(self) -> Iterator[None]:
        if self.state_path is None or self._durable_parent_fd is not None:
            yield
            return
        parent_fd = self._open_parent_fd()
        lock_fd: int | None = None
        try:
            lock_name = f".{self.state_path.name}.lock"
            lock_fd, created = self._open_regular_at(
                parent_fd,
                lock_name,
                os.O_RDWR | os.O_CREAT,
                conflict=False,
            )
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            if created:
                os.fsync(parent_fd)
            self._durable_parent_fd = parent_fd
            self._load_durable_state()
            yield
        finally:
            self._durable_parent_fd = None
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                finally:
                    os.close(lock_fd)
            os.close(parent_fd)

    def _capture_state(self) -> tuple[object, ...]:
        return (
            dict(self._snapshots),
            dict(self._reservations),
            dict(self._idempotency_index),
            dict(self._fingerprints),
            dict(self._snapshot_fingerprints),
            set(self._start_claimed_refs),
            self._sequence,
            self._last_record_ref,
        )

    def _restore_state(self, state: tuple[object, ...]) -> None:
        (
            snapshots,
            reservations,
            idempotency_index,
            fingerprints,
            snapshot_fingerprints,
            start_claimed_refs,
            sequence,
            last_record_ref,
        ) = state
        self._snapshots = dict(snapshots)  # type: ignore[arg-type]
        self._reservations = dict(reservations)  # type: ignore[arg-type]
        self._idempotency_index = dict(idempotency_index)  # type: ignore[arg-type]
        self._fingerprints = dict(fingerprints)  # type: ignore[arg-type]
        self._snapshot_fingerprints = dict(snapshot_fingerprints)  # type: ignore[arg-type]
        self._start_claimed_refs = set(start_claimed_refs)  # type: ignore[arg-type]
        self._sequence = int(sequence)  # type: ignore[arg-type]
        self._last_record_ref = (
            str(last_record_ref) if last_record_ref is not None else None
        )

    def _ensure_usable(self) -> None:
        if self._poisoned:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_RELOAD_REQUIRED")

    def _persist_state(self, event: str) -> None:
        if self.state_path is None:
            return
        if len(self._reservations) > WEB_CREDIT_LEDGER_MAX_RESERVATIONS:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_RESERVATION_LIMIT")
        if len(self._snapshots) > WEB_CREDIT_LEDGER_MAX_SNAPSHOTS:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_SNAPSHOT_LIMIT")
        if self._sequence >= WEB_CREDIT_LEDGER_MAX_RECORDS:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_RECORD_LIMIT")
        sequence = self._sequence + 1
        payload = {
            "schema_version": "uaa-web-credit-ledger.v1",
            "sequence": sequence,
            "event": event,
            "previous_record_ref": self._last_record_ref,
            "snapshots": [
                item.model_dump(mode="json")
                for item in sorted(
                    self._snapshots.values(), key=lambda value: value.provider_ref
                )
            ],
            "reservations": [
                item.model_dump(mode="json")
                for item in sorted(
                    self._reservations.values(),
                    key=lambda value: value.reservation_ref,
                )
            ],
            "start_claimed_refs": sorted(self._start_claimed_refs),
        }
        record_ref = stable_web_hybrid_ref("web-credit-ledger-record-ref", payload)
        record = {**payload, "record_ref": record_ref}
        encoded = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
        try:
            self._append_record(encoded)
        except Exception:
            self._poisoned = True
            raise
        self._sequence = sequence
        self._last_record_ref = record_ref

    def _append_record(self, encoded: bytes) -> None:
        if self.state_path is None or self._durable_parent_fd is None:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_LOCK_REQUIRED")
        fd, created = self._open_regular_at(
            self._durable_parent_fd,
            self.state_path.name,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            conflict=False,
        )
        try:
            info = os.fstat(fd)
            if info.st_size + len(encoded) > WEB_CREDIT_LEDGER_MAX_BYTES:
                raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_SIZE_LIMIT")
            view = memoryview(encoded)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise WebCreditLedgerTransitionError(
                        "WEB_CREDIT_LEDGER_WRITE_FAILED"
                    )
                view = view[written:]
            os.fsync(fd)
            if created:
                os.fsync(self._durable_parent_fd)
        finally:
            os.close(fd)

    def _load_durable_state(self) -> None:
        if self.state_path is None or self._durable_parent_fd is None:
            raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_LOCK_REQUIRED")
        try:
            fd, _created = self._open_regular_at(
                self._durable_parent_fd,
                self.state_path.name,
                os.O_RDWR,
                conflict=True,
                allow_missing=True,
            )
        except FileNotFoundError:
            self._reset_loaded_state()
            return
        try:
            info = os.fstat(fd)
            if info.st_size > WEB_CREDIT_LEDGER_MAX_BYTES:
                raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_FILE_UNSAFE")
            raw = b""
            while len(raw) <= WEB_CREDIT_LEDGER_MAX_BYTES:
                chunk = os.read(fd, 65_536)
                if not chunk:
                    break
                raw += chunk
            if len(raw) > WEB_CREDIT_LEDGER_MAX_BYTES:
                raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_SIZE_LIMIT")
            if raw and not raw.endswith(b"\n"):
                safe_end = raw.rfind(b"\n") + 1
                os.ftruncate(fd, safe_end)
                os.fsync(fd)
                raw = raw[:safe_end]
        finally:
            os.close(fd)
        lines = raw.splitlines()
        if len(lines) > WEB_CREDIT_LEDGER_MAX_RECORDS:
            raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_RECORD_LIMIT")
        previous_ref: str | None = None
        last: dict[str, object] | None = None
        for expected_sequence, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise WebCreditLedgerConflictError(
                    "WEB_CREDIT_LEDGER_RECORD_INVALID"
                ) from exc
            if not isinstance(record, dict):
                raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_RECORD_INVALID")
            record_ref = record.pop("record_ref", None)
            if (
                record.get("schema_version") != "uaa-web-credit-ledger.v1"
                or record.get("sequence") != expected_sequence
                or record.get("previous_record_ref") != previous_ref
                or record_ref
                != stable_web_hybrid_ref("web-credit-ledger-record-ref", record)
            ):
                raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_CHAIN_INVALID")
            previous_ref = str(record_ref)
            last = record
        self._reset_loaded_state()
        if last is None:
            return
        try:
            snapshots = tuple(
                WebProviderCreditSnapshot.model_validate(item)
                for item in last["snapshots"]  # type: ignore[index]
            )
            reservations = tuple(
                WebProviderCreditReservation.model_validate(item)
                for item in last["reservations"]  # type: ignore[index]
            )
            claimed = {str(item) for item in last["start_claimed_refs"]}  # type: ignore[index]
        except (KeyError, TypeError, ValueError) as exc:
            raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_STATE_INVALID") from exc
        if (
            len(snapshots) > WEB_CREDIT_LEDGER_MAX_SNAPSHOTS
            or len(reservations) > WEB_CREDIT_LEDGER_MAX_RESERVATIONS
        ):
            raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_STATE_LIMIT")
        self._snapshots = {item.provider_ref: item for item in snapshots}
        self._reservations = {item.reservation_ref: item for item in reservations}
        if any(
            ref not in self._reservations
            or self._reservations[ref].status != WebCreditReservationStatus.reserved
            for ref in claimed
        ):
            raise WebCreditLedgerConflictError("WEB_CREDIT_LEDGER_START_STATE_INVALID")
        self._start_claimed_refs = claimed
        for snapshot in snapshots:
            self._snapshot_fingerprints[snapshot.snapshot_ref] = stable_web_hybrid_ref(
                "snapshot-fingerprint-ref:web-credit",
                snapshot.model_dump(mode="json"),
            )
        for reservation in reservations:
            prior = self._idempotency_index.get(reservation.idempotency_ref)
            if prior is not None and prior != reservation.reservation_ref:
                raise WebCreditLedgerConflictError(
                    "WEB_CREDIT_LEDGER_IDEMPOTENCY_STATE_CONFLICT"
                )
            self._idempotency_index[reservation.idempotency_ref] = (
                reservation.reservation_ref
            )
            self._fingerprints[reservation.idempotency_ref] = (
                reservation.request_fingerprint_ref
            )
        self._sequence = int(last["sequence"])
        self._last_record_ref = previous_ref

    def _reset_loaded_state(self) -> None:
        self._snapshots = {}
        self._reservations = {}
        self._idempotency_index = {}
        self._fingerprints = {}
        self._snapshot_fingerprints = {}
        self._start_claimed_refs = set()
        self._sequence = 0
        self._last_record_ref = None

    def _open_parent_fd(self) -> int:
        if self.state_path is None:
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_PATH_MISSING")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            parent_fd = os.open(self.state_path.parent, flags)
        except OSError as exc:
            raise WebCreditLedgerTransitionError(
                "WEB_CREDIT_LEDGER_PARENT_UNSAFE"
            ) from exc
        info = os.fstat(parent_fd)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o022
        ):
            os.close(parent_fd)
            raise WebCreditLedgerTransitionError("WEB_CREDIT_LEDGER_PARENT_UNSAFE")
        return parent_fd

    def _open_regular_at(
        self,
        parent_fd: int,
        name: str,
        access_flags: int,
        *,
        conflict: bool,
        allow_missing: bool = False,
    ) -> tuple[int, bool]:
        try:
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            existed = True
        except FileNotFoundError:
            existed = False
        flags = access_flags | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            fd = os.open(name, flags, 0o600, dir_fd=parent_fd)
        except FileNotFoundError:
            if allow_missing:
                raise
            error = (
                WebCreditLedgerConflictError
                if conflict
                else WebCreditLedgerTransitionError
            )
            raise error("WEB_CREDIT_LEDGER_OPEN_FAILED") from None
        except OSError as exc:
            error = (
                WebCreditLedgerConflictError
                if conflict
                else WebCreditLedgerTransitionError
            )
            raise error("WEB_CREDIT_LEDGER_OPEN_FAILED") from exc
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or info.st_mode & 0o022
        ):
            os.close(fd)
            error = (
                WebCreditLedgerConflictError
                if conflict
                else WebCreditLedgerTransitionError
            )
            raise error("WEB_CREDIT_LEDGER_FILE_UNSAFE")
        return fd, not existed


class DurableWebCreditLedger(InMemoryWebCreditLedger):
    """Crash-recoverable credit ledger required by real cloud transports."""

    def __init__(self, state_path: Path) -> None:
        super().__init__(state_path=state_path)


__all__ = [
    "DurableWebCreditLedger",
    "InMemoryWebCreditLedger",
    "WEB_HYBRID_EFFECTIVE_CLOUD_CONCURRENCY",
    "WebCreditLedgerConflictError",
    "WebCreditReservationInProgressError",
    "WebCreditLedgerTransitionError",
]
