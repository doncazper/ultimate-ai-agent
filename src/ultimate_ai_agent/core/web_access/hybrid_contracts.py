"""Provider-neutral contracts for the bounded SearXNG/Firecrawl hybrid lane.

The contracts in this module are inert. They preserve provider, deployment,
health, capability, transport, routing, and free-credit truth without opening
a socket or granting standing authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capability_availability.contracts import (
    AuthorityPosture,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    CostPosture,
    DerivedRuntimeReadinessStatus,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
    derive_runtime_readiness,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


WEB_HYBRID_SCHEMA_VERSION = "uaa-web-hybrid.v1"
WEB_HYBRID_COST_POLICY_REF = "cost-policy-ref:firecrawl-standard-scrape:v1"
WEB_HYBRID_RECEIPT_REDACTIONS = (
    "raw_query_omitted",
    "raw_page_omitted",
    "raw_provider_payload_omitted",
    "credential_material_omitted",
    "local_path_omitted",
)


class WebProviderDeploymentKind(str, Enum):
    searxng_self_hosted = "searxng_self_hosted"
    firecrawl_self_hosted = "firecrawl_self_hosted"
    firecrawl_cloud = "firecrawl_cloud"


class WebProviderOperation(str, Enum):
    search = "search"
    scrape_markdown = "scrape_markdown"
    reconcile_credits = "reconcile_credits"


class WebProviderTransportMethod(str, Enum):
    get = "GET"
    post = "POST"


class WebProviderTransportStatus(str, Enum):
    blocked = "blocked"
    simulated = "simulated"
    succeeded = "succeeded"
    failed = "failed"


class WebProviderPlanKind(str, Enum):
    free = "free"
    paid = "paid"
    unknown = "unknown"


class WebCreditSnapshotFreshness(str, Enum):
    current = "current"
    stale = "stale"
    unknown = "unknown"


class WebCreditReservationStatus(str, Enum):
    reserved = "reserved"
    denied = "denied"
    settled = "settled"
    released = "released"
    incomplete = "incomplete"


class WebCreditReceiptCompleteness(str, Enum):
    complete = "complete"
    incomplete = "incomplete"
    unknown = "unknown"


class WebProviderRoutingPolicy(str, Enum):
    sealed = "sealed"
    self_host_only = "self_host_only"
    self_host_first_cloud_escalation = "self_host_first_cloud_escalation"


class WebProviderAttemptOutcome(str, Enum):
    not_attempted = "not_attempted"
    succeeded = "succeeded"
    timeout = "timeout"
    connection_failure = "connection_failure"
    provider_5xx = "provider_5xx"
    quota_blocked = "quota_blocked"
    circuit_open = "circuit_open"
    render_failure = "render_failure"
    empty_content = "empty_content"
    bot_challenge = "bot_challenge"
    policy_denied = "policy_denied"
    private_target_denied = "private_target_denied"
    robots_terms_denied = "robots_terms_denied"
    authority_denied = "authority_denied"
    target_4xx = "target_4xx"
    unsupported_content_type = "unsupported_content_type"
    scope_exhausted = "scope_exhausted"
    incomplete_credit_receipt = "incomplete_credit_receipt"
    unknown_failure = "unknown_failure"


class WebProviderCircuitState(str, Enum):
    closed = "closed"
    open = "open"
    unknown = "unknown"


class _WebHybridModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    @model_validator(mode="after")
    def reject_unsafe_material(self) -> "_WebHybridModel":
        payload = self.model_dump(mode="json")
        if contains_secret_like(payload) or contains_obvious_secret(payload):
            raise ValueError("WEB_HYBRID_SECRET_LIKE_VALUE_REJECTED")
        if _contains_private_material(payload):
            raise ValueError("WEB_HYBRID_PRIVATE_MATERIAL_REJECTED")
        return self

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class WebProviderCapabilityState(_WebHybridModel):
    schema_version: Literal["uaa-web-hybrid.v1"] = WEB_HYBRID_SCHEMA_VERSION
    state_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    deployment: WebProviderDeploymentKind
    operation: WebProviderOperation
    version_ref: str = Field(..., min_length=1)
    catalog_status: CatalogStatus
    compatibility_status: CompatibilityStatus
    configuration_status: ConfigurationStatus
    health_status: HealthStatus
    authority_posture: AuthorityPosture
    resource_status: ResourceBudgetStatus
    safe_disable_status: SafeDisableStatus
    freshness_status: FreshnessStatus
    runtime_readiness: DerivedRuntimeReadinessStatus
    observed_at: datetime
    expires_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = ()
    provider_catalog_visible: Literal[True] = True
    request_scoped_evaluation_required: Literal[True] = True
    standing_authority_granted: Literal[False] = False
    network_call_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_state(self) -> "WebProviderCapabilityState":
        _validate_refs(
            (self.state_ref, self.provider_ref, self.version_ref),
            "web_provider_capability_ref",
        )
        for code in (*self.reason_codes, *self.blocker_codes):
            _validate_code(code)
        derived = derive_runtime_readiness(
            catalog_status=self.catalog_status,
            compatibility_status=self.compatibility_status,
            configuration_status=self.configuration_status,
            health_status=self.health_status,
            resource_status=self.resource_status,
            cost_posture=(
                CostPosture.metered
                if self.deployment == WebProviderDeploymentKind.firecrawl_cloud
                else CostPosture.not_metered
            ),
            safe_disable_status=self.safe_disable_status,
            freshness_status=self.freshness_status,
            checked_at=self.observed_at,
            expires_at=self.expires_at,
        )
        if derived.status != self.runtime_readiness:
            raise ValueError("WEB_PROVIDER_RUNTIME_READINESS_DERIVATION_MISMATCH")
        return self


class WebProviderTransportReceipt(_WebHybridModel):
    schema_version: Literal["uaa-web-hybrid.v1"] = WEB_HYBRID_SCHEMA_VERSION
    receipt_ref: str = Field(..., min_length=1)
    request_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    deployment: WebProviderDeploymentKind
    operation: WebProviderOperation
    target_source_ref: str | None = None
    configured_endpoint_ref: str = Field(..., min_length=1)
    target_method: Literal["GET"] = "GET"
    provider_transport_method: WebProviderTransportMethod
    request_schema_ref: str = Field(..., min_length=1)
    status: WebProviderTransportStatus
    response_receipt_hash_ref: str | None = None
    authority_decision_ref: str = Field(..., min_length=1)
    approval_decision_ref: str = Field(..., min_length=1)
    budget_decision_ref: str = Field(..., min_length=1)
    reason_codes: tuple[str, ...] = ()
    content_untrusted: Literal[True] = True
    raw_query_stored: Literal[False] = False
    raw_page_stored: Literal[False] = False
    raw_provider_payload_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False
    local_path_stored: Literal[False] = False
    network_call_performed: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_receipt(self) -> "WebProviderTransportReceipt":
        refs = [
            self.receipt_ref,
            self.request_ref,
            self.provider_ref,
            self.configured_endpoint_ref,
            self.request_schema_ref,
            self.authority_decision_ref,
            self.approval_decision_ref,
            self.budget_decision_ref,
        ]
        if self.target_source_ref:
            refs.append(self.target_source_ref)
        if self.response_receipt_hash_ref:
            refs.append(self.response_receipt_hash_ref)
        _validate_refs(refs, "web_provider_transport_ref")
        for code in self.reason_codes:
            _validate_code(code)
        if (
            self.status
            in {
                WebProviderTransportStatus.blocked,
                WebProviderTransportStatus.simulated,
            }
            and self.network_call_performed
        ):
            raise ValueError("WEB_PROVIDER_BLOCKED_OR_SIMULATED_CALL_DENIED")
        return self


class WebProviderCreditSnapshot(_WebHybridModel):
    schema_version: Literal["uaa-web-hybrid.v1"] = WEB_HYBRID_SCHEMA_VERSION
    snapshot_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    deployment: Literal[WebProviderDeploymentKind.firecrawl_cloud] = (
        WebProviderDeploymentKind.firecrawl_cloud
    )
    account_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    plan_kind: WebProviderPlanKind
    plan_credits: int = Field(..., ge=0)
    remaining_credits: int = Field(..., ge=0)
    max_concurrency: int | None = Field(default=None, ge=1, le=16)
    billing_period_ref: str = Field(..., min_length=1)
    billing_period_start: datetime
    billing_period_end: datetime
    fetched_at: datetime
    expires_at: datetime
    freshness: WebCreditSnapshotFreshness
    response_receipt_hash_ref: str = Field(..., min_length=1)
    raw_provider_payload_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False

    @model_validator(mode="after")
    def validate_snapshot(self) -> "WebProviderCreditSnapshot":
        _validate_refs(
            (
                self.snapshot_ref,
                self.provider_ref,
                self.account_ref,
                self.credential_ref,
                self.billing_period_ref,
                self.response_receipt_hash_ref,
            ),
            "web_credit_snapshot_ref",
        )
        if not self.billing_period_start < self.billing_period_end:
            raise ValueError("WEB_CREDIT_BILLING_PERIOD_INVALID")
        if not self.fetched_at < self.expires_at:
            raise ValueError("WEB_CREDIT_SNAPSHOT_EXPIRY_INVALID")
        return self


class WebProviderCreditReservationRequest(_WebHybridModel):
    request_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    deployment: Literal[WebProviderDeploymentKind.firecrawl_cloud] = (
        WebProviderDeploymentKind.firecrawl_cloud
    )
    operation: Literal[WebProviderOperation.scrape_markdown] = (
        WebProviderOperation.scrape_markdown
    )
    snapshot_ref: str = Field(..., min_length=1)
    billing_period_ref: str = Field(..., min_length=1)
    routing_decision_ref: str = Field(..., min_length=1)
    cost_policy_ref: str = WEB_HYBRID_COST_POLICY_REF
    estimated_credits: int = Field(..., ge=1, le=10)
    safety_reserve_credits: int = Field(default=1, ge=0, le=100)
    run_credit_ceiling: int = Field(default=10, ge=1, le=100)
    attempt_number: int = Field(default=1, ge=1, le=2)
    fallback_parent_ref: str | None = None

    @model_validator(mode="after")
    def validate_request(self) -> "WebProviderCreditReservationRequest":
        refs = [
            self.request_ref,
            self.idempotency_ref,
            self.provider_ref,
            self.snapshot_ref,
            self.billing_period_ref,
            self.routing_decision_ref,
            self.cost_policy_ref,
        ]
        if self.fallback_parent_ref:
            refs.append(self.fallback_parent_ref)
        _validate_refs(refs, "web_credit_reservation_request_ref")
        if self.estimated_credits > self.run_credit_ceiling:
            raise ValueError("WEB_CREDIT_ESTIMATE_EXCEEDS_RUN_CEILING")
        return self


class WebProviderCreditReservation(_WebHybridModel):
    reservation_ref: str = Field(..., min_length=1)
    request_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    request_fingerprint_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    deployment: Literal[WebProviderDeploymentKind.firecrawl_cloud] = (
        WebProviderDeploymentKind.firecrawl_cloud
    )
    operation: Literal[WebProviderOperation.scrape_markdown] = (
        WebProviderOperation.scrape_markdown
    )
    snapshot_ref: str = Field(..., min_length=1)
    billing_period_ref: str = Field(..., min_length=1)
    routing_decision_ref: str = Field(..., min_length=1)
    cost_policy_ref: str = WEB_HYBRID_COST_POLICY_REF
    estimated_credits: int = Field(..., ge=1, le=10)
    reserved_credits: int = Field(..., ge=0, le=10)
    status: WebCreditReservationStatus
    receipt_completeness: WebCreditReceiptCompleteness
    attempt_number: int = Field(..., ge=1, le=2)
    fallback_parent_ref: str | None = None
    actual_usage_ref: str | None = None
    reason_codes: tuple[str, ...] = ()
    in_flight: bool = False
    safe_disabled: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_reservation(self) -> "WebProviderCreditReservation":
        refs = [
            self.reservation_ref,
            self.request_ref,
            self.idempotency_ref,
            self.request_fingerprint_ref,
            self.provider_ref,
            self.snapshot_ref,
            self.billing_period_ref,
            self.routing_decision_ref,
            self.cost_policy_ref,
        ]
        if self.fallback_parent_ref:
            refs.append(self.fallback_parent_ref)
        if self.actual_usage_ref:
            refs.append(self.actual_usage_ref)
        _validate_refs(refs, "web_credit_reservation_ref")
        for code in self.reason_codes:
            _validate_code(code)
        if self.status == WebCreditReservationStatus.reserved:
            if not self.in_flight or self.reserved_credits != self.estimated_credits:
                raise ValueError("WEB_CREDIT_RESERVED_STATE_INVALID")
        if self.status == WebCreditReservationStatus.denied and (
            self.in_flight or self.reserved_credits != 0
        ):
            raise ValueError("WEB_CREDIT_DENIED_STATE_INVALID")
        return self


class WebProviderRoutingDecision(_WebHybridModel):
    decision_ref: str = Field(..., min_length=1)
    request_ref: str = Field(..., min_length=1)
    policy: WebProviderRoutingPolicy
    operation: WebProviderOperation
    selected_deployment: WebProviderDeploymentKind | None = None
    fallback_deployment: WebProviderDeploymentKind | None = None
    attempt_count_ceiling: int = Field(default=1, ge=0, le=2)
    reason_codes: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = ()
    simulation_only: Literal[True] = True
    request_scoped_authority_required: Literal[True] = True
    execution_authorized: Literal[False] = False
    network_call_performed: Literal[False] = False
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_decision(self) -> "WebProviderRoutingDecision":
        _validate_refs((self.decision_ref, self.request_ref), "web_routing_ref")
        for code in (*self.reason_codes, *self.blocker_codes):
            _validate_code(code)
        if self.selected_deployment is None and self.attempt_count_ceiling != 0:
            raise ValueError("WEB_ROUTING_BLOCKED_ATTEMPT_CEILING_MUST_BE_ZERO")
        if self.fallback_deployment is not None and self.attempt_count_ceiling != 2:
            raise ValueError("WEB_ROUTING_FALLBACK_REQUIRES_TWO_ATTEMPT_CEILING")
        return self


def build_web_provider_capability_state(
    *,
    state_ref: str,
    provider_ref: str,
    deployment: WebProviderDeploymentKind,
    operation: WebProviderOperation,
    version_ref: str,
    catalog_status: CatalogStatus,
    compatibility_status: CompatibilityStatus,
    configuration_status: ConfigurationStatus,
    health_status: HealthStatus,
    authority_posture: AuthorityPosture,
    resource_status: ResourceBudgetStatus,
    safe_disable_status: SafeDisableStatus,
    freshness_status: FreshnessStatus,
    observed_at: datetime,
    expires_at: datetime | None,
    reason_codes: tuple[str, ...] = (),
    blocker_codes: tuple[str, ...] = (),
) -> WebProviderCapabilityState:
    derived = derive_runtime_readiness(
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status,
        resource_status=resource_status,
        cost_posture=(
            CostPosture.metered
            if deployment == WebProviderDeploymentKind.firecrawl_cloud
            else CostPosture.not_metered
        ),
        safe_disable_status=safe_disable_status,
        freshness_status=freshness_status,
        checked_at=observed_at,
        expires_at=expires_at,
    )
    return WebProviderCapabilityState(
        state_ref=state_ref,
        provider_ref=provider_ref,
        deployment=deployment,
        operation=operation,
        version_ref=version_ref,
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status,
        authority_posture=authority_posture,
        resource_status=resource_status,
        safe_disable_status=safe_disable_status,
        freshness_status=freshness_status,
        runtime_readiness=derived.status,
        observed_at=observed_at,
        expires_at=expires_at,
        reason_codes=reason_codes,
        blocker_codes=tuple(dict.fromkeys((*blocker_codes, *derived.blocker_codes))),
    )


def stable_web_hybrid_ref(prefix: str, value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_refs(values: Any, field_name: str) -> None:
    for value in values:
        validate_task_ref(str(value), field_name)


def _validate_code(value: str) -> None:
    validate_safe_task_text(value, "web_hybrid_reason_code")
    if value.upper() != value or not value.replace("_", "").isalnum():
        raise ValueError("WEB_HYBRID_REASON_CODE_INVALID")


def _contains_private_material(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.lower()
        return any(
            marker in normalized
            for marker in (
                "/users/",
                "/home/",
                "c:\\users\\",
                "authorization: bearer",
                "raw provider payload",
                "raw page content",
                "raw query:",
                "hostname:",
                "username:",
            )
        )
    if isinstance(value, dict):
        return any(_contains_private_material(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_private_material(item) for item in value)
    return False
