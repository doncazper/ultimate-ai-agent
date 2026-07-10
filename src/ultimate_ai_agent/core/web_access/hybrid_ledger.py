"""Atomic in-memory free-credit ledger for deterministic hybrid-web tests.

The provider credit snapshot is authoritative for account balance. This local
ledger coordinates only UAA-owned in-flight reservations and never opens a
network connection or grants provider authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock

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


class WebCreditLedgerConflictError(RuntimeError):
    """Raised when an idempotency ref is reused for different semantics."""


class WebCreditReservationInProgressError(RuntimeError):
    """Raised when another caller owns the active idempotent reservation."""


class WebCreditLedgerTransitionError(RuntimeError):
    """Raised when a reservation transition is invalid."""


@dataclass
class InMemoryWebCreditLedger:
    """Thread-safe injected ledger used before durable provider promotion."""

    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
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

    def reconcile(
        self, snapshot: WebProviderCreditSnapshot
    ) -> WebProviderCreditSnapshot:
        fingerprint = stable_web_hybrid_ref(
            "snapshot-fingerprint-ref:web-credit",
            snapshot.model_dump(mode="json"),
        )
        with self._lock:
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
            return snapshot

    def latest_snapshot(self, provider_ref: str) -> WebProviderCreditSnapshot | None:
        with self._lock:
            return self._snapshots.get(provider_ref)

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
        with self._lock:
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
        with self._lock:
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
            return updated

    def release(self, reservation_ref: str) -> WebProviderCreditReservation:
        with self._lock:
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
            return updated

    def list_reservations(self) -> tuple[WebProviderCreditReservation, ...]:
        with self._lock:
            return tuple(self._reservations.values())


__all__ = [
    "InMemoryWebCreditLedger",
    "WEB_HYBRID_EFFECTIVE_CLOUD_CONCURRENCY",
    "WebCreditLedgerConflictError",
    "WebCreditReservationInProgressError",
    "WebCreditLedgerTransitionError",
]
