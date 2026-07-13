from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionOutcome,
    AuthorityPolicyDecision,
)
from ultimate_ai_agent.core.capabilities.enums import PolicyDecisionStatus
from ultimate_ai_agent.core.capabilities.models import PolicyDecision
from ultimate_ai_agent.core.costs import BudgetStatus, CostDecision
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


CAPABILITY_AVAILABILITY_SCHEMA_VERSION = "uaa-capability-availability.v1"
CAPABILITY_AVAILABILITY_READ_MODEL_SCHEMA_VERSION = (
    "uaa-capability-availability-read-model.v1"
)
CAPABILITY_INVOCATION_DECISION_SCHEMA_VERSION = (
    "uaa-capability-invocation-decision.v1"
)
CAPABILITY_AVAILABILITY_ROUTE_REF = (
    "GET /control-center/capabilities/availability"
)
CAPABILITY_AVAILABILITY_CLI_REF = (
    "repo-local-command:uaa-runtime-capability-availability"
)
CAPABILITY_INVOCATION_DECISION_CONTRACT_REF = (
    "contract-ref:capability-invocation-decision:v1"
)
EXECUTION_RECEIPT_CONTRACT_REF = "contract-ref:lane-specific-execution-receipt"


_SAFE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_RAW_ENV_ASSIGNMENT_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=")
_RAW_USERNAME_RE = re.compile(r"(?<![A-Za-z0-9])@[A-Za-z0-9_.-]{2,}")
_HOSTNAME_RE = re.compile(
    r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|io|dev|app|local|internal)\b"
)


class CatalogStatus(str, Enum):
    supported = "supported"
    unsupported = "unsupported"
    unknown = "unknown"


class CompatibilityStatus(str, Enum):
    supported = "supported"
    unsupported = "unsupported"
    unknown = "unknown"


class ConfigurationStatus(str, Enum):
    configured = "configured"
    not_configured = "not_configured"
    invalid = "invalid"
    unknown = "unknown"


class HealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"
    stale = "stale"
    unknown = "unknown"


class AuthorityPosture(str, Enum):
    eligible_for_policy_evaluation = "eligible_for_policy_evaluation"
    approval_required = "approval_required"
    lease_required = "lease_required"
    blocked = "blocked"


class ResourceBudgetStatus(str, Enum):
    available = "available"
    constrained = "constrained"
    exhausted = "exhausted"
    unknown = "unknown"


class CostPosture(str, Enum):
    not_metered = "not_metered"
    metered = "metered"
    unknown = "unknown"


class SafeDisableStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    unknown = "unknown"


class FreshnessStatus(str, Enum):
    current = "current"
    stale = "stale"
    unknown = "unknown"


class DerivedRuntimeReadinessStatus(str, Enum):
    ready = "ready"
    unavailable = "unavailable"
    blocked = "blocked"
    unknown = "unknown"


class InvocationDecisionOutcome(str, Enum):
    allow = "allow"
    approval_required = "approval_required"
    lease_required = "lease_required"
    blocked = "blocked"


class IdempotencyPosture(str, Enum):
    validated = "validated"
    not_required = "not_required"
    missing = "missing"
    invalid = "invalid"


class InvocationDecisionCachePosture(str, Enum):
    not_cacheable = "not_cacheable"


class _CapabilityAvailabilityModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    @model_validator(mode="after")
    def reject_unsafe_payload(self) -> "_CapabilityAvailabilityModel":
        payload = self.model_dump(mode="json")
        if contains_secret_like(payload) or contains_obvious_secret(payload):
            raise ValueError("CAPABILITY_AVAILABILITY_SECRET_LIKE_VALUE_REJECTED")
        return self


class RuntimeReadinessDerivation(_CapabilityAvailabilityModel):
    status: DerivedRuntimeReadinessStatus
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_codes(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)


def derive_runtime_readiness(
    *,
    catalog_status: CatalogStatus,
    compatibility_status: CompatibilityStatus,
    configuration_status: ConfigurationStatus,
    health_status: HealthStatus,
    resource_status: ResourceBudgetStatus,
    cost_posture: CostPosture,
    safe_disable_status: SafeDisableStatus,
    freshness_status: FreshnessStatus,
    checked_at: datetime,
    expires_at: datetime | None = None,
) -> RuntimeReadinessDerivation:
    """Derive environment readiness only; this function never grants authority."""

    checked_at = _aware_datetime(checked_at, "checked_at")
    if expires_at is not None:
        expires_at = _aware_datetime(expires_at, "expires_at")

    if safe_disable_status == SafeDisableStatus.active:
        return _derivation(
            DerivedRuntimeReadinessStatus.blocked,
            "SAFE_DISABLE_OVERRIDE_APPLIED",
            "SAFE_DISABLE_ACTIVE",
        )
    if safe_disable_status == SafeDisableStatus.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "SAFE_DISABLE_POSTURE_UNCONFIRMED",
            "SAFE_DISABLE_STATUS_UNKNOWN",
        )
    if freshness_status == FreshnessStatus.stale or (
        expires_at is not None and expires_at <= checked_at
    ):
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "OBSERVATION_EXPIRED_OR_STALE",
            "OBSERVATION_STALE",
        )
    if freshness_status == FreshnessStatus.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "OBSERVATION_FRESHNESS_UNCONFIRMED",
            "FRESHNESS_STATUS_UNKNOWN",
        )
    if catalog_status == CatalogStatus.unsupported:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "CAPABILITY_NOT_SUPPORTED_BY_CATALOG",
            "CATALOG_UNSUPPORTED",
        )
    if catalog_status == CatalogStatus.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "CAPABILITY_CATALOG_STATUS_UNCONFIRMED",
            "CATALOG_STATUS_UNKNOWN",
        )
    if compatibility_status == CompatibilityStatus.unsupported:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "DECLARED_VERSION_NOT_SUPPORTED",
            "COMPATIBILITY_UNSUPPORTED",
        )
    if compatibility_status == CompatibilityStatus.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "COMPATIBILITY_NOT_PROVEN",
            "COMPATIBILITY_STATUS_UNKNOWN",
        )
    if configuration_status == ConfigurationStatus.not_configured:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "RUNTIME_CONFIGURATION_MISSING",
            "NOT_CONFIGURED",
        )
    if configuration_status == ConfigurationStatus.invalid:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "RUNTIME_CONFIGURATION_INVALID",
            "CONFIGURATION_INVALID",
        )
    if configuration_status == ConfigurationStatus.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "RUNTIME_CONFIGURATION_UNCONFIRMED",
            "CONFIGURATION_STATUS_UNKNOWN",
        )
    if health_status == HealthStatus.stale:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "HEALTH_OBSERVATION_STALE",
            "HEALTH_STALE",
        )
    if health_status == HealthStatus.unhealthy:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "RUNTIME_HEALTH_CHECK_FAILED",
            "HEALTH_UNHEALTHY",
        )
    if health_status == HealthStatus.degraded:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "DEGRADED_USE_REQUIRES_EXACT_POLICY",
            "HEALTH_DEGRADED_NOT_PERMITTED",
        )
    if health_status == HealthStatus.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "RUNTIME_HEALTH_UNCONFIRMED",
            "HEALTH_STATUS_UNKNOWN",
        )
    if cost_posture == CostPosture.unknown:
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "COST_POSTURE_UNCONFIRMED",
            "COST_POSTURE_UNKNOWN",
        )
    if resource_status == ResourceBudgetStatus.exhausted:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "RESOURCE_OR_BUDGET_EXHAUSTED",
            "RESOURCE_BUDGET_EXHAUSTED",
        )
    if resource_status == ResourceBudgetStatus.constrained:
        return _derivation(
            DerivedRuntimeReadinessStatus.unavailable,
            "CONSTRAINED_USE_REQUIRES_EXACT_POLICY",
            "RESOURCE_BUDGET_CONSTRAINED",
        )
    if resource_status == ResourceBudgetStatus.unknown:
        blocker = (
            "METERED_BUDGET_STATUS_UNKNOWN"
            if cost_posture == CostPosture.metered
            else "RESOURCE_BUDGET_STATUS_UNKNOWN"
        )
        return _derivation(
            DerivedRuntimeReadinessStatus.unknown,
            "RESOURCE_OR_BUDGET_AVAILABILITY_UNCONFIRMED",
            blocker,
        )
    return _derivation(
        DerivedRuntimeReadinessStatus.ready,
        "ENVIRONMENT_READY_FOR_REQUEST_SCOPED_EVALUATION",
        None,
    )


class CapabilityAvailabilitySnapshot(_CapabilityAvailabilityModel):
    schema_version: Literal["uaa-capability-availability.v1"] = (
        CAPABILITY_AVAILABILITY_SCHEMA_VERSION
    )
    snapshot_ref: str
    capability_ref: str
    provider_ref: str | None = None
    adapter_ref: str | None = None
    catalog_status: CatalogStatus
    compatibility_status: CompatibilityStatus
    configuration_status: ConfigurationStatus
    health_status: HealthStatus
    authority_posture: AuthorityPosture
    resource_status: ResourceBudgetStatus
    cost_posture: CostPosture
    safe_disable_status: SafeDisableStatus
    runtime_readiness_status: DerivedRuntimeReadinessStatus
    declared_or_observed_version_ref: str | None = None
    checked_at: datetime
    expires_at: datetime | None = None
    freshness_status: FreshnessStatus
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    probe_refs: list[str] = Field(default_factory=list)
    source_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=500)

    @field_validator(
        "snapshot_ref",
        "capability_ref",
        "provider_ref",
        "adapter_ref",
        "declared_or_observed_version_ref",
        "source_ref",
    )
    @classmethod
    def validate_optional_refs(cls, value: str | None) -> str | None:
        if value is not None:
            validate_execution_ref(value, "capability_availability_ref")
        return value

    @field_validator("evidence_refs", "probe_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            validate_execution_ref(value, "capability_availability_ref")
        return list(dict.fromkeys(values))

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_snapshot_codes(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value

    @field_validator("checked_at", "expires_at")
    @classmethod
    def validate_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return _aware_datetime(value, "capability_availability_timestamp")
        return value

    @model_validator(mode="after")
    def validate_derived_readiness(self) -> "CapabilityAvailabilitySnapshot":
        derived = derive_runtime_readiness(
            catalog_status=self.catalog_status,
            compatibility_status=self.compatibility_status,
            configuration_status=self.configuration_status,
            health_status=self.health_status,
            resource_status=self.resource_status,
            cost_posture=self.cost_posture,
            safe_disable_status=self.safe_disable_status,
            freshness_status=self.freshness_status,
            checked_at=self.checked_at,
            expires_at=self.expires_at,
        )
        if self.runtime_readiness_status != derived.status:
            raise ValueError("CAPABILITY_AVAILABILITY_DERIVED_STATUS_MISMATCH")
        if not set(derived.reason_codes).issubset(set(self.reason_codes)):
            raise ValueError("CAPABILITY_AVAILABILITY_DERIVED_REASON_REQUIRED")
        if not set(derived.blocker_codes).issubset(set(self.blocker_codes)):
            raise ValueError("CAPABILITY_AVAILABILITY_DERIVED_BLOCKER_REQUIRED")
        return self


def build_capability_availability_snapshot(
    *,
    snapshot_ref: str,
    capability_ref: str,
    catalog_status: CatalogStatus,
    compatibility_status: CompatibilityStatus,
    configuration_status: ConfigurationStatus,
    health_status: HealthStatus,
    authority_posture: AuthorityPosture,
    resource_status: ResourceBudgetStatus,
    cost_posture: CostPosture,
    safe_disable_status: SafeDisableStatus,
    checked_at: datetime,
    freshness_status: FreshnessStatus,
    source_ref: str,
    safe_summary: str,
    provider_ref: str | None = None,
    adapter_ref: str | None = None,
    declared_or_observed_version_ref: str | None = None,
    expires_at: datetime | None = None,
    reason_codes: list[str] | None = None,
    blocker_codes: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    probe_refs: list[str] | None = None,
) -> CapabilityAvailabilitySnapshot:
    derivation = derive_runtime_readiness(
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status,
        resource_status=resource_status,
        cost_posture=cost_posture,
        safe_disable_status=safe_disable_status,
        freshness_status=freshness_status,
        checked_at=checked_at,
        expires_at=expires_at,
    )
    return CapabilityAvailabilitySnapshot(
        snapshot_ref=snapshot_ref,
        capability_ref=capability_ref,
        provider_ref=provider_ref,
        adapter_ref=adapter_ref,
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status,
        authority_posture=authority_posture,
        resource_status=resource_status,
        cost_posture=cost_posture,
        safe_disable_status=safe_disable_status,
        runtime_readiness_status=derivation.status,
        declared_or_observed_version_ref=declared_or_observed_version_ref,
        checked_at=checked_at,
        expires_at=expires_at,
        freshness_status=freshness_status,
        reason_codes=_dedupe([*(reason_codes or []), *derivation.reason_codes]),
        blocker_codes=_dedupe([*(blocker_codes or []), *derivation.blocker_codes]),
        evidence_refs=evidence_refs or [],
        probe_refs=probe_refs or [],
        source_ref=source_ref,
        safe_summary=safe_summary,
    )


class CapabilityInvocationRequest(_CapabilityAvailabilityModel):
    request_ref: str
    snapshot_ref: str
    capability_ref: str
    provider_ref: str | None = None
    adapter_ref: str | None = None
    task_ref: str | None = None
    approval_ref: str | None = None
    budget_decision_ref: str | None = None
    authority_lease_required: bool = False
    local_approval_required: bool = False
    idempotency_posture: IdempotencyPosture
    expected_execution_receipt_ref: str

    @field_validator(
        "request_ref",
        "snapshot_ref",
        "capability_ref",
        "provider_ref",
        "adapter_ref",
        "task_ref",
        "approval_ref",
        "budget_decision_ref",
        "expected_execution_receipt_ref",
    )
    @classmethod
    def validate_request_refs(cls, value: str | None) -> str | None:
        if value is not None:
            validate_execution_ref(value, "capability_invocation_ref")
        return value


class CapabilityInvocationDecision(_CapabilityAvailabilityModel):
    schema_version: Literal["uaa-capability-invocation-decision.v1"] = (
        CAPABILITY_INVOCATION_DECISION_SCHEMA_VERSION
    )
    decision_ref: str
    request_ref: str
    snapshot_ref: str
    capability_ref: str
    provider_ref: str | None = None
    adapter_ref: str | None = None
    outcome: InvocationDecisionOutcome
    policy_decision_ref: str
    authority_decision_ref: str | None = None
    approval_decision_ref: str | None = None
    budget_decision_ref: str | None = None
    expected_execution_receipt_ref: str
    authority_lease_required: bool = False
    local_approval_required: bool = False
    cache_posture: Literal["not_cacheable"] = (
        InvocationDecisionCachePosture.not_cacheable.value
    )
    evaluated_at: datetime
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)

    @field_validator(
        "decision_ref",
        "request_ref",
        "snapshot_ref",
        "capability_ref",
        "provider_ref",
        "adapter_ref",
        "policy_decision_ref",
        "authority_decision_ref",
        "approval_decision_ref",
        "budget_decision_ref",
        "expected_execution_receipt_ref",
    )
    @classmethod
    def validate_decision_refs(cls, value: str | None) -> str | None:
        if value is not None:
            validate_execution_ref(value, "capability_invocation_decision_ref")
        return value

    @field_validator("evaluated_at")
    @classmethod
    def validate_evaluated_at(cls, value: datetime) -> datetime:
        return _aware_datetime(value, "evaluated_at")

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_decision_codes(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)

    @field_validator("safe_summary")
    @classmethod
    def validate_decision_summary(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value

    @model_validator(mode="after")
    def validate_allow_posture(self) -> "CapabilityInvocationDecision":
        if self.outcome == InvocationDecisionOutcome.allow and self.blocker_codes:
            raise ValueError("CAPABILITY_INVOCATION_ALLOW_WITH_BLOCKERS_DENIED")
        if (
            self.outcome == InvocationDecisionOutcome.allow
            and self.authority_lease_required
            and self.authority_decision_ref is None
        ):
            raise ValueError("CAPABILITY_INVOCATION_ALLOW_REQUIRES_AUTHORITY_DECISION")
        if (
            self.outcome == InvocationDecisionOutcome.allow
            and self.local_approval_required
            and self.approval_decision_ref is None
        ):
            raise ValueError("CAPABILITY_INVOCATION_ALLOW_REQUIRES_APPROVAL_DECISION")
        return self


def evaluate_capability_invocation(
    *,
    request: CapabilityInvocationRequest,
    snapshot: CapabilityAvailabilitySnapshot,
    policy_decision: PolicyDecision,
    authority_decision: AuthorityPolicyDecision | None = None,
    local_approval_decision: PolicyDecision | None = None,
    budget_decision: CostDecision | None = None,
    evaluated_at: datetime | None = None,
) -> CapabilityInvocationDecision:
    """Evaluate one exact request immediately before a future execution attempt."""

    evaluated_at = _aware_datetime(evaluated_at or utc_now(), "evaluated_at")
    blockers: list[str] = []
    reasons: list[str] = ["REQUEST_SCOPED_EVALUATION_PERFORMED"]
    requested_outcome: InvocationDecisionOutcome | None = None

    if request.snapshot_ref != snapshot.snapshot_ref:
        blockers.append("SNAPSHOT_REF_MISMATCH")
    if request.capability_ref != snapshot.capability_ref:
        blockers.append("CAPABILITY_REF_MISMATCH")
    if request.provider_ref != snapshot.provider_ref:
        blockers.append("PROVIDER_REF_MISMATCH")
    if request.adapter_ref != snapshot.adapter_ref:
        blockers.append("ADAPTER_REF_MISMATCH")
    if snapshot.safe_disable_status != SafeDisableStatus.inactive:
        blockers.append("SAFE_DISABLE_NOT_INACTIVE")
    if snapshot.runtime_readiness_status != DerivedRuntimeReadinessStatus.ready:
        blockers.append("RUNTIME_READINESS_NOT_READY")
    if snapshot.authority_posture == AuthorityPosture.blocked:
        blockers.append("AVAILABILITY_AUTHORITY_POSTURE_BLOCKED")

    if policy_decision.capability_id != request.capability_ref:
        blockers.append("POLICY_CAPABILITY_SCOPE_MISMATCH")
    if request.task_ref is not None and policy_decision.task_id != request.task_ref:
        blockers.append("POLICY_TASK_SCOPE_MISMATCH")
    if policy_decision.status == PolicyDecisionStatus.approval_required:
        requested_outcome = InvocationDecisionOutcome.approval_required
        reasons.append("POLICY_REQUIRES_APPROVAL")
    elif policy_decision.status != PolicyDecisionStatus.allowed or not policy_decision.allowed:
        blockers.append("POLICY_ENGINE_DENIED")

    approval_required = (
        snapshot.authority_posture == AuthorityPosture.approval_required
        or policy_decision.requires_approval
        or policy_decision.status == PolicyDecisionStatus.approval_required
        or request.local_approval_required
    )
    if approval_required:
        if not request.approval_ref:
            requested_outcome = InvocationDecisionOutcome.approval_required
            reasons.append("APPROVAL_REF_REQUIRED")
        if not _exact_local_approval_valid(
            local_approval_decision,
            capability_ref=request.capability_ref,
            task_ref=request.task_ref,
        ):
            requested_outcome = InvocationDecisionOutcome.approval_required
            reasons.append("EXACT_LOCAL_APPROVAL_VALIDATION_REQUIRED")

    if (
        snapshot.authority_posture == AuthorityPosture.lease_required
        or request.authority_lease_required
    ):
        if not _exact_authority_lease_valid(
            authority_decision,
            capability_ref=request.capability_ref,
        ):
            requested_outcome = InvocationDecisionOutcome.lease_required
            reasons.append("EXACT_AUTHORITY_LEASE_SCOPE_REQUIRED")

    budget_required = snapshot.cost_posture in {
        CostPosture.metered,
        CostPosture.unknown,
    }
    if budget_required and request.budget_decision_ref is None:
        blockers.append("REQUEST_BUDGET_DECISION_REF_REQUIRED")
    if budget_required and budget_decision is None:
        blockers.append("REQUEST_BUDGET_DECISION_REQUIRED")
    if request.budget_decision_ref is not None and budget_decision is None:
        blockers.append("REQUEST_BUDGET_DECISION_REQUIRED")
    if budget_decision is not None:
        observed_budget_ref = f"budget-decision-ref:{budget_decision.decision_id}"
        if request.budget_decision_ref != observed_budget_ref:
            blockers.append("REQUEST_BUDGET_DECISION_REF_MISMATCH")
        if (
            budget_decision.status != BudgetStatus.allowed.value
            or not budget_decision.allowed
        ):
            blockers.append("REQUEST_BUDGET_DECISION_BLOCKED")

    if request.idempotency_posture not in {
        IdempotencyPosture.validated,
        IdempotencyPosture.not_required,
    }:
        blockers.append("IDEMPOTENCY_POSTURE_INVALID")

    blockers = _dedupe(blockers)
    reasons = _dedupe(reasons)
    if blockers:
        outcome = InvocationDecisionOutcome.blocked
        safe_summary = (
            "Exact request evaluation blocked execution; availability did not grant authority."
        )
    elif requested_outcome is not None:
        outcome = requested_outcome
        safe_summary = (
            "Exact request evaluation requires an additional scoped authority decision before execution."
        )
    else:
        outcome = InvocationDecisionOutcome.allow
        reasons.append("REQUEST_SCOPED_INVOCATION_ALLOWED")
        safe_summary = (
            "Exact request gates passed for one immediate execution attempt; a separate execution receipt is required."
        )

    decision_ref = _stable_decision_ref(
        request=request,
        snapshot=snapshot,
        policy_decision=policy_decision,
        authority_decision=authority_decision,
        local_approval_decision=local_approval_decision,
        budget_decision=budget_decision,
        outcome=outcome,
        blocker_codes=blockers,
    )
    return CapabilityInvocationDecision(
        decision_ref=decision_ref,
        request_ref=request.request_ref,
        snapshot_ref=snapshot.snapshot_ref,
        capability_ref=request.capability_ref,
        provider_ref=request.provider_ref,
        adapter_ref=request.adapter_ref,
        outcome=outcome,
        policy_decision_ref=_policy_decision_ref(policy_decision),
        authority_decision_ref=(
            authority_decision.decision_ref if authority_decision else None
        ),
        approval_decision_ref=(
            _policy_decision_ref(local_approval_decision)
            if local_approval_decision
            else None
        ),
        budget_decision_ref=(
            f"budget-decision-ref:{budget_decision.decision_id}"
            if budget_decision
            else None
        ),
        expected_execution_receipt_ref=request.expected_execution_receipt_ref,
        authority_lease_required=request.authority_lease_required,
        local_approval_required=request.local_approval_required,
        evaluated_at=evaluated_at,
        reason_codes=reasons,
        blocker_codes=blockers,
        safe_summary=safe_summary,
    )


class WebHybridCapabilityLanePosture(_CapabilityAvailabilityModel):
    lane_ref: str
    capability_ref: str
    display_label: str = Field(..., min_length=1, max_length=160)
    implementation_status: Literal["implemented_exact_lane"] = "implemented_exact_lane"
    runtime_availability: str = Field(..., min_length=1, max_length=120)
    provider_ref: str
    adapter_ref: str
    side_effect_class: Literal["read_only_external"] = "read_only_external"
    approval_posture: str = Field(..., min_length=1, max_length=120)
    authority_posture: Literal["request_scoped_evaluation_required"] = (
        "request_scoped_evaluation_required"
    )
    cost_posture: Literal["not_metered", "metered_free_plan_only"]
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)

    @field_validator("lane_ref", "capability_ref", "provider_ref", "adapter_ref")
    @classmethod
    def validate_lane_refs(cls, value: str) -> str:
        validate_execution_ref(value, "web_hybrid_lane_ref")
        return value

    @field_validator("display_label", "runtime_availability", "approval_posture")
    @classmethod
    def validate_lane_text(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_lane_codes(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)


class WebResearchAggregationPosture(_CapabilityAvailabilityModel):
    schema_version: Literal["uaa-web-research-aggregation-posture.v1"] = (
        "uaa-web-research-aggregation-posture.v1"
    )
    contract_ref: str = "contract-ref:web-research-aggregation:v1"
    status: Literal["implemented_injected_observations_required"] = (
        "implemented_injected_observations_required"
    )
    current_observation_status: Literal["not_injected_by_read_only_route"] = (
        "not_injected_by_read_only_route"
    )
    current_citation_count: Literal[0] = 0
    citation_limit: Literal[10] = 10
    summary_character_limit: Literal[4000] = 4000
    deterministic_injected_observations_only: Literal[True] = True
    provider_readiness_included: Literal[True] = True
    provider_latency_posture_included: Literal[True] = True
    provider_cost_posture_included: Literal[True] = True
    provider_context_posture_included: Literal[True] = True
    provider_routing_posture_included: Literal[True] = True
    excluded_source_reasons_included: Literal[True] = True
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True
    context_injection_authorized: Literal[False] = False
    memory_write_authorized: Literal[False] = False
    action_execution_authorized: Literal[False] = False
    raw_query_persisted: Literal[False] = False
    raw_page_content_persisted: Literal[False] = False
    raw_provider_payload_persisted: Literal[False] = False
    proof_refs: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=700)

    @field_validator("contract_ref", "proof_refs")
    @classmethod
    def validate_refs(cls, value: str | list[str]) -> str | list[str]:
        values = [value] if isinstance(value, str) else value
        for item in values:
            validate_execution_ref(item, "web_research_aggregation_posture_ref")
        return value

    @field_validator("blocker_codes")
    @classmethod
    def validate_blockers(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value


class WebHybridAvailabilityReadModel(_CapabilityAvailabilityModel):
    schema_version: Literal["uaa-web-hybrid-availability.v1"] = (
        "uaa-web-hybrid-availability.v1"
    )
    read_model_ref: str = "web-hybrid-read-model-ref:operator:v1"
    truth_owner: Literal["python_core"] = "python_core"
    status: Literal["implemented_runtime_observation_required"] = (
        "implemented_runtime_observation_required"
    )
    cli_ref: str = "repo-local-command:inspect-web-hybrid-status"
    cli_path: Literal["scripts/inspect_web_hybrid_status.py"] = (
        "scripts/inspect_web_hybrid_status.py"
    )
    lanes: list[WebHybridCapabilityLanePosture]
    research_aggregation: WebResearchAggregationPosture
    routing_policy: Literal["self_host_first_cloud_escalation"] = (
        "self_host_first_cloud_escalation"
    )
    routing_attempt_ceiling: Literal[2] = 2
    cloud_first_enabled: Literal[False] = False
    paid_usage_enabled: Literal[False] = False
    keyless_enabled: Literal[False] = False
    provider_zero_data_retention_claimed: Literal[False] = False
    current_credit_snapshot_status: Literal["not_observed_by_read_only_route"] = (
        "not_observed_by_read_only_route"
    )
    current_remaining_credits: None = None
    reviewed_free_plan_credits: Literal[1000] = 1000
    reviewed_free_plan_concurrency: Literal[2] = 2
    uaa_effective_cloud_concurrency: Literal[1] = 1
    reviewed_standard_scrape_credits: Literal[1] = 1
    cost_policy_ref: str = "cost-policy-ref:firecrawl-standard-scrape:v1"
    credential_ref: str = "credential-ref:firecrawl-cloud:ignored-local-file"
    circuit_state: Literal["unknown_until_runtime_inspection"] = (
        "unknown_until_runtime_inspection"
    )
    circuit_ref: str = "web-provider-circuit-ref:firecrawl-cloud:v1"
    request_scoped_evaluation_required: Literal[True] = True
    final_start_revalidation_required: Literal[True] = True
    mission_scoped_lease_required: Literal[True] = True
    complete_request_fingerprint_required: Literal[True] = True
    start_deadline_required: Literal[True] = True
    local_approval_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    budget_reservation_required_for_cloud: Literal[True] = True
    external_content_untrusted: Literal[True] = True
    instruction_authority_granted: Literal[False] = False
    memory_write_allowed: Literal[False] = False
    context_injection_allowed: Literal[False] = False
    browser_actions_allowed: Literal[False] = False
    raw_page_persisted: Literal[False] = False
    raw_provider_payload_persisted: Literal[False] = False
    credential_material_returned: Literal[False] = False
    provider_network_call_performed: Literal[False] = False
    proof_refs: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=700)

    @field_validator(
        "read_model_ref",
        "cli_ref",
        "cost_policy_ref",
        "credential_ref",
        "circuit_ref",
    )
    @classmethod
    def validate_web_refs(cls, value: str) -> str:
        validate_execution_ref(value, "web_hybrid_read_model_ref")
        return value

    @field_validator("proof_refs")
    @classmethod
    def validate_web_proof_refs(cls, values: list[str]) -> list[str]:
        for value in values:
            validate_execution_ref(value, "web_hybrid_proof_ref")
        return list(dict.fromkeys(values))

    @field_validator("blocker_codes")
    @classmethod
    def validate_web_blockers(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)

    @field_validator("safe_summary")
    @classmethod
    def validate_web_summary(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value


class CapabilityAvailabilityReadModel(_CapabilityAvailabilityModel):
    schema_version: Literal["uaa-capability-availability-read-model.v1"] = (
        CAPABILITY_AVAILABILITY_READ_MODEL_SCHEMA_VERSION
    )
    read_model_ref: str
    generated_at: datetime
    truth_owner: Literal["python_core"] = "python_core"
    source_ref: str
    route_ref: Literal["GET /control-center/capabilities/availability"] = (
        CAPABILITY_AVAILABILITY_ROUTE_REF
    )
    cli_ref: str = CAPABILITY_AVAILABILITY_CLI_REF
    invocation_decision_contract_ref: str = (
        CAPABILITY_INVOCATION_DECISION_CONTRACT_REF
    )
    execution_receipt_contract_ref: str = EXECUTION_RECEIPT_CONTRACT_REF
    authority_boundary: Literal["request_scoped_evaluation_required"] = (
        "request_scoped_evaluation_required"
    )
    redaction_posture: Literal["safe_refs_and_bounded_summaries_only"] = (
        "safe_refs_and_bounded_summaries_only"
    )
    probe_posture: Literal["injected_observations_only"] = (
        "injected_observations_only"
    )
    execution_evidence_posture: Literal["separate_receipt_contract"] = (
        "separate_receipt_contract"
    )
    request_scoped_evaluation_required: Literal[True] = True
    availability_does_not_grant_execution: Literal[True] = True
    web_hybrid: WebHybridAvailabilityReadModel
    snapshots: list[CapabilityAvailabilitySnapshot] = Field(default_factory=list)
    snapshot_count: int = Field(..., ge=0)
    readiness_counts: dict[str, int] = Field(default_factory=dict)
    authority_counts: dict[str, int] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=700)

    @field_validator(
        "read_model_ref",
        "source_ref",
        "cli_ref",
        "invocation_decision_contract_ref",
        "execution_receipt_contract_ref",
    )
    @classmethod
    def validate_read_model_refs(cls, value: str) -> str:
        validate_execution_ref(value, "capability_availability_read_model_ref")
        return value

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: datetime) -> datetime:
        return _aware_datetime(value, "generated_at")

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_read_model_codes(cls, values: list[str]) -> list[str]:
        return _validated_codes(values)

    @field_validator("safe_summary")
    @classmethod
    def validate_read_model_summary(cls, value: str) -> str:
        _validate_safe_summary(value)
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> "CapabilityAvailabilityReadModel":
        if self.snapshot_count != len(self.snapshots):
            raise ValueError("CAPABILITY_AVAILABILITY_SNAPSHOT_COUNT_MISMATCH")
        if len({item.capability_ref for item in self.snapshots}) != len(self.snapshots):
            raise ValueError("CAPABILITY_AVAILABILITY_CAPABILITY_REF_DUPLICATE")
        expected_readiness = {
            status.value: sum(
                item.runtime_readiness_status == status for item in self.snapshots
            )
            for status in DerivedRuntimeReadinessStatus
        }
        expected_authority = {
            status.value: sum(item.authority_posture == status for item in self.snapshots)
            for status in AuthorityPosture
        }
        if self.readiness_counts != expected_readiness:
            raise ValueError("CAPABILITY_AVAILABILITY_READINESS_COUNTS_MISMATCH")
        if self.authority_counts != expected_authority:
            raise ValueError("CAPABILITY_AVAILABILITY_AUTHORITY_COUNTS_MISMATCH")
        return self


def _derivation(
    status: DerivedRuntimeReadinessStatus,
    reason_code: str,
    blocker_code: str | None,
) -> RuntimeReadinessDerivation:
    return RuntimeReadinessDerivation(
        status=status,
        reason_codes=[reason_code],
        blocker_codes=[blocker_code] if blocker_code else [],
    )


def _validated_codes(values: list[str]) -> list[str]:
    deduped = _dedupe(values)
    if any(not _SAFE_CODE_RE.fullmatch(value) for value in deduped):
        raise ValueError("CAPABILITY_AVAILABILITY_CODE_UNSAFE")
    return deduped


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _aware_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _validate_safe_summary(value: str) -> None:
    validate_safe_execution_text(value, "capability_availability_safe_summary")
    if _RAW_ENV_ASSIGNMENT_RE.search(value):
        raise ValueError("CAPABILITY_AVAILABILITY_RAW_ENV_VALUE_REJECTED")
    if _RAW_USERNAME_RE.search(value):
        raise ValueError("CAPABILITY_AVAILABILITY_USERNAME_REJECTED")
    if _HOSTNAME_RE.search(value):
        raise ValueError("CAPABILITY_AVAILABILITY_HOSTNAME_REJECTED")


def _exact_local_approval_valid(
    decision: PolicyDecision | None,
    *,
    capability_ref: str,
    task_ref: str | None,
) -> bool:
    if decision is None:
        return False
    if decision.status != PolicyDecisionStatus.allowed or not decision.allowed:
        return False
    if decision.capability_id != capability_ref:
        return False
    if task_ref is not None and decision.task_id != task_ref:
        return False
    return "APPROVAL_GRANT_VALID" in decision.reason_codes


def _exact_authority_lease_valid(
    decision: AuthorityPolicyDecision | None,
    *,
    capability_ref: str,
) -> bool:
    return bool(
        decision is not None
        and decision.outcome == AuthorityDecisionOutcome.allow.value
        and decision.known_authority
        and decision.lease_ref
        and decision.capability_ref == capability_ref
        and not decision.unsupported_adapter
    )


def _policy_decision_ref(decision: PolicyDecision) -> str:
    payload = decision.model_dump(mode="json")
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    return f"policy-decision-ref:{digest}"


def _stable_decision_ref(
    *,
    request: CapabilityInvocationRequest,
    snapshot: CapabilityAvailabilitySnapshot,
    policy_decision: PolicyDecision,
    authority_decision: AuthorityPolicyDecision | None,
    local_approval_decision: PolicyDecision | None,
    budget_decision: CostDecision | None,
    outcome: InvocationDecisionOutcome,
    blocker_codes: list[str],
) -> str:
    payload: dict[str, Any] = {
        "request": request.model_dump(mode="json"),
        "snapshot_ref": snapshot.snapshot_ref,
        "policy": policy_decision.model_dump(mode="json"),
        "authority_decision_ref": (
            authority_decision.decision_ref if authority_decision else None
        ),
        "approval": (
            local_approval_decision.model_dump(mode="json")
            if local_approval_decision
            else None
        ),
        "budget": budget_decision.model_dump(mode="json") if budget_decision else None,
        "outcome": outcome.value,
        "blockers": blocker_codes,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"capability-invocation-decision-ref:{digest}"
