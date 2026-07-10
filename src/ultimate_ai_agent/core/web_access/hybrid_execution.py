"""Governed self-host-first markdown execution with one cloud fallback."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.authority import AuthorityLease
from ultimate_ai_agent.core.capabilities.approval import LocalApprovalAuthority
from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .firecrawl_cloud import (
    CloudScrapeTransport,
    CreditTransport,
    FirecrawlCloudCredential,
    FirecrawlCloudExecutionResult,
    FirecrawlCloudMarkdownRequest,
    execute_firecrawl_cloud_markdown,
)
from .firecrawl_markdown import (
    FirecrawlMarkdownEvidence,
    FirecrawlMarkdownExecutionResult,
    FirecrawlMarkdownRequest,
    FirecrawlTransport,
    TargetValidator,
    execute_firecrawl_markdown,
)
from .hybrid_contracts import (
    WebCreditSnapshotFreshness,
    WebProviderAttemptOutcome,
    WebProviderCapabilityState,
    WebProviderCircuitState,
    WebProviderCreditSnapshot,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderPlanKind,
    WebProviderRoutingDecision,
    WebProviderRoutingPolicy,
    WebProviderTransportReceipt,
    WebProviderTransportStatus,
    stable_web_hybrid_ref,
)
from .hybrid_ledger import InMemoryWebCreditLedger
from .hybrid_router import simulate_hybrid_route


class HybridMarkdownExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    request_ref: str
    idempotency_ref: str
    policy: Literal[WebProviderRoutingPolicy.self_host_first_cloud_escalation] = (
        WebProviderRoutingPolicy.self_host_first_cloud_escalation
    )
    local_request: FirecrawlMarkdownRequest
    cloud_request: FirecrawlCloudMarkdownRequest
    expected_execution_receipt_ref: str
    max_attempts: Literal[2] = 2

    @field_validator(
        "request_ref",
        "idempotency_ref",
        "expected_execution_receipt_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        validate_execution_ref(value, "hybrid_markdown_execution_ref")
        return value

    @model_validator(mode="after")
    def validate_children(self) -> "HybridMarkdownExecutionRequest":
        if self.local_request.request_ref == self.cloud_request.request_ref:
            raise ValueError("HYBRID_CHILD_REQUEST_REFS_MUST_DIFFER")
        if (
            self.local_request.target_url != self.cloud_request.target_url
            or self.local_request.target_source_ref
            != self.cloud_request.target_source_ref
            or self.local_request.allowed_domains != self.cloud_request.allowed_domains
        ):
            raise ValueError("HYBRID_CHILD_TARGET_SCOPE_MISMATCH")
        return self


class WebCloudCircuitSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    circuit_ref: str
    state: WebProviderCircuitState
    failure_count: int = Field(..., ge=0, le=10)
    failure_threshold: int = Field(..., ge=1, le=10)
    opened_at: datetime | None = None
    review_after: datetime | None = None
    reason_codes: tuple[str, ...] = ()
    manual_reconciliation_required: Literal[True] = True
    background_probe_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_snapshot(self) -> "WebCloudCircuitSnapshot":
        validate_execution_ref(self.circuit_ref, "web_cloud_circuit_ref")
        if self.state == WebProviderCircuitState.open and (
            self.opened_at is None or self.review_after is None
        ):
            raise ValueError("WEB_CLOUD_CIRCUIT_OPEN_TIMESTAMPS_REQUIRED")
        return self


class HybridMarkdownExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    request_ref: str
    idempotency_ref: str
    execution_receipt_ref: str
    routing_decision: WebProviderRoutingDecision
    first_attempt_outcome: WebProviderAttemptOutcome
    final_deployment: WebProviderDeploymentKind | None = None
    status: WebProviderTransportStatus
    attempt_count: int = Field(..., ge=0, le=2)
    local_receipt: WebProviderTransportReceipt | None = None
    cloud_receipt: WebProviderTransportReceipt | None = None
    evidence: FirecrawlMarkdownEvidence | None = None
    reason_codes: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = ()
    replayed: bool = False
    content_untrusted: Literal[True] = True
    instruction_use_allowed: Literal[False] = False
    full_markdown_persisted: Literal[False] = False
    raw_provider_payload_persisted: Literal[False] = False
    credential_material_persisted: Literal[False] = False
    local_path_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "HybridMarkdownExecutionResult":
        for value in (
            self.request_ref,
            self.idempotency_ref,
            self.execution_receipt_ref,
        ):
            validate_execution_ref(value, "hybrid_markdown_result_ref")
        if self.attempt_count == 0 and self.local_receipt is not None:
            raise ValueError("HYBRID_ZERO_ATTEMPT_RECEIPT_DENIED")
        if self.attempt_count == 1 and self.local_receipt is None:
            raise ValueError("HYBRID_LOCAL_RECEIPT_REQUIRED")
        if self.attempt_count == 2 and (
            self.local_receipt is None or self.cloud_receipt is None
        ):
            raise ValueError("HYBRID_TWO_ATTEMPT_RECEIPTS_REQUIRED")
        if self.replayed and self.evidence is not None:
            raise ValueError("HYBRID_REPLAY_TRANSIENT_EVIDENCE_DENIED")
        if (
            self.status
            not in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            and self.evidence is not None
        ):
            raise ValueError("HYBRID_FAILED_EVIDENCE_DENIED")
        return self


class WebHybridExecutionConflictError(RuntimeError):
    """An idempotency ref was reused with different safe request semantics."""


class WebHybridExecutionInProgressError(RuntimeError):
    """The same idempotent request already owns the dispatch claim."""


@dataclass
class InMemoryWebCloudCircuitBreaker:
    failure_threshold: int = 2
    review_delay: timedelta = timedelta(minutes=5)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _failure_count: int = field(default=0, init=False, repr=False)
    _state: WebProviderCircuitState = field(
        default=WebProviderCircuitState.closed,
        init=False,
        repr=False,
    )
    _opened_at: datetime | None = field(default=None, init=False, repr=False)
    _reasons: tuple[str, ...] = field(default=(), init=False, repr=False)

    def __post_init__(self) -> None:
        if not 1 <= self.failure_threshold <= 10:
            raise ValueError("WEB_CLOUD_CIRCUIT_THRESHOLD_INVALID")
        if self.review_delay <= timedelta(0):
            raise ValueError("WEB_CLOUD_CIRCUIT_REVIEW_DELAY_INVALID")

    def inspect(self) -> WebCloudCircuitSnapshot:
        with self._lock:
            return self._snapshot()

    def record_failure(
        self,
        outcome: WebProviderAttemptOutcome,
        *,
        now: datetime,
    ) -> WebCloudCircuitSnapshot:
        if outcome not in {
            WebProviderAttemptOutcome.timeout,
            WebProviderAttemptOutcome.connection_failure,
            WebProviderAttemptOutcome.provider_5xx,
            WebProviderAttemptOutcome.quota_blocked,
            WebProviderAttemptOutcome.incomplete_credit_receipt,
        }:
            return self.inspect()
        with self._lock:
            self._failure_count = min(10, self._failure_count + 1)
            self._reasons = tuple(
                dict.fromkeys((*self._reasons, f"CLOUD_{outcome.value.upper()}"))
            )
            if self._failure_count >= self.failure_threshold:
                self._state = WebProviderCircuitState.open
                self._opened_at = self._opened_at or now
            return self._snapshot()

    def close_after_reconciliation(
        self,
        snapshot: WebProviderCreditSnapshot,
        *,
        now: datetime,
    ) -> WebCloudCircuitSnapshot:
        valid = bool(
            snapshot.plan_kind == WebProviderPlanKind.free
            and snapshot.freshness == WebCreditSnapshotFreshness.current
            and snapshot.expires_at > now
            and snapshot.billing_period_start <= now < snapshot.billing_period_end
            and snapshot.max_concurrency is not None
            and snapshot.remaining_credits >= 1
        )
        if not valid:
            return self.inspect()
        with self._lock:
            self._state = WebProviderCircuitState.closed
            self._failure_count = 0
            self._opened_at = None
            self._reasons = ("CLOUD_CIRCUIT_CLOSED_AFTER_RECONCILIATION",)
            return self._snapshot()

    def _snapshot(self) -> WebCloudCircuitSnapshot:
        return WebCloudCircuitSnapshot(
            circuit_ref="web-provider-circuit-ref:firecrawl-cloud:v1",
            state=self._state,
            failure_count=self._failure_count,
            failure_threshold=self.failure_threshold,
            opened_at=self._opened_at,
            review_after=(
                self._opened_at + self.review_delay if self._opened_at else None
            ),
            reason_codes=self._reasons,
        )


@dataclass
class InMemoryWebHybridExecutionLedger:
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _fingerprints: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _results: dict[str, HybridMarkdownExecutionResult] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def replay_or_conflict(
        self,
        request: HybridMarkdownExecutionRequest,
    ) -> HybridMarkdownExecutionResult | None:
        fingerprint = _hybrid_fingerprint(request)
        with self._lock:
            prior = self._fingerprints.get(request.idempotency_ref)
            if prior is None:
                self._fingerprints[request.idempotency_ref] = fingerprint
                return None
            if prior != fingerprint:
                raise WebHybridExecutionConflictError(
                    "WEB_HYBRID_IDEMPOTENCY_SEMANTIC_CONFLICT"
                )
            stored = self._results.get(request.idempotency_ref)
            if stored is None:
                raise WebHybridExecutionInProgressError(
                    "WEB_HYBRID_IDEMPOTENT_REQUEST_IN_PROGRESS"
                )
            return HybridMarkdownExecutionResult.model_validate(
                {
                    **stored.model_dump(mode="python"),
                    "replayed": True,
                    "evidence": None,
                    "reason_codes": tuple(
                        dict.fromkeys(
                            (*stored.reason_codes, "WEB_HYBRID_IDEMPOTENT_REPLAY")
                        )
                    ),
                }
            )

    def record(
        self,
        request: HybridMarkdownExecutionRequest,
        result: HybridMarkdownExecutionResult,
    ) -> None:
        safe_result = HybridMarkdownExecutionResult.model_validate(
            {**result.model_dump(mode="python"), "evidence": None}
        )
        fingerprint = _hybrid_fingerprint(request)
        with self._lock:
            prior = self._fingerprints.get(request.idempotency_ref)
            if prior is not None and prior != fingerprint:
                raise WebHybridExecutionConflictError(
                    "WEB_HYBRID_IDEMPOTENCY_SEMANTIC_CONFLICT"
                )
            self._fingerprints[request.idempotency_ref] = fingerprint
            self._results[request.idempotency_ref] = safe_result


def execute_hybrid_firecrawl_markdown(
    request: HybridMarkdownExecutionRequest,
    *,
    local_capability_state: WebProviderCapabilityState,
    cloud_capability_state: WebProviderCapabilityState,
    credit_snapshot: WebProviderCreditSnapshot,
    credit_ledger: InMemoryWebCreditLedger,
    execution_ledger: InMemoryWebHybridExecutionLedger,
    cloud_circuit: InMemoryWebCloudCircuitBreaker,
    credential: FirecrawlCloudCredential,
    local_approval_authority: LocalApprovalAuthority,
    cloud_approval_authority: LocalApprovalAuthority,
    local_authority_leases: Sequence[AuthorityLease],
    cloud_authority_leases: Sequence[AuthorityLease],
    local_transport: FirecrawlTransport,
    cloud_scrape_transport: CloudScrapeTransport,
    cloud_credit_transport: CreditTransport,
    target_validator: TargetValidator,
    before_fallback: Callable[[], None] | None = None,
    cloud_state_provider: Callable[[], WebProviderCapabilityState] | None = None,
    evaluated_at: datetime | None = None,
) -> HybridMarkdownExecutionResult:
    now = _aware(evaluated_at or datetime.now(timezone.utc))
    replay = execution_ledger.replay_or_conflict(request)
    if replay is not None:
        return replay

    local_result = execute_firecrawl_markdown(
        request.local_request,
        capability_state=local_capability_state,
        approval_authority=local_approval_authority,
        authority_leases=local_authority_leases,
        transport=local_transport,
        target_validator=target_validator,
        evaluated_at=now,
    )
    first_outcome = classify_local_firecrawl_outcome(local_result)
    circuit_snapshot = cloud_circuit.inspect()
    routing = simulate_hybrid_route(
        request_ref=request.request_ref,
        operation=WebProviderOperation.scrape_markdown,
        policy=WebProviderRoutingPolicy.self_host_first_cloud_escalation,
        capability_states=(local_capability_state, cloud_capability_state),
        first_attempt_outcome=first_outcome,
        cloud_snapshot=credit_snapshot,
        cloud_safety_reserve_credits=request.cloud_request.safety_reserve_credits,
        cloud_circuit_state=circuit_snapshot.state,
        now=now,
    )
    cloud_result: FirecrawlCloudExecutionResult | None = None
    if (
        routing.fallback_deployment == WebProviderDeploymentKind.firecrawl_cloud
        and request.cloud_request.routing_decision_ref != routing.decision_ref
    ):
        routing = WebProviderRoutingDecision(
            decision_ref=stable_web_hybrid_ref(
                "web-provider-routing-decision-ref",
                {
                    "request_ref": request.request_ref,
                    "candidate_ref": routing.decision_ref,
                    "provided_ref": request.cloud_request.routing_decision_ref,
                    "status": "scope_mismatch",
                },
            ),
            request_ref=request.request_ref,
            policy=routing.policy,
            operation=routing.operation,
            selected_deployment=routing.selected_deployment,
            fallback_deployment=None,
            attempt_count_ceiling=1,
            reason_codes=routing.reason_codes,
            blocker_codes=tuple(
                dict.fromkeys(
                    (*routing.blocker_codes, "CLOUD_ROUTING_DECISION_REF_MISMATCH")
                )
            ),
        )
    if (
        routing.fallback_deployment == WebProviderDeploymentKind.firecrawl_cloud
        and request.cloud_request.routing_decision_ref == routing.decision_ref
    ):
        if before_fallback is not None:
            before_fallback()
        current_cloud_state = (
            cloud_state_provider() if cloud_state_provider else cloud_capability_state
        )
        cloud_result = execute_firecrawl_cloud_markdown(
            request.cloud_request,
            capability_state=current_cloud_state,
            credit_snapshot=credit_snapshot,
            ledger=credit_ledger,
            credential=credential,
            approval_authority=cloud_approval_authority,
            authority_leases=cloud_authority_leases,
            scrape_transport=cloud_scrape_transport,
            credit_transport=cloud_credit_transport,
            target_validator=target_validator,
            evaluated_at=now,
        )
        cloud_outcome = classify_cloud_firecrawl_outcome(cloud_result)
        if cloud_outcome != WebProviderAttemptOutcome.succeeded:
            cloud_circuit.record_failure(cloud_outcome, now=now)

    result = _hybrid_result(
        request=request,
        routing=routing,
        first_outcome=first_outcome,
        local_result=local_result,
        cloud_result=cloud_result,
    )
    execution_ledger.record(request, result)
    return result


def classify_local_firecrawl_outcome(
    result: FirecrawlMarkdownExecutionResult,
) -> WebProviderAttemptOutcome:
    if (
        result.status
        in {
            WebProviderTransportStatus.succeeded,
            WebProviderTransportStatus.simulated,
        }
        and result.evidence is not None
    ):
        return WebProviderAttemptOutcome.succeeded
    if result.invocation_decision.outcome.value != "allow":
        return WebProviderAttemptOutcome.authority_denied
    codes = set(result.reason_codes) | set(result.blocker_codes)
    if any("PRIVATE" in code or "REDIRECT" in code for code in codes):
        return WebProviderAttemptOutcome.private_target_denied
    if any("DNS_RESOLUTION" in code or "TARGET_VALIDATION" in code for code in codes):
        return WebProviderAttemptOutcome.private_target_denied
    if any("MARKDOWN_REQUIRED" in code or "EMPTY" in code for code in codes):
        return WebProviderAttemptOutcome.empty_content
    if any("TIMEOUT" in code for code in codes):
        return WebProviderAttemptOutcome.timeout
    if any(
        "HTTP_5XX" in code or "RENDER" in code or "RETRY_LIMIT" in code
        for code in codes
    ):
        return WebProviderAttemptOutcome.provider_5xx
    if any("TRANSPORT_FAILED" in code or "CONNECTION" in code for code in codes):
        return WebProviderAttemptOutcome.connection_failure
    if any("LIMIT_EXCEEDED" in code or "TOO_LARGE" in code for code in codes):
        return WebProviderAttemptOutcome.scope_exhausted
    return WebProviderAttemptOutcome.unknown_failure


def classify_cloud_firecrawl_outcome(
    result: FirecrawlCloudExecutionResult,
) -> WebProviderAttemptOutcome:
    if (
        result.status
        in {
            WebProviderTransportStatus.succeeded,
            WebProviderTransportStatus.simulated,
        }
        and result.evidence is not None
    ):
        return WebProviderAttemptOutcome.succeeded
    codes = set(result.reason_codes) | set(result.blocker_codes)
    if any(
        "USAGE_PROOF_INCOMPLETE" in code or "RECEIPT_INCOMPLETE" in code
        for code in codes
    ):
        return WebProviderAttemptOutcome.incomplete_credit_receipt
    if any(
        "CREDIT" in code or "QUOTA" in code or "RATE_LIMIT" in code for code in codes
    ):
        return WebProviderAttemptOutcome.quota_blocked
    if any("PROVIDER_5XX" in code or "HTTP_5XX" in code for code in codes):
        return WebProviderAttemptOutcome.provider_5xx
    if any("TIMEOUT" in code for code in codes):
        return WebProviderAttemptOutcome.timeout
    if any("TRANSPORT_FAILED" in code or "CONNECTION" in code for code in codes):
        return WebProviderAttemptOutcome.connection_failure
    if result.invocation_decision.outcome.value != "allow":
        return WebProviderAttemptOutcome.authority_denied
    return WebProviderAttemptOutcome.unknown_failure


def _hybrid_result(
    *,
    request: HybridMarkdownExecutionRequest,
    routing: WebProviderRoutingDecision,
    first_outcome: WebProviderAttemptOutcome,
    local_result: FirecrawlMarkdownExecutionResult,
    cloud_result: FirecrawlCloudExecutionResult | None,
) -> HybridMarkdownExecutionResult:
    selected_result = cloud_result or local_result
    succeeded = bool(
        selected_result.status
        in {WebProviderTransportStatus.succeeded, WebProviderTransportStatus.simulated}
        and selected_result.evidence is not None
    )
    final_deployment = None
    if succeeded:
        final_deployment = (
            WebProviderDeploymentKind.firecrawl_cloud
            if cloud_result is not None
            else WebProviderDeploymentKind.firecrawl_self_hosted
        )
    reason_codes = tuple(
        dict.fromkeys(
            (
                *routing.reason_codes,
                *local_result.reason_codes,
                *(cloud_result.reason_codes if cloud_result else ()),
            )
        )
    )
    blocker_codes = tuple(
        dict.fromkeys(
            (
                *routing.blocker_codes,
                *local_result.blocker_codes,
                *(cloud_result.blocker_codes if cloud_result else ()),
            )
        )
    )
    status = selected_result.status
    evidence = selected_result.evidence if succeeded else None
    return HybridMarkdownExecutionResult(
        request_ref=request.request_ref,
        idempotency_ref=request.idempotency_ref,
        execution_receipt_ref=stable_web_hybrid_ref(
            "hybrid-execution-receipt-ref",
            {
                "request_ref": request.request_ref,
                "routing_ref": routing.decision_ref,
                "local_receipt_ref": local_result.transport_receipt.receipt_ref,
                "cloud_receipt_ref": (
                    cloud_result.transport_receipt.receipt_ref if cloud_result else None
                ),
                "status": status.value,
            },
        ),
        routing_decision=routing,
        first_attempt_outcome=first_outcome,
        final_deployment=final_deployment,
        status=status,
        attempt_count=2 if cloud_result is not None else 1,
        local_receipt=local_result.transport_receipt,
        cloud_receipt=cloud_result.transport_receipt if cloud_result else None,
        evidence=evidence,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
    )


def _hybrid_fingerprint(request: HybridMarkdownExecutionRequest) -> str:
    return stable_web_hybrid_ref(
        "hybrid-request-fingerprint-ref",
        {
            "request_ref": request.request_ref,
            "idempotency_ref": request.idempotency_ref,
            "policy": request.policy.value,
            "target_source_ref": request.local_request.target_source_ref,
            "local_request_ref": request.local_request.request_ref,
            "cloud_request_ref": request.cloud_request.request_ref,
            "cloud_routing_ref": request.cloud_request.routing_decision_ref,
            "max_attempts": request.max_attempts,
        },
    )


def _aware(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("WEB_HYBRID_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)


__all__ = [
    "HybridMarkdownExecutionRequest",
    "HybridMarkdownExecutionResult",
    "InMemoryWebCloudCircuitBreaker",
    "InMemoryWebHybridExecutionLedger",
    "WebCloudCircuitSnapshot",
    "WebHybridExecutionConflictError",
    "WebHybridExecutionInProgressError",
    "classify_cloud_firecrawl_outcome",
    "classify_local_firecrawl_outcome",
    "execute_hybrid_firecrawl_markdown",
]
