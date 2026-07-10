"""Exact authenticated Firecrawl Cloud free-plan markdown lane.

Credential material is resolved from one operator-configured ignored file and
remains transient. Provider account reads and one-page markdown extraction use
fixed official endpoints. A current free-plan snapshot, atomic reservation,
exact approval, exact AuthorityLease, and request-scoped budget decision are
required before one provider scrape attempt.
"""

from __future__ import annotations

import json
import os
import re
import socket
import ssl
import stat
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityPrivacyLevel,
    CoordinationMode,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.approval import LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    RuntimePolicy,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capability_availability import (
    CapabilityAvailabilitySnapshot,
    CapabilityInvocationDecision,
    CapabilityInvocationRequest,
    CostPosture,
    DerivedRuntimeReadinessStatus,
    IdempotencyPosture,
    InvocationDecisionOutcome,
    SafeDisableStatus,
    build_capability_availability_snapshot,
    evaluate_capability_invocation,
)
from ultimate_ai_agent.core.costs.decisions import CostDecision
from ultimate_ai_agent.core.costs.enums import BudgetStatus
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.time import utc_now

from .firecrawl_markdown import (
    FirecrawlMarkdownEvidence,
    FirecrawlMarkdownRequest,
    FirecrawlTransportError,
    TargetValidator,
    authority_decision_has_exact_resource_scope,
    execute_authorized_firecrawl_markdown_attempt,
    validate_resolved_public_target,
)
from .hybrid_contracts import (
    WEB_HYBRID_COST_POLICY_REF,
    WebCreditReservationStatus,
    WebCreditSnapshotFreshness,
    WebProviderCapabilityState,
    WebProviderCreditReservation,
    WebProviderCreditReservationRequest,
    WebProviderCreditSnapshot,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderPlanKind,
    WebProviderTransportMethod,
    WebProviderTransportReceipt,
    WebProviderTransportStatus,
    stable_web_hybrid_ref,
)
from .hybrid_ledger import InMemoryWebCreditLedger


FIRECRAWL_CLOUD_PROVIDER_REF = "web-provider-ref:firecrawl-cloud"
FIRECRAWL_CLOUD_ADAPTER_REF = "web-adapter-ref:firecrawl-cloud-markdown:v1"
FIRECRAWL_CLOUD_CAPABILITY_REF = "capability-ref:web-access:firecrawl-cloud-markdown:v1"
FIRECRAWL_CLOUD_LANE_REF = "web-lane-ref:firecrawl-cloud-markdown:v1"
FIRECRAWL_CLOUD_ENDPOINT_REF = "configured-endpoint-ref:firecrawl:cloud-v2"
FIRECRAWL_CLOUD_CREDENTIAL_REF = "credential-ref:firecrawl-cloud:ignored-local-file"
FIRECRAWL_CLOUD_ACCOUNT_REF = "provider-account-ref:firecrawl:authenticated-team"
FIRECRAWL_CLOUD_CREDIT_SCHEMA_REF = "request-schema-ref:firecrawl-credit-usage:v2"
FIRECRAWL_CLOUD_SCRAPE_SCHEMA_REF = "request-schema-ref:firecrawl-scrape:v2"
FIRECRAWL_CLOUD_CREDIT_PATH = "/v2/team/credit-usage"
FIRECRAWL_CLOUD_SCRAPE_PATH = "/v2/scrape"
FIRECRAWL_CLOUD_BASE_URL = "https://api.firecrawl.dev"
FIRECRAWL_FREE_PLAN_CREDITS = 1_000
FIRECRAWL_FREE_PLAN_CONCURRENCY = 2
FIRECRAWL_STANDARD_SCRAPE_CREDITS = 1
FIRECRAWL_CREDIT_SNAPSHOT_TTL = timedelta(minutes=5)
FIRECRAWL_CLOUD_DEFAULT_SECRET_FILE = Path(
    ".uaa/local-web-services/firecrawl_cloud_api_key"
)
_MAX_PROVIDER_RESPONSE_BYTES = 2_000_000


@dataclass(frozen=True)
class FirecrawlCloudCredential:
    """Transient secret plus safe refs; repr never includes credential material."""

    value: SecretStr = field(repr=False)
    credential_ref: str = FIRECRAWL_CLOUD_CREDENTIAL_REF
    source_ref: str = "secret-source-ref:firecrawl-cloud:ignored-local-file"


class FirecrawlCloudMarkdownRequest(FirecrawlMarkdownRequest):
    idempotency_ref: str
    routing_decision_ref: str
    run_credit_ceiling: int = Field(default=10, ge=1, le=100)
    safety_reserve_credits: int = Field(default=1, ge=0, le=100)

    @field_validator("idempotency_ref", "routing_decision_ref")
    @classmethod
    def validate_cloud_refs(cls, value: str) -> str:
        validate_execution_ref(value, "firecrawl_cloud_request_ref")
        return value


class FirecrawlCloudCreditReconciliationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    status: WebProviderTransportStatus
    reconciliation_receipt_ref: str
    snapshot: WebProviderCreditSnapshot | None = None
    reason_codes: tuple[str, ...] = ()
    network_call_performed: bool = False
    raw_provider_payload_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False
    local_path_stored: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "FirecrawlCloudCreditReconciliationResult":
        validate_execution_ref(
            self.reconciliation_receipt_ref,
            "firecrawl_cloud_credit_receipt_ref",
        )
        if (
            self.status
            in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            and self.snapshot is None
        ):
            raise ValueError("FIRECRAWL_CLOUD_CREDIT_SUCCESS_SNAPSHOT_REQUIRED")
        if (
            self.status
            not in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            and self.snapshot is not None
        ):
            raise ValueError("FIRECRAWL_CLOUD_CREDIT_FAILED_SNAPSHOT_DENIED")
        if (
            self.status == WebProviderTransportStatus.simulated
            and self.network_call_performed
        ):
            raise ValueError("FIRECRAWL_CLOUD_CREDIT_SIMULATED_NETWORK_DENIED")
        return self


class FirecrawlCloudExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    request_ref: str
    task_ref: str
    invocation_decision: CapabilityInvocationDecision
    transport_receipt: WebProviderTransportReceipt
    reservation: WebProviderCreditReservation | None = None
    credit_snapshot_before_ref: str | None = None
    credit_snapshot_after_ref: str | None = None
    gateway_audit_ref: str
    status: WebProviderTransportStatus
    evidence: FirecrawlMarkdownEvidence | None = None
    execution_succeeded: bool = False
    reason_codes: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = ()
    content_untrusted: Literal[True] = True
    instruction_use_allowed: Literal[False] = False
    raw_target_stored: Literal[False] = False
    raw_page_stored: Literal[False] = False
    raw_provider_payload_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False
    local_path_stored: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "FirecrawlCloudExecutionResult":
        for value in (self.request_ref, self.task_ref, self.gateway_audit_ref):
            validate_execution_ref(value, "firecrawl_cloud_execution_ref")
        if self.execution_succeeded != (
            self.status == WebProviderTransportStatus.succeeded
        ):
            raise ValueError("FIRECRAWL_CLOUD_EXECUTION_STATUS_MISMATCH")
        if self.execution_succeeded:
            if self.invocation_decision.outcome != InvocationDecisionOutcome.allow:
                raise ValueError("FIRECRAWL_CLOUD_EXECUTION_AUTHORITY_REQUIRED")
            if (
                self.reservation is None
                or self.reservation.status != WebCreditReservationStatus.settled
                or self.credit_snapshot_after_ref is None
            ):
                raise ValueError("FIRECRAWL_CLOUD_EXECUTION_USAGE_PROOF_REQUIRED")
        if (
            self.status
            not in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            and self.evidence is not None
        ):
            raise ValueError("FIRECRAWL_CLOUD_FAILED_EVIDENCE_DENIED")
        return self


class FirecrawlCloudTransportError(RuntimeError):
    def __init__(self, code: str, *, network_call_performed: bool) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,159}", code):
            raise ValueError("FIRECRAWL_CLOUD_TRANSPORT_CODE_UNSAFE")
        super().__init__(code)
        self.code = code
        self.network_call_performed = network_call_performed


CreditTransport = Callable[[FirecrawlCloudCredential], Mapping[str, Any]]
CloudScrapeTransport = Callable[
    [FirecrawlMarkdownRequest, FirecrawlCloudCredential], Mapping[str, Any]
]


def resolve_firecrawl_cloud_credential(
    secret_file: Path = FIRECRAWL_CLOUD_DEFAULT_SECRET_FILE,
) -> FirecrawlCloudCredential:
    """Resolve the exact ignored credential without returning path metadata."""

    path = Path(secret_file)
    if tuple(path.parts[-3:]) != (
        ".uaa",
        "local-web-services",
        "firecrawl_cloud_api_key",
    ):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDENTIAL_SOURCE_DENIED",
            network_call_performed=False,
        )
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDENTIAL_UNAVAILABLE",
            network_call_performed=False,
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_CREDENTIAL_FILE_MODE_DENIED",
                network_call_performed=False,
            )
        raw = os.read(descriptor, 257)
    finally:
        os.close(descriptor)
    value = raw.rstrip(b"\r\n")
    if (
        len(raw) > 256
        or not 20 <= len(value) <= 128
        or any(byte < 33 or byte > 126 for byte in value)
    ):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDENTIAL_FORMAT_INVALID",
            network_call_performed=False,
        )
    try:
        decoded = value.decode("ascii")
    except UnicodeDecodeError as exc:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDENTIAL_FORMAT_INVALID",
            network_call_performed=False,
        ) from exc
    return FirecrawlCloudCredential(value=SecretStr(decoded))


def build_firecrawl_cloud_credit_transport() -> CreditTransport:
    def transport(credential: FirecrawlCloudCredential) -> Mapping[str, Any]:
        return _cloud_json_request(
            path=FIRECRAWL_CLOUD_CREDIT_PATH,
            method="GET",
            credential=credential,
            payload=None,
        )

    transport.real_world_transport_performed = True  # type: ignore[attr-defined]
    return transport


def build_firecrawl_cloud_scrape_transport() -> CloudScrapeTransport:
    def transport(
        request: FirecrawlMarkdownRequest,
        credential: FirecrawlCloudCredential,
    ) -> Mapping[str, Any]:
        return _cloud_json_request(
            path=FIRECRAWL_CLOUD_SCRAPE_PATH,
            method="POST",
            credential=credential,
            payload=build_firecrawl_cloud_scrape_payload(request),
        )

    transport.real_world_transport_performed = True  # type: ignore[attr-defined]
    return transport


def build_firecrawl_cloud_scrape_payload(
    request: FirecrawlMarkdownRequest,
) -> dict[str, Any]:
    return {
        "url": request.target_url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "maxAge": 0,
        "waitFor": 0,
        "timeout": 15_000,
        "removeBase64Images": True,
        "blockAds": True,
        "proxy": "basic",
        "storeInCache": False,
    }


def reconcile_firecrawl_cloud_credits(
    credential: FirecrawlCloudCredential,
    *,
    transport: CreditTransport | None = None,
    fetched_at: datetime | None = None,
) -> FirecrawlCloudCreditReconciliationResult:
    now = _aware(fetched_at or utc_now())
    selected_transport = transport or build_firecrawl_cloud_credit_transport()
    live_transport = bool(
        getattr(selected_transport, "real_world_transport_performed", False)
    )
    try:
        payload = selected_transport(credential)
        snapshot = _normalize_credit_payload(payload, fetched_at=now)
    except FirecrawlCloudTransportError as exc:
        return _credit_failure(
            exc.code,
            network_call_performed=exc.network_call_performed and live_transport,
            fetched_at=now,
        )
    except Exception:  # noqa: BLE001 - raw provider/credential detail stays private.
        return _credit_failure(
            "FIRECRAWL_CLOUD_CREDIT_RECONCILIATION_FAILED",
            network_call_performed=live_transport,
            fetched_at=now,
        )
    return FirecrawlCloudCreditReconciliationResult(
        status=(
            WebProviderTransportStatus.succeeded
            if live_transport
            else WebProviderTransportStatus.simulated
        ),
        reconciliation_receipt_ref=stable_web_hybrid_ref(
            "web-credit-reconciliation-receipt-ref",
            {
                "snapshot_ref": snapshot.snapshot_ref,
                "fetched_at": now,
            },
        ),
        snapshot=snapshot,
        reason_codes=("FIRECRAWL_CLOUD_CREDIT_SNAPSHOT_NORMALIZED",),
        network_call_performed=live_transport,
    )


def build_firecrawl_cloud_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=FIRECRAWL_CLOUD_CAPABILITY_REF,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="Firecrawl Cloud governed one-page markdown extraction",
        description="Spend one reserved free-plan credit for one approved public page.",
        examples=["Extract one approved page using one reserved free credit."],
        anti_examples=["Do not use paid plans, enhanced proxies, actions, or retries."],
        input_schema={"type": "object", "additionalProperties": False},
        output_schema={"type": "object", "additionalProperties": False},
        input_modes=["ephemeral_target_url", "safe_target_source_ref"],
        output_modes=["transient_untrusted_markdown", "redacted_usage_receipt"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.high,
        authority_level=CapabilityAuthorityLevel.read_only,
        approval_required=True,
        deterministic=False,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_cost_class=CapabilityCostClass.low,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=True,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        runtime_policy=RuntimePolicy(
            timeout_seconds=60,
            max_retries=0,
            max_concurrency=1,
            deterministic=False,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            approval_required=True,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=SideEffectLevel.read,
        ),
    )


def firecrawl_cloud_snapshot_from_state(
    state: WebProviderCapabilityState,
) -> CapabilityAvailabilitySnapshot:
    if (
        state.provider_ref != FIRECRAWL_CLOUD_PROVIDER_REF
        or state.deployment != WebProviderDeploymentKind.firecrawl_cloud
        or state.operation != WebProviderOperation.scrape_markdown
    ):
        raise ValueError("FIRECRAWL_CLOUD_CAPABILITY_STATE_SCOPE_MISMATCH")
    return build_capability_availability_snapshot(
        snapshot_ref=stable_web_hybrid_ref(
            "capability-availability-ref",
            {
                "state_ref": state.state_ref,
                "capability_ref": FIRECRAWL_CLOUD_CAPABILITY_REF,
            },
        ),
        capability_ref=FIRECRAWL_CLOUD_CAPABILITY_REF,
        provider_ref=state.provider_ref,
        adapter_ref=FIRECRAWL_CLOUD_ADAPTER_REF,
        catalog_status=state.catalog_status,
        compatibility_status=state.compatibility_status,
        configuration_status=state.configuration_status,
        health_status=state.health_status,
        authority_posture=state.authority_posture,
        resource_status=state.resource_status,
        cost_posture=CostPosture.metered,
        safe_disable_status=state.safe_disable_status,
        checked_at=state.observed_at,
        expires_at=state.expires_at,
        freshness_status=state.freshness_status,
        declared_or_observed_version_ref=state.version_ref,
        reason_codes=list(state.reason_codes),
        blocker_codes=list(state.blocker_codes),
        evidence_refs=[state.state_ref],
        source_ref=state.state_ref,
        safe_summary="Cloud readiness and free-credit truth do not grant request authority.",
    )


def execute_firecrawl_cloud_markdown(
    request: FirecrawlCloudMarkdownRequest,
    *,
    capability_state: WebProviderCapabilityState,
    credit_snapshot: WebProviderCreditSnapshot | None,
    ledger: InMemoryWebCreditLedger,
    credential: FirecrawlCloudCredential,
    approval_authority: LocalApprovalAuthority,
    authority_leases: Sequence[AuthorityLease],
    scrape_transport: CloudScrapeTransport | None = None,
    credit_transport: CreditTransport | None = None,
    target_validator: TargetValidator | None = None,
    evaluated_at: datetime | None = None,
) -> FirecrawlCloudExecutionResult:
    now = _aware(evaluated_at or utc_now())
    snapshot = firecrawl_cloud_snapshot_from_state(capability_state)
    manifest = build_firecrawl_cloud_capability_manifest()
    task = TaskEnvelope(
        task_id=request.task_ref,
        user_request="Execute one exact governed cloud markdown extraction.",
        objective="Return transient evidence with complete free-credit proof.",
        selected_capability_ids=[FIRECRAWL_CLOUD_CAPABILITY_REF],
        context={"approval_ref": request.approval_ref} if request.approval_ref else {},
    )
    context: dict[str, Any] = {"coordination_mode": CoordinationMode.direct_tool.value}
    if request.approval_ref:
        context["approval_ref"] = request.approval_ref
    local_approval = approval_authority.validate_approval(manifest, task, context)
    policy_decision = PolicyEngine(approval_authority=approval_authority).can_execute(
        manifest,
        task,
        context,
    )
    exact_refs = _exact_cloud_resource_refs(request, credit_snapshot)
    observed_authority = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref=stable_web_hybrid_ref(
                "authority-action-ref",
                {"request_ref": request.request_ref, "task_ref": request.task_ref},
            ),
            domain=AuthorityDomain.browser,
            capability=AuthorityCapability.read,
            safe_summary="Evaluate one exact free-plan cloud extraction attempt.",
            resource_refs=list(exact_refs),
            capability_ref=FIRECRAWL_CLOUD_CAPABILITY_REF,
            lane_ref=FIRECRAWL_CLOUD_LANE_REF,
            adapter_ref=FIRECRAWL_CLOUD_ADAPTER_REF,
            rollback_ref="rollback-ref:web-access:firecrawl-cloud:disable",
            safe_disable_ref="safe-disable-ref:web-access:firecrawl-cloud",
        ),
        list(authority_leases),
        now=now,
    )
    authority_decision = (
        observed_authority
        if authority_decision_has_exact_resource_scope(
            observed_authority,
            authority_leases,
            exact_refs,
        )
        else None
    )

    reservation: WebProviderCreditReservation | None = None
    preflight_reasons = _cloud_preflight_reasons(
        snapshot=snapshot,
        credit_snapshot=credit_snapshot,
        credential=credential,
        request=request,
        policy_allowed=policy_decision.allowed,
        approval_allowed=local_approval.allowed,
        authority_allowed=authority_decision is not None,
        now=now,
    )
    if not preflight_reasons:
        validator = target_validator or validate_resolved_public_target
        try:
            validator(request.target_url)
        except Exception:  # noqa: BLE001 - target validation detail stays private.
            preflight_reasons.append("FIRECRAWL_TARGET_VALIDATION_FAILED")
    if not preflight_reasons and credit_snapshot is not None:
        ledger.reconcile(credit_snapshot)
        reservation = ledger.reserve(
            WebProviderCreditReservationRequest(
                request_ref=request.request_ref,
                idempotency_ref=request.idempotency_ref,
                provider_ref=FIRECRAWL_CLOUD_PROVIDER_REF,
                snapshot_ref=credit_snapshot.snapshot_ref,
                billing_period_ref=credit_snapshot.billing_period_ref,
                routing_decision_ref=request.routing_decision_ref,
                estimated_credits=FIRECRAWL_STANDARD_SCRAPE_CREDITS,
                safety_reserve_credits=request.safety_reserve_credits,
                run_credit_ceiling=request.run_credit_ceiling,
            ),
            now=now,
        )
        preflight_reasons.extend(reservation.reason_codes)

    budget_decision = _budget_decision(request, reservation, preflight_reasons)
    invocation_request = CapabilityInvocationRequest(
        request_ref=request.request_ref,
        snapshot_ref=snapshot.snapshot_ref,
        capability_ref=FIRECRAWL_CLOUD_CAPABILITY_REF,
        provider_ref=FIRECRAWL_CLOUD_PROVIDER_REF,
        adapter_ref=FIRECRAWL_CLOUD_ADAPTER_REF,
        task_ref=request.task_ref,
        approval_ref=request.approval_ref,
        budget_decision_ref=f"budget-decision-ref:{budget_decision.decision_id}",
        authority_lease_required=True,
        local_approval_required=True,
        idempotency_posture=IdempotencyPosture.validated,
        expected_execution_receipt_ref=request.expected_execution_receipt_ref,
    )
    invocation = evaluate_capability_invocation(
        request=invocation_request,
        snapshot=snapshot,
        policy_decision=policy_decision,
        authority_decision=authority_decision,
        local_approval_decision=local_approval,
        budget_decision=budget_decision,
        evaluated_at=now,
    )
    if invocation.outcome != InvocationDecisionOutcome.allow:
        if (
            reservation is not None
            and reservation.status == WebCreditReservationStatus.reserved
        ):
            reservation = ledger.release(reservation.reservation_ref)
        return _cloud_result(
            request=request,
            invocation=invocation,
            reservation=reservation,
            credit_before=credit_snapshot,
            credit_after=None,
            status=WebProviderTransportStatus.blocked,
            evidence=None,
            network_call_performed=False,
            reason_codes=tuple(
                dict.fromkeys((*preflight_reasons, *invocation.reason_codes))
            ),
            blocker_codes=tuple(invocation.blocker_codes),
            gateway_audit_ref=stable_web_hybrid_ref(
                "web-access-audit-ref",
                {
                    "request_ref": request.request_ref,
                    "outcome": invocation.outcome.value,
                },
            ),
            created_at=now,
        )

    selected_scrape = scrape_transport or build_firecrawl_cloud_scrape_transport()

    def bound_transport(extract_request: FirecrawlMarkdownRequest) -> Mapping[str, Any]:
        try:
            return selected_scrape(extract_request, credential)
        except FirecrawlCloudTransportError as exc:
            raise FirecrawlTransportError(
                exc.code,
                network_call_performed=exc.network_call_performed,
            ) from exc

    bound_transport.real_world_transport_performed = bool(  # type: ignore[attr-defined]
        getattr(selected_scrape, "real_world_transport_performed", False)
    )
    attempt = execute_authorized_firecrawl_markdown_attempt(
        request=request,
        invocation_decision=invocation,
        capability_ref=FIRECRAWL_CLOUD_CAPABILITY_REF,
        provider_ref=FIRECRAWL_CLOUD_PROVIDER_REF,
        adapter_ref=FIRECRAWL_CLOUD_ADAPTER_REF,
        transport=bound_transport,
        target_validator=target_validator or validate_resolved_public_target,
    )
    after_snapshot: WebProviderCreditSnapshot | None = None
    final_status = attempt.status
    final_evidence = attempt.evidence
    final_reasons = list(attempt.reason_codes)
    if (
        reservation is not None
        and reservation.status == WebCreditReservationStatus.reserved
    ):
        if (
            attempt.network_call_performed
            or attempt.status == WebProviderTransportStatus.simulated
        ):
            reconciled = reconcile_firecrawl_cloud_credits(
                credential,
                transport=credit_transport,
                fetched_at=now + timedelta(seconds=1),
            )
            after_snapshot = reconciled.snapshot
            actual_usage_ref, actual_credits = _actual_usage(
                credit_snapshot,
                after_snapshot,
                allowed_credits=(
                    {FIRECRAWL_STANDARD_SCRAPE_CREDITS}
                    if attempt.status
                    in {
                        WebProviderTransportStatus.succeeded,
                        WebProviderTransportStatus.simulated,
                    }
                    else {0, FIRECRAWL_STANDARD_SCRAPE_CREDITS}
                ),
            )
            reservation = ledger.settle(
                reservation.reservation_ref,
                actual_credits=actual_credits,
                actual_usage_ref=actual_usage_ref,
            )
            if after_snapshot is not None:
                ledger.reconcile(after_snapshot)
            if reservation.status != WebCreditReservationStatus.settled:
                final_status = WebProviderTransportStatus.failed
                final_evidence = None
                final_reasons.append("FIRECRAWL_CLOUD_USAGE_PROOF_INCOMPLETE")
        else:
            reservation = ledger.release(reservation.reservation_ref)
    return _cloud_result(
        request=request,
        invocation=invocation,
        reservation=reservation,
        credit_before=credit_snapshot,
        credit_after=after_snapshot,
        status=final_status,
        evidence=final_evidence,
        network_call_performed=attempt.network_call_performed,
        reason_codes=tuple(dict.fromkeys(final_reasons)),
        blocker_codes=()
        if final_status
        in {WebProviderTransportStatus.succeeded, WebProviderTransportStatus.simulated}
        else tuple(dict.fromkeys(final_reasons)),
        gateway_audit_ref=attempt.gateway_audit_ref,
        created_at=now,
    )


def _cloud_json_request(
    *,
    path: str,
    method: str,
    credential: FirecrawlCloudCredential,
    payload: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if path not in {FIRECRAWL_CLOUD_CREDIT_PATH, FIRECRAWL_CLOUD_SCRAPE_PATH}:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_ENDPOINT_DENIED",
            network_call_performed=False,
        )
    body = b""
    if payload is not None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    header_lines = [
        f"{method} {path} HTTP/1.1",
        "Host: api.firecrawl.dev",
        "Accept: application/json",
        "Accept-Encoding: identity",
        f"Authorization: Bearer {credential.value.get_secret_value()}",
        "User-Agent: ultimate-ai-agent-firecrawl-cloud/1",
        "Connection: close",
    ]
    if body:
        header_lines.extend(
            [
                "Content-Type: application/json",
                f"Content-Length: {len(body)}",
            ]
        )
    request_bytes = ("\r\n".join(header_lines) + "\r\n\r\n").encode("ascii") + body
    attempted = False
    try:
        attempted = True
        context = ssl.create_default_context()
        with socket.create_connection(
            ("api.firecrawl.dev", 443), timeout=45
        ) as raw_socket:
            with context.wrap_socket(
                raw_socket,
                server_hostname="api.firecrawl.dev",
            ) as connection:
                connection.settimeout(45)
                connection.sendall(request_bytes)
                status, headers, raw = _read_cloud_response(connection)
    except FirecrawlCloudTransportError:
        raise
    except (OSError, TimeoutError, ssl.SSLError) as exc:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_TRANSPORT_FAILED",
            network_call_performed=attempted,
        ) from exc
    if status != 200:
        raise FirecrawlCloudTransportError(
            _cloud_provider_error_code(status, raw, headers),
            network_call_performed=True,
        )
    if (
        headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "application/json"
    ):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_JSON_RESPONSE_REQUIRED",
            network_call_performed=True,
        )
    if len(raw) > _MAX_PROVIDER_RESPONSE_BYTES:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_TOO_LARGE",
            network_call_performed=True,
        )
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_JSON_INVALID",
            network_call_performed=True,
        ) from exc
    if not isinstance(decoded, Mapping):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_OBJECT_REQUIRED",
            network_call_performed=True,
        )
    return decoded


def _read_cloud_response(
    connection: ssl.SSLSocket,
) -> tuple[int, dict[str, str], bytes]:
    raw = bytearray()
    header_end = -1
    while header_end < 0:
        chunk = connection.recv(4096)
        if not chunk:
            break
        raw.extend(chunk)
        header_end = raw.find(b"\r\n\r\n")
        if len(raw) > 32_768:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_RESPONSE_HEADERS_TOO_LARGE",
                network_call_performed=True,
            )
    if header_end < 0:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_HEADERS_INVALID",
            network_call_performed=True,
        )
    status, headers = _parse_cloud_headers(bytes(raw[:header_end]))
    response_body = bytearray(raw[header_end + 4 :])
    while len(response_body) <= _MAX_PROVIDER_RESPONSE_BYTES:
        chunk = connection.recv(
            min(8192, _MAX_PROVIDER_RESPONSE_BYTES + 1 - len(response_body))
        )
        if not chunk:
            break
        response_body.extend(chunk)
    if len(response_body) > _MAX_PROVIDER_RESPONSE_BYTES:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_TOO_LARGE",
            network_call_performed=True,
        )
    if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_ENCODING_DENIED",
            network_call_performed=True,
        )
    transfer = headers.get("transfer-encoding", "").lower()
    body = bytes(response_body)
    if transfer == "chunked":
        body = _decode_chunked_body(body)
    elif transfer not in {"", "identity"}:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_TRANSFER_ENCODING_DENIED",
            network_call_performed=True,
        )
    content_length = headers.get("content-length")
    if content_length is not None:
        try:
            expected_length = int(content_length)
        except ValueError as exc:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_CONTENT_LENGTH_INVALID",
                network_call_performed=True,
            ) from exc
        if expected_length != len(body):
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_RESPONSE_TRUNCATED",
                network_call_performed=True,
            )
    return status, headers, body


def _parse_cloud_headers(header_bytes: bytes) -> tuple[int, dict[str, str]]:
    try:
        lines = header_bytes.decode("iso-8859-1").split("\r\n")
        status_parts = lines[0].split(None, 2)
        status = int(status_parts[1])
    except (IndexError, UnicodeDecodeError, ValueError) as exc:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_STATUS_INVALID",
            network_call_performed=True,
        ) from exc
    if len(status_parts) < 2 or not status_parts[0].startswith("HTTP/"):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_RESPONSE_STATUS_INVALID",
            network_call_performed=True,
        )
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_RESPONSE_HEADERS_INVALID",
                network_call_performed=True,
            )
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return status, headers


def _decode_chunked_body(value: bytes) -> bytes:
    decoded = bytearray()
    cursor = 0
    while True:
        line_end = value.find(b"\r\n", cursor)
        if line_end < 0:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_CHUNKED_BODY_INVALID",
                network_call_performed=True,
            )
        size_text = value[cursor:line_end].split(b";", 1)[0]
        try:
            size = int(size_text, 16)
        except ValueError as exc:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_CHUNKED_BODY_INVALID",
                network_call_performed=True,
            ) from exc
        cursor = line_end + 2
        if size == 0:
            return bytes(decoded)
        end = cursor + size
        if end + 2 > len(value) or value[end : end + 2] != b"\r\n":
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_CHUNKED_BODY_INVALID",
                network_call_performed=True,
            )
        decoded.extend(value[cursor:end])
        if len(decoded) > _MAX_PROVIDER_RESPONSE_BYTES:
            raise FirecrawlCloudTransportError(
                "FIRECRAWL_CLOUD_RESPONSE_TOO_LARGE",
                network_call_performed=True,
            )
        cursor = end + 2


def _normalize_credit_payload(
    payload: Mapping[str, Any],
    *,
    fetched_at: datetime,
) -> WebProviderCreditSnapshot:
    data = payload.get("data")
    if payload.get("success") is not True or not isinstance(data, Mapping):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDIT_PAYLOAD_INVALID",
            network_call_performed=True,
        )
    plan_credits = _strict_nonnegative_int(data.get("planCredits"))
    remaining_credits = _strict_nonnegative_int(data.get("remainingCredits"))
    start = _provider_datetime(data.get("billingPeriodStart"))
    end = _provider_datetime(data.get("billingPeriodEnd"))
    if not start <= fetched_at < end:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDIT_STATE_INVALID",
            network_call_performed=True,
        )
    plan_kind = (
        WebProviderPlanKind.free
        if plan_credits == FIRECRAWL_FREE_PLAN_CREDITS
        else (
            WebProviderPlanKind.paid
            if plan_credits > FIRECRAWL_FREE_PLAN_CREDITS
            else WebProviderPlanKind.unknown
        )
    )
    max_concurrency = (
        FIRECRAWL_FREE_PLAN_CONCURRENCY
        if plan_kind == WebProviderPlanKind.free
        else None
    )
    billing_ref = stable_web_hybrid_ref(
        "billing-period-ref:firecrawl",
        {"start": start, "end": end},
    )
    normalized = {
        "plan_kind": plan_kind.value,
        "plan_credits": plan_credits,
        "remaining_credits": remaining_credits,
        "billing_period_ref": billing_ref,
        "billing_period_start": start,
        "billing_period_end": end,
        "fetched_at": fetched_at,
    }
    response_ref = stable_web_hybrid_ref(
        "provider-response-receipt-hash-ref:credit-usage",
        normalized,
    )
    return WebProviderCreditSnapshot(
        snapshot_ref=stable_web_hybrid_ref("web-credit-snapshot-ref", normalized),
        provider_ref=FIRECRAWL_CLOUD_PROVIDER_REF,
        account_ref=FIRECRAWL_CLOUD_ACCOUNT_REF,
        credential_ref=FIRECRAWL_CLOUD_CREDENTIAL_REF,
        plan_kind=plan_kind,
        plan_credits=plan_credits,
        remaining_credits=remaining_credits,
        max_concurrency=max_concurrency,
        billing_period_ref=billing_ref,
        billing_period_start=start,
        billing_period_end=end,
        fetched_at=fetched_at,
        expires_at=min(end, fetched_at + FIRECRAWL_CREDIT_SNAPSHOT_TTL),
        freshness=WebCreditSnapshotFreshness.current,
        response_receipt_hash_ref=response_ref,
    )


def _cloud_preflight_reasons(
    *,
    snapshot: CapabilityAvailabilitySnapshot,
    credit_snapshot: WebProviderCreditSnapshot | None,
    credential: FirecrawlCloudCredential,
    request: FirecrawlCloudMarkdownRequest,
    policy_allowed: bool,
    approval_allowed: bool,
    authority_allowed: bool,
    now: datetime,
) -> list[str]:
    reasons: list[str] = []
    if snapshot.runtime_readiness_status != DerivedRuntimeReadinessStatus.ready:
        reasons.append("FIRECRAWL_CLOUD_RUNTIME_NOT_READY")
    if snapshot.safe_disable_status != SafeDisableStatus.inactive:
        reasons.append("FIRECRAWL_CLOUD_SAFE_DISABLED")
    if not policy_allowed:
        reasons.append("FIRECRAWL_CLOUD_POLICY_DENIED")
    if not approval_allowed:
        reasons.append("FIRECRAWL_CLOUD_APPROVAL_REQUIRED")
    if not authority_allowed:
        reasons.append("FIRECRAWL_CLOUD_EXACT_LEASE_REQUIRED")
    if credential.credential_ref != FIRECRAWL_CLOUD_CREDENTIAL_REF:
        reasons.append("FIRECRAWL_CLOUD_CREDENTIAL_REF_MISMATCH")
    if credit_snapshot is None:
        reasons.append("CLOUD_CREDIT_SNAPSHOT_MISSING")
    else:
        if credit_snapshot.provider_ref != FIRECRAWL_CLOUD_PROVIDER_REF:
            reasons.append("CLOUD_CREDIT_PROVIDER_MISMATCH")
        if credit_snapshot.credential_ref != credential.credential_ref:
            reasons.append("CLOUD_CREDIT_CREDENTIAL_MISMATCH")
        if credit_snapshot.plan_kind != WebProviderPlanKind.free:
            reasons.append("CLOUD_FREE_PLAN_NOT_PROVEN")
        if credit_snapshot.freshness != WebCreditSnapshotFreshness.current:
            reasons.append("CLOUD_CREDIT_SNAPSHOT_NOT_CURRENT")
        if credit_snapshot.expires_at <= now:
            reasons.append("CLOUD_CREDIT_SNAPSHOT_EXPIRED")
        if (
            not credit_snapshot.billing_period_start
            <= now
            < credit_snapshot.billing_period_end
        ):
            reasons.append("CLOUD_CREDIT_BILLING_PERIOD_INACTIVE")
        if credit_snapshot.max_concurrency is None:
            reasons.append("CLOUD_PLAN_CONCURRENCY_UNKNOWN")
        if (
            credit_snapshot.remaining_credits - request.safety_reserve_credits
            < FIRECRAWL_STANDARD_SCRAPE_CREDITS
        ):
            reasons.append("CLOUD_CREDIT_BUDGET_EXHAUSTED")
    return list(dict.fromkeys(reasons))


def _budget_decision(
    request: FirecrawlCloudMarkdownRequest,
    reservation: WebProviderCreditReservation | None,
    reasons: Sequence[str],
) -> CostDecision:
    allowed = bool(
        reservation is not None
        and reservation.status == WebCreditReservationStatus.reserved
        and not reasons
    )
    decision_id = stable_web_hybrid_ref(
        "firecrawl-cloud-cost-decision",
        {
            "request_ref": request.request_ref,
            "reservation_ref": reservation.reservation_ref if reservation else None,
            "allowed": allowed,
        },
    )
    return CostDecision(
        decision_id=decision_id,
        allowed=allowed,
        status=BudgetStatus.allowed if allowed else BudgetStatus.denied,
        reason_codes=["FREE_CREDIT_RESERVED"]
        if allowed
        else list(reasons) or ["FREE_CREDIT_NOT_RESERVED"],
        safe_message=(
            "One free-plan credit is reserved for the exact request."
            if allowed
            else "The exact request has no valid free-credit reservation."
        ),
    )


def _actual_usage(
    before: WebProviderCreditSnapshot | None,
    after: WebProviderCreditSnapshot | None,
    *,
    allowed_credits: set[int],
) -> tuple[str | None, int | None]:
    if (
        before is None
        or after is None
        or before.billing_period_ref != after.billing_period_ref
        or before.plan_kind != WebProviderPlanKind.free
        or after.plan_kind != WebProviderPlanKind.free
        or after.fetched_at <= before.fetched_at
    ):
        return None, None
    actual = before.remaining_credits - after.remaining_credits
    if actual not in allowed_credits:
        return None, None
    return (
        stable_web_hybrid_ref(
            "actual-usage-ref:firecrawl-cloud",
            {
                "before": before.snapshot_ref,
                "after": after.snapshot_ref,
                "actual": actual,
            },
        ),
        actual,
    )


def _cloud_result(
    *,
    request: FirecrawlCloudMarkdownRequest,
    invocation: CapabilityInvocationDecision,
    reservation: WebProviderCreditReservation | None,
    credit_before: WebProviderCreditSnapshot | None,
    credit_after: WebProviderCreditSnapshot | None,
    status: WebProviderTransportStatus,
    evidence: FirecrawlMarkdownEvidence | None,
    network_call_performed: bool,
    reason_codes: tuple[str, ...],
    blocker_codes: tuple[str, ...],
    gateway_audit_ref: str,
    created_at: datetime,
) -> FirecrawlCloudExecutionResult:
    effective_status = status
    if status == WebProviderTransportStatus.succeeded and (
        reservation is None or reservation.status != WebCreditReservationStatus.settled
    ):
        effective_status = WebProviderTransportStatus.failed
        evidence = None
    receipt = WebProviderTransportReceipt(
        receipt_ref=stable_web_hybrid_ref(
            "web-provider-transport-receipt-ref",
            {
                "request_ref": request.request_ref,
                "invocation_ref": invocation.decision_ref,
                "reservation_ref": reservation.reservation_ref if reservation else None,
                "status": effective_status.value,
            },
        ),
        request_ref=request.request_ref,
        provider_ref=FIRECRAWL_CLOUD_PROVIDER_REF,
        deployment=WebProviderDeploymentKind.firecrawl_cloud,
        operation=WebProviderOperation.scrape_markdown,
        target_source_ref=request.target_source_ref,
        configured_endpoint_ref=FIRECRAWL_CLOUD_ENDPOINT_REF,
        provider_transport_method=WebProviderTransportMethod.post,
        request_schema_ref=FIRECRAWL_CLOUD_SCRAPE_SCHEMA_REF,
        status=effective_status,
        response_receipt_hash_ref=(
            evidence.content_hash_ref if evidence is not None else None
        ),
        authority_decision_ref=(
            invocation.authority_decision_ref
            or "authority-decision-ref:firecrawl-cloud:not-allowed"
        ),
        approval_decision_ref=(
            invocation.approval_decision_ref
            or "approval-decision-ref:firecrawl-cloud:not-allowed"
        ),
        budget_decision_ref=(
            invocation.budget_decision_ref
            or "budget-decision-ref:firecrawl-cloud:not-allowed"
        ),
        reason_codes=reason_codes or tuple(blocker_codes),
        network_call_performed=network_call_performed,
        created_at=created_at,
    )
    return FirecrawlCloudExecutionResult(
        request_ref=request.request_ref,
        task_ref=request.task_ref,
        invocation_decision=invocation,
        transport_receipt=receipt,
        reservation=reservation,
        credit_snapshot_before_ref=(
            credit_before.snapshot_ref if credit_before else None
        ),
        credit_snapshot_after_ref=(credit_after.snapshot_ref if credit_after else None),
        gateway_audit_ref=gateway_audit_ref,
        status=effective_status,
        evidence=evidence,
        execution_succeeded=effective_status == WebProviderTransportStatus.succeeded,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
    )


def _exact_cloud_resource_refs(
    request: FirecrawlCloudMarkdownRequest,
    credit_snapshot: WebProviderCreditSnapshot | None,
) -> tuple[str, ...]:
    return (
        request.request_ref,
        request.task_ref,
        request.target_source_ref,
        request.idempotency_ref,
        request.routing_decision_ref,
        credit_snapshot.snapshot_ref
        if credit_snapshot
        else "web-credit-snapshot-ref:missing",
        credit_snapshot.billing_period_ref
        if credit_snapshot
        else "billing-period-ref:missing",
        FIRECRAWL_CLOUD_CAPABILITY_REF,
        FIRECRAWL_CLOUD_PROVIDER_REF,
        FIRECRAWL_CLOUD_ADAPTER_REF,
        WEB_HYBRID_COST_POLICY_REF,
    )


def _credit_failure(
    code: str,
    *,
    network_call_performed: bool,
    fetched_at: datetime,
) -> FirecrawlCloudCreditReconciliationResult:
    return FirecrawlCloudCreditReconciliationResult(
        status=WebProviderTransportStatus.failed,
        reconciliation_receipt_ref=stable_web_hybrid_ref(
            "web-credit-reconciliation-receipt-ref",
            {"status": "failed", "code": code, "fetched_at": fetched_at},
        ),
        reason_codes=(code,),
        network_call_performed=network_call_performed,
    )


def _strict_nonnegative_int(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_CREDIT_VALUE_INVALID",
            network_call_performed=True,
        )
    return value


def _provider_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_BILLING_PERIOD_INVALID",
            network_call_performed=True,
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FirecrawlCloudTransportError(
            "FIRECRAWL_CLOUD_BILLING_PERIOD_INVALID",
            network_call_performed=True,
        ) from exc
    return _aware(parsed)


def _aware(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("FIRECRAWL_CLOUD_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)


def _cloud_http_error_code(status: int) -> str:
    if 300 <= status <= 399:
        return "FIRECRAWL_CLOUD_PROVIDER_REDIRECT_DENIED"
    if status == 401:
        return "FIRECRAWL_CLOUD_AUTHENTICATION_FAILED"
    if status == 402:
        return "FIRECRAWL_CLOUD_PAID_OR_QUOTA_PATH_BLOCKED"
    if status == 429:
        return "FIRECRAWL_CLOUD_RATE_LIMITED"
    if status in {400, 403, 404, 409, 422}:
        return f"FIRECRAWL_CLOUD_PROVIDER_HTTP_{status}"
    if 500 <= status <= 599:
        return "FIRECRAWL_CLOUD_PROVIDER_5XX"
    return "FIRECRAWL_CLOUD_PROVIDER_NON_SUCCESS"


def _cloud_provider_error_code(
    status: int,
    raw: bytes,
    headers: Mapping[str, str],
) -> str:
    base = _cloud_http_error_code(status)
    if (
        headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "application/json"
    ):
        return base
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return base
    provider_code = payload.get("code") if isinstance(payload, Mapping) else None
    if isinstance(provider_code, str) and re.fullmatch(
        r"[A-Z][A-Z0-9_]{0,63}", provider_code
    ):
        return f"FIRECRAWL_CLOUD_PROVIDER_CODE_{provider_code}"
    provider_error = payload.get("error") if isinstance(payload, Mapping) else None
    if isinstance(provider_error, str):
        normalized = provider_error.lower()
        categories = (
            (("api key", "authentication"), "AUTHENTICATION_FAILED"),
            (("zero data", "zero-data"), "ZERO_DATA_RETENTION_UNAVAILABLE"),
            (("permission", "forbidden"), "PERMISSION_DENIED"),
            (("not allowed",), "REQUEST_NOT_ALLOWED"),
            (("blocked",), "TARGET_BLOCKED"),
        )
        for markers, category in categories:
            if any(marker in normalized for marker in markers):
                return f"FIRECRAWL_CLOUD_PROVIDER_{category}"
    return base


__all__ = [
    "FIRECRAWL_CLOUD_ACCOUNT_REF",
    "FIRECRAWL_CLOUD_ADAPTER_REF",
    "FIRECRAWL_CLOUD_CAPABILITY_REF",
    "FIRECRAWL_CLOUD_CREDENTIAL_REF",
    "FIRECRAWL_CLOUD_DEFAULT_SECRET_FILE",
    "FIRECRAWL_CLOUD_ENDPOINT_REF",
    "FIRECRAWL_CLOUD_LANE_REF",
    "FIRECRAWL_CLOUD_PROVIDER_REF",
    "FIRECRAWL_FREE_PLAN_CONCURRENCY",
    "FIRECRAWL_FREE_PLAN_CREDITS",
    "FIRECRAWL_STANDARD_SCRAPE_CREDITS",
    "CloudScrapeTransport",
    "CreditTransport",
    "FirecrawlCloudCredential",
    "FirecrawlCloudCreditReconciliationResult",
    "FirecrawlCloudExecutionResult",
    "FirecrawlCloudMarkdownRequest",
    "FirecrawlCloudTransportError",
    "build_firecrawl_cloud_capability_manifest",
    "build_firecrawl_cloud_credit_transport",
    "build_firecrawl_cloud_scrape_transport",
    "build_firecrawl_cloud_scrape_payload",
    "execute_firecrawl_cloud_markdown",
    "firecrawl_cloud_snapshot_from_state",
    "reconcile_firecrawl_cloud_credits",
    "resolve_firecrawl_cloud_credential",
]
