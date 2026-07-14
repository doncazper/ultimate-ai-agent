from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from itertools import islice
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
    CapabilityAvailabilitySnapshot,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    CostPosture,
    DerivedRuntimeReadinessStatus,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
    build_capability_availability_snapshot,
    validate_capability_availability_safe_text,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


PROVIDER_ROUTING_INTELLIGENCE_CONTRACT_REF = (
    "contract-ref:provider-routing-intelligence:v1"
)
PROVIDER_ROUTING_INTELLIGENCE_SOURCE_REF = (
    "source-ref:model-router:deterministic-routing-patterns:v0.8.9"
)
PROVIDER_ROUTING_INVOCATION_CAPABILITY_REF = "capability-ref:provider-model-invocation"
PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES = 4
PROVIDER_ROUTING_MAX_OBSERVATIONS = 32

_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:@-]{2,220}$")
_SAFE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,119}$")
_FINGERPRINT_REF_RE = re.compile(
    r"^(?:request|observation|observation-set)-fingerprint-ref:[a-f0-9]{64}$"
)
_PROPOSAL_REF_RE = re.compile(r"^provider-routing-proposal-ref:[a-f0-9]{64}$")
_CANDIDATE_REF_RE = re.compile(r"^provider-routing-candidate-ref:[a-f0-9]{64}$")
_IPV4_LITERAL_RE = re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])")
_LOCALHOST_RE = re.compile(r"(?i)(?<![A-Za-z0-9])localhost(?![A-Za-z0-9])|::1")


class ProviderRoutingStrategy(str, Enum):
    best_value = "best_value"
    lowest_cost = "lowest_cost"
    lowest_latency = "lowest_latency"
    best_quality = "best_quality"
    local_first = "local_first"


class ProviderRoutingRuntimeClass(str, Enum):
    local = "local"
    hosted = "hosted"
    unknown = "unknown"


# Compatibility aliases preserve the public import surface while canonical
# availability contracts remain the sole status definitions.
ProviderRoutingCompatibilityStatus = CompatibilityStatus
ProviderRoutingConfigurationStatus = ConfigurationStatus
ProviderRoutingHealthStatus = HealthStatus
ProviderRoutingBudgetStatus = ResourceBudgetStatus
ProviderRoutingSafeDisableStatus = SafeDisableStatus


class ProviderRoutingCandidateStatus(str, Enum):
    eligible_for_request_scoped_evaluation = "eligible_for_request_scoped_evaluation"
    blocked = "blocked"


class _ProviderRoutingModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
        allow_inf_nan=False,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        payload = self.model_dump(mode="python")
        if update:
            payload.update(update)
        return self.__class__.model_validate(payload)


class ProviderRoutingAvailabilitySnapshot(_ProviderRoutingModel):
    schema_version: Literal["uaa-capability-availability.v1"] = (
        "uaa-capability-availability.v1"
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
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    blocker_codes: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    probe_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def preserve_canonical_availability_truth(
        self,
    ) -> "ProviderRoutingAvailabilitySnapshot":
        canonical = CapabilityAvailabilitySnapshot.model_validate(
            self.model_dump(mode="python")
        )
        if canonical.model_dump(mode="json") != self.model_dump(mode="json"):
            raise ValueError("PROVIDER_ROUTING_AVAILABILITY_PROJECTION_DRIFT")
        return self


def _project_availability_snapshot(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    return value


class ProviderRoutingNeed(_ProviderRoutingModel):
    request_ref: str = "provider-routing-request-ref:control-plane:default"
    task_ref: str = "task-ref:provider-routing:operator-inspection"
    strategy: ProviderRoutingStrategy = ProviderRoutingStrategy.best_value
    required_capability_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=12,
    )
    minimum_context_tokens: int = Field(0, ge=0, le=2_000_000)
    maximum_presented_candidates: int = Field(
        PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
        ge=1,
        le=PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
    )

    @model_validator(mode="after")
    def validate_need(self) -> "ProviderRoutingNeed":
        _validate_safe_refs(
            [self.request_ref, self.task_ref, *self.required_capability_refs],
            "PROVIDER_ROUTING_NEED_REF_INVALID",
        )
        if self.required_capability_refs != tuple(
            sorted(set(self.required_capability_refs))
        ):
            raise ValueError("PROVIDER_ROUTING_REQUIRED_CAPABILITY_SET_INVALID")
        _reject_unsafe(self.model_dump(mode="json"), "PROVIDER_ROUTING_NEED_UNSAFE")
        return self


class ProviderRoutingObservation(_ProviderRoutingModel):
    observation_ref: str
    provider_ref: str
    provider_label: str = Field(..., min_length=1, max_length=120)
    provider_manifest_ref: str
    model_ref: str
    adapter_ref: str
    runtime_class: ProviderRoutingRuntimeClass
    availability_snapshot: ProviderRoutingAvailabilitySnapshot
    metered: bool
    estimated_cost_usd: float | None = Field(None, ge=0, le=1_000_000)
    estimated_latency_ms: float | None = Field(None, ge=0, le=3_600_000)
    quality_score: float | None = Field(None, ge=0, le=100)
    context_tokens: int | None = Field(None, ge=1, le=2_000_000)
    capability_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=24)
    evidence_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
        max_length=24,
    )
    source_ref: str

    @field_validator("provider_label")
    @classmethod
    def validate_provider_label(cls, value: str) -> str:
        return validate_capability_availability_safe_text(
            value,
            "provider_routing_provider_label",
        )

    @field_validator("availability_snapshot", mode="before")
    @classmethod
    def project_availability_snapshot(cls, value: object) -> object:
        return _project_availability_snapshot(value)

    @model_validator(mode="after")
    def validate_observation(self) -> "ProviderRoutingObservation":
        _validate_safe_refs(
            [
                self.observation_ref,
                self.provider_ref,
                self.provider_manifest_ref,
                self.model_ref,
                self.adapter_ref,
                *self.capability_refs,
                *self.evidence_refs,
                self.source_ref,
            ],
            "PROVIDER_ROUTING_OBSERVATION_REF_INVALID",
        )
        snapshot = self.availability_snapshot
        if snapshot.provider_ref != self.provider_ref:
            raise ValueError("PROVIDER_ROUTING_SNAPSHOT_PROVIDER_REF_MISMATCH")
        if snapshot.adapter_ref != self.adapter_ref:
            raise ValueError("PROVIDER_ROUTING_SNAPSHOT_ADAPTER_REF_MISMATCH")
        if snapshot.source_ref != self.source_ref:
            raise ValueError("PROVIDER_ROUTING_SNAPSHOT_SOURCE_REF_MISMATCH")
        if snapshot.capability_ref != PROVIDER_ROUTING_INVOCATION_CAPABILITY_REF:
            raise ValueError("PROVIDER_ROUTING_SNAPSHOT_CAPABILITY_REF_MISMATCH")
        expected_cost_posture = (
            CostPosture.metered if self.metered else CostPosture.not_metered
        )
        if snapshot.cost_posture != expected_cost_posture:
            raise ValueError("PROVIDER_ROUTING_SNAPSHOT_COST_POSTURE_MISMATCH")
        if self.capability_refs != tuple(sorted(set(self.capability_refs))):
            raise ValueError("PROVIDER_ROUTING_CAPABILITY_SET_INVALID")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("PROVIDER_ROUTING_EVIDENCE_SET_INVALID")
        if self.evidence_refs != tuple(snapshot.evidence_refs):
            raise ValueError("PROVIDER_ROUTING_SNAPSHOT_EVIDENCE_INCOMPLETE")
        _reject_unsafe(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTING_OBSERVATION_UNSAFE",
        )
        return self


class ProviderRoutingCandidate(_ProviderRoutingModel):
    candidate_ref: str
    observation_ref: str
    observation_fingerprint_ref: str
    rank: int | None = Field(None, ge=1, le=PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES)
    provider_ref: str
    provider_label: str
    provider_manifest_ref: str
    model_ref: str
    adapter_ref: str
    runtime_class: ProviderRoutingRuntimeClass
    status: ProviderRoutingCandidateStatus
    availability_snapshot: ProviderRoutingAvailabilitySnapshot
    estimated_cost_usd: float | None = Field(None, ge=0, le=1_000_000)
    estimated_latency_ms: float | None = Field(None, ge=0, le=3_600_000)
    quality_score: float | None = Field(None, ge=0, le=100)
    reason_codes: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
        max_length=64,
    )
    blocker_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    evidence_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
        max_length=24,
    )
    safe_summary: str = Field(..., min_length=1, max_length=500)
    proposal_only: Literal[True] = True
    invocation_authorized: Literal[False] = False
    provider_call_performed: Literal[False] = False

    @field_validator("provider_label", "safe_summary")
    @classmethod
    def validate_safe_text(cls, value: str) -> str:
        return validate_capability_availability_safe_text(
            value,
            "provider_routing_candidate_text",
        )

    @field_validator("availability_snapshot", mode="before")
    @classmethod
    def project_availability_snapshot(cls, value: object) -> object:
        return _project_availability_snapshot(value)

    @model_validator(mode="after")
    def validate_candidate(self) -> "ProviderRoutingCandidate":
        _validate_safe_refs(
            [
                self.candidate_ref,
                self.observation_ref,
                self.observation_fingerprint_ref,
                self.provider_ref,
                self.provider_manifest_ref,
                self.model_ref,
                self.adapter_ref,
                *self.evidence_refs,
            ],
            "PROVIDER_ROUTING_CANDIDATE_REF_INVALID",
        )
        _validate_codes(self.reason_codes, "PROVIDER_ROUTING_REASON_CODE_INVALID")
        _validate_codes(self.blocker_codes, "PROVIDER_ROUTING_BLOCKER_CODE_INVALID")
        if _CANDIDATE_REF_RE.fullmatch(self.candidate_ref) is None:
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_FINGERPRINT_INVALID")
        if _FINGERPRINT_REF_RE.fullmatch(self.observation_fingerprint_ref) is None:
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_FINGERPRINT_INVALID")
        snapshot = self.availability_snapshot
        if snapshot.provider_ref != self.provider_ref:
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_PROVIDER_REF_MISMATCH")
        if snapshot.adapter_ref != self.adapter_ref:
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_ADAPTER_REF_MISMATCH")
        if snapshot.capability_ref != PROVIDER_ROUTING_INVOCATION_CAPABILITY_REF:
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_CAPABILITY_REF_MISMATCH")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_EVIDENCE_SET_INVALID")
        if self.evidence_refs != tuple(snapshot.evidence_refs):
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_EVIDENCE_INCOMPLETE")
        if not set(snapshot.reason_codes).issubset(self.reason_codes):
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_REASON_INCOMPLETE")
        if not set(snapshot.blocker_codes).issubset(self.blocker_codes):
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_BLOCKER_INCOMPLETE")
        if snapshot.authority_posture == AuthorityPosture.blocked:
            if (
                self.status != ProviderRoutingCandidateStatus.blocked.value
                or "PROVIDER_INVOCATION_AUTHORITY_BLOCKED" not in self.blocker_codes
            ):
                raise ValueError("PROVIDER_ROUTING_BLOCKED_AUTHORITY_CANDIDATE_INVALID")
        elif snapshot.authority_posture == AuthorityPosture.approval_required:
            if "PROVIDER_APPROVAL_REQUIRED_BEFORE_INVOCATION" not in self.reason_codes:
                raise ValueError("PROVIDER_ROUTING_APPROVAL_POSTURE_REASON_REQUIRED")
        elif snapshot.authority_posture == AuthorityPosture.lease_required:
            if "PROVIDER_LEASE_REQUIRED_BEFORE_INVOCATION" not in self.reason_codes:
                raise ValueError("PROVIDER_ROUTING_LEASE_POSTURE_REASON_REQUIRED")
        elif "PROVIDER_ELIGIBLE_FOR_POLICY_EVALUATION" not in self.reason_codes:
            raise ValueError("PROVIDER_ROUTING_POLICY_EVALUATION_REASON_REQUIRED")
        if self.status == (
            ProviderRoutingCandidateStatus.eligible_for_request_scoped_evaluation.value
        ):
            required_revalidation_reasons = {
                "PROVIDER_REQUEST_SCOPED_APPROVAL_REVALIDATION_REQUIRED",
                "PROVIDER_REQUEST_SCOPED_AUTHORITY_LEASE_REVALIDATION_REQUIRED",
            }
            if not required_revalidation_reasons.issubset(self.reason_codes):
                raise ValueError("PROVIDER_ROUTING_AUTHORITY_REVALIDATION_REQUIRED")
        expected_candidate_ref = _candidate_decision_ref(self)
        if self.candidate_ref != expected_candidate_ref:
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_FINGERPRINT_DRIFT")
        if self.status == ProviderRoutingCandidateStatus.blocked.value:
            if not self.blocker_codes or self.rank is not None:
                raise ValueError("PROVIDER_ROUTING_BLOCKED_CANDIDATE_INVALID")
        elif self.blocker_codes:
            raise ValueError("PROVIDER_ROUTING_ELIGIBLE_CANDIDATE_HAS_BLOCKERS")
        if (
            self.status
            == ProviderRoutingCandidateStatus.eligible_for_request_scoped_evaluation.value
            and self.availability_snapshot.runtime_readiness_status
            != DerivedRuntimeReadinessStatus.ready
        ):
            raise ValueError("PROVIDER_ROUTING_ELIGIBLE_CANDIDATE_NOT_RUNTIME_READY")
        _reject_unsafe(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTING_CANDIDATE_UNSAFE",
        )
        return self


class ProviderRoutingProposal(_ProviderRoutingModel):
    schema_version: Literal["provider_routing_intelligence.v1"] = (
        "provider_routing_intelligence.v1"
    )
    contract_ref: Literal["contract-ref:provider-routing-intelligence:v1"] = (
        PROVIDER_ROUTING_INTELLIGENCE_CONTRACT_REF
    )
    proposal_ref: str
    request: ProviderRoutingNeed
    request_ref: str
    request_fingerprint_ref: str
    observation_fingerprint_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=PROVIDER_ROUTING_MAX_OBSERVATIONS,
    )
    observation_set_fingerprint_ref: str
    strategy: ProviderRoutingStrategy
    status: Literal["proposal_only"] = "proposal_only"
    observations: tuple[ProviderRoutingObservation, ...] = Field(
        default_factory=tuple,
        max_length=PROVIDER_ROUTING_MAX_OBSERVATIONS,
    )
    candidates: tuple[ProviderRoutingCandidate, ...] = Field(
        default_factory=tuple,
        max_length=PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
    )
    evaluated_candidates: tuple[ProviderRoutingCandidate, ...] = Field(
        default_factory=tuple,
        max_length=PROVIDER_ROUTING_MAX_OBSERVATIONS,
    )
    observed_candidate_count: int = Field(..., ge=0)
    presented_candidate_count: int = Field(..., ge=0)
    omitted_candidate_count: int = Field(..., ge=0)
    recommended_candidate_ref: str | None = None
    approval_queue_route_ref: str = "route-ref:control-center-approval-queue"
    run_detail_group_ref: str = "run-detail-group-ref:provider-routing-decision"
    bounded_fanout_presentation_ref: str = (
        "presentation-ref:provider-routing:bounded-candidates"
    )
    source_ref: str = PROVIDER_ROUTING_INTELLIGENCE_SOURCE_REF
    reason_codes: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
        max_length=64,
    )
    blocker_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    maximum_presented_candidates: int = Field(
        PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
        ge=1,
        le=PROVIDER_ROUTING_MAX_PRESENTED_CANDIDATES,
    )
    proposal_only: Literal[True] = True
    deterministic: Literal[True] = True
    safe_refs_only: Literal[True] = True
    approval_refs_are_identifiers_only: Literal[True] = True
    request_scoped_invocation_decision_required: Literal[True] = True
    fresh_local_approval_validation_required: Literal[True] = True
    fresh_authority_lease_evaluation_required: Literal[True] = True
    invocation_authorized: Literal[False] = False
    provider_call_performed: Literal[False] = False

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        return validate_capability_availability_safe_text(
            value,
            "provider_routing_proposal_summary",
        )

    fallback_execution_performed: Literal[False] = False
    background_fanout_performed: Literal[False] = False
    raw_prompt_persisted: Literal[False] = False
    raw_response_persisted: Literal[False] = False
    raw_provider_payload_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_proposal(self) -> "ProviderRoutingProposal":
        refs = [
            self.contract_ref,
            self.proposal_ref,
            self.request_ref,
            self.request_fingerprint_ref,
            self.observation_set_fingerprint_ref,
            *self.observation_fingerprint_refs,
            self.approval_queue_route_ref,
            self.run_detail_group_ref,
            self.bounded_fanout_presentation_ref,
            self.source_ref,
        ]
        if self.recommended_candidate_ref is not None:
            refs.append(self.recommended_candidate_ref)
        _validate_safe_refs(refs, "PROVIDER_ROUTING_PROPOSAL_REF_INVALID")
        _validate_codes(self.reason_codes, "PROVIDER_ROUTING_REASON_CODE_INVALID")
        _validate_codes(self.blocker_codes, "PROVIDER_ROUTING_BLOCKER_CODE_INVALID")
        if self.request_ref != self.request.request_ref:
            raise ValueError("PROVIDER_ROUTING_REQUEST_REF_MISMATCH")
        if self.strategy != self.request.strategy:
            raise ValueError("PROVIDER_ROUTING_REQUEST_STRATEGY_MISMATCH")
        if (
            self.maximum_presented_candidates
            != self.request.maximum_presented_candidates
        ):
            raise ValueError("PROVIDER_ROUTING_REQUEST_PRESENTATION_LIMIT_MISMATCH")
        if self.request_fingerprint_ref != _request_fingerprint(self.request):
            raise ValueError("PROVIDER_ROUTING_REQUEST_FINGERPRINT_DRIFT")
        if _PROPOSAL_REF_RE.fullmatch(self.proposal_ref) is None:
            raise ValueError("PROVIDER_ROUTING_PROPOSAL_FINGERPRINT_INVALID")
        fingerprint_refs = [
            self.request_fingerprint_ref,
            self.observation_set_fingerprint_ref,
            *self.observation_fingerprint_refs,
        ]
        if any(
            _FINGERPRINT_REF_RE.fullmatch(value) is None for value in fingerprint_refs
        ):
            raise ValueError("PROVIDER_ROUTING_FINGERPRINT_REF_INVALID")
        if self.presented_candidate_count != len(self.candidates):
            raise ValueError("PROVIDER_ROUTING_PRESENTED_COUNT_DRIFT")
        if self.observed_candidate_count != len(self.evaluated_candidates):
            raise ValueError("PROVIDER_ROUTING_EVALUATED_COUNT_DRIFT")
        if self.observed_candidate_count != len(self.observations):
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_COUNT_DRIFT")
        if self.presented_candidate_count != min(
            self.observed_candidate_count,
            self.maximum_presented_candidates,
        ):
            raise ValueError("PROVIDER_ROUTING_PRESENTATION_UNDERFILLED")
        if self.omitted_candidate_count != (
            self.observed_candidate_count - self.presented_candidate_count
        ):
            raise ValueError("PROVIDER_ROUTING_OMITTED_COUNT_DRIFT")
        if len(self.candidates) > self.maximum_presented_candidates:
            raise ValueError("PROVIDER_ROUTING_PRESENTATION_LIMIT_EXCEEDED")
        if self.observed_candidate_count != len(self.observation_fingerprint_refs):
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_FINGERPRINT_COUNT_DRIFT")
        if self.observation_fingerprint_refs != tuple(
            sorted(set(self.observation_fingerprint_refs))
        ):
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_FINGERPRINT_SET_INVALID")
        if tuple(
            observation.provider_ref for observation in self.observations
        ) != tuple(
            sorted(observation.provider_ref for observation in self.observations)
        ):
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_ORDER_DRIFT")
        expected_observation_fingerprints = tuple(
            sorted(_observation_fingerprint(row) for row in self.observations)
        )
        if expected_observation_fingerprints != self.observation_fingerprint_refs:
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_PROJECTION_DRIFT")
        evaluated_fingerprints = tuple(
            sorted(
                candidate.observation_fingerprint_ref
                for candidate in self.evaluated_candidates
            )
        )
        if evaluated_fingerprints != self.observation_fingerprint_refs:
            raise ValueError("PROVIDER_ROUTING_EVALUATED_FINGERPRINT_SET_DRIFT")
        if any(candidate.rank is not None for candidate in self.evaluated_candidates):
            raise ValueError("PROVIDER_ROUTING_EVALUATED_CANDIDATE_RANK_INVALID")
        if tuple(
            candidate.provider_ref for candidate in self.evaluated_candidates
        ) != tuple(
            sorted(candidate.provider_ref for candidate in self.evaluated_candidates)
        ):
            raise ValueError("PROVIDER_ROUTING_EVALUATED_ORDER_DRIFT")
        expected_evaluated_candidates = tuple(
            sorted(
                (
                    _evaluate_candidate(self.request, observation)
                    for observation in self.observations
                ),
                key=lambda candidate: candidate.provider_ref,
            )
        )
        if self.evaluated_candidates != expected_evaluated_candidates:
            raise ValueError("PROVIDER_ROUTING_EVALUATION_PROJECTION_DRIFT")
        for values, error_code in (
            (
                [candidate.candidate_ref for candidate in self.evaluated_candidates],
                "PROVIDER_ROUTING_EVALUATED_CANDIDATE_DUPLICATE",
            ),
            (
                [candidate.observation_ref for candidate in self.evaluated_candidates],
                "PROVIDER_ROUTING_EVALUATED_OBSERVATION_DUPLICATE",
            ),
            (
                [candidate.provider_ref for candidate in self.evaluated_candidates],
                "PROVIDER_ROUTING_EVALUATED_PROVIDER_DUPLICATE",
            ),
            (
                [candidate.candidate_ref for candidate in self.candidates],
                "PROVIDER_ROUTING_PRESENTED_CANDIDATE_DUPLICATE",
            ),
            (
                [candidate.observation_ref for candidate in self.candidates],
                "PROVIDER_ROUTING_PRESENTED_OBSERVATION_DUPLICATE",
            ),
            (
                [candidate.provider_ref for candidate in self.candidates],
                "PROVIDER_ROUTING_PRESENTED_PROVIDER_DUPLICATE",
            ),
        ):
            if len(values) != len(set(values)):
                raise ValueError(error_code)
        candidate_fingerprints = [
            candidate.observation_fingerprint_ref for candidate in self.candidates
        ]
        if not set(candidate_fingerprints).issubset(self.observation_fingerprint_refs):
            raise ValueError("PROVIDER_ROUTING_CANDIDATE_FINGERPRINT_NOT_BOUND")
        if self.observation_set_fingerprint_ref != _observation_set_fingerprint(
            self.observation_fingerprint_refs
        ):
            raise ValueError("PROVIDER_ROUTING_OBSERVATION_SET_FINGERPRINT_DRIFT")
        expected_blockers = tuple(
            sorted(
                {
                    code
                    for candidate in self.evaluated_candidates
                    for code in candidate.blocker_codes
                }
            )
        )
        if self.blocker_codes != expected_blockers:
            raise ValueError("PROVIDER_ROUTING_PROPOSAL_BLOCKER_SET_DRIFT")
        expected_reason_codes = (
            "PROVIDER_ROUTING_PROPOSAL_ONLY",
            (
                "PROVIDER_ROUTING_CANDIDATE_AVAILABLE"
                if any(
                    not candidate.blocker_codes
                    for candidate in self.evaluated_candidates
                )
                else "PROVIDER_ROUTING_NO_ELIGIBLE_CANDIDATE"
            ),
        )
        if self.reason_codes != expected_reason_codes:
            raise ValueError("PROVIDER_ROUTING_PROPOSAL_REASON_SET_DRIFT")
        presented_blockers = {
            code for candidate in self.candidates for code in candidate.blocker_codes
        }
        if not presented_blockers.issubset(self.blocker_codes):
            raise ValueError("PROVIDER_ROUTING_PROPOSAL_CANDIDATE_BLOCKER_INCOMPLETE")
        if self.proposal_ref != _proposal_ref(
            request_ref=self.request_ref,
            request_fingerprint_ref=self.request_fingerprint_ref,
            observation_set_fingerprint_ref=self.observation_set_fingerprint_ref,
            strategy=self.strategy,
            presented_candidate_refs=[
                candidate.candidate_ref for candidate in self.candidates
            ],
            evaluated_candidate_refs=[
                candidate.candidate_ref for candidate in self.evaluated_candidates
            ],
            observed_candidate_count=self.observed_candidate_count,
            omitted_candidate_count=self.omitted_candidate_count,
            recommended_candidate_ref=self.recommended_candidate_ref,
            reason_codes=self.reason_codes,
            blocker_codes=self.blocker_codes,
            maximum_presented_candidates=self.maximum_presented_candidates,
            approval_queue_route_ref=self.approval_queue_route_ref,
            run_detail_group_ref=self.run_detail_group_ref,
            bounded_fanout_presentation_ref=self.bounded_fanout_presentation_ref,
            source_ref=self.source_ref,
            safe_summary=self.safe_summary,
        ):
            raise ValueError("PROVIDER_ROUTING_PROPOSAL_FINGERPRINT_DRIFT")
        eligible = sorted(
            [
                candidate
                for candidate in self.evaluated_candidates
                if not candidate.blocker_codes
            ],
            key=lambda candidate: _candidate_sort_key(self.strategy, candidate),
        )
        blocked = sorted(
            [
                candidate
                for candidate in self.evaluated_candidates
                if candidate.blocker_codes
            ],
            key=lambda candidate: candidate.provider_ref,
        )
        eligible_for_presentation = eligible[: self.maximum_presented_candidates]
        expected_presented = (
            eligible_for_presentation
            + blocked[
                : self.maximum_presented_candidates - len(eligible_for_presentation)
            ]
        )
        if [candidate.candidate_ref for candidate in self.candidates] != [
            candidate.candidate_ref for candidate in expected_presented
        ]:
            raise ValueError("PROVIDER_ROUTING_PRESENTATION_SELECTION_DRIFT")
        expected_ranks = [
            index if index <= len(eligible_for_presentation) else None
            for index in range(1, len(expected_presented) + 1)
        ]
        if [candidate.rank for candidate in self.candidates] != expected_ranks:
            raise ValueError("PROVIDER_ROUTING_RANK_ORDER_INVALID")
        expected_recommendation = (
            eligible_for_presentation[0].candidate_ref
            if eligible_for_presentation
            else None
        )
        if self.recommended_candidate_ref != expected_recommendation:
            raise ValueError("PROVIDER_ROUTING_RECOMMENDATION_BINDING_INVALID")
        _reject_unsafe(
            self.model_dump(mode="json"),
            "PROVIDER_ROUTING_PROPOSAL_UNSAFE",
        )
        return self


def build_provider_routing_proposal(
    need: ProviderRoutingNeed,
    observations: Iterable[ProviderRoutingObservation],
) -> ProviderRoutingProposal:
    need = ProviderRoutingNeed.model_validate(need.model_dump(mode="python"))
    rows = [
        ProviderRoutingObservation.model_validate(row.model_dump(mode="python"))
        for row in islice(iter(observations), PROVIDER_ROUTING_MAX_OBSERVATIONS + 1)
    ]
    if len(rows) > PROVIDER_ROUTING_MAX_OBSERVATIONS:
        raise ValueError("PROVIDER_ROUTING_OBSERVATION_LIMIT_EXCEEDED")
    rows.sort(key=lambda observation: observation.provider_ref)
    observation_refs = [row.observation_ref for row in rows]
    if len(observation_refs) != len(set(observation_refs)):
        raise ValueError("PROVIDER_ROUTING_DUPLICATE_OBSERVATION_REF")
    provider_refs = [row.provider_ref for row in rows]
    if len(provider_refs) != len(set(provider_refs)):
        raise ValueError("PROVIDER_ROUTING_DUPLICATE_PROVIDER_REF")

    evaluated = sorted(
        [_evaluate_candidate(need, observation) for observation in rows],
        key=lambda candidate: candidate.provider_ref,
    )
    ranked = [candidate for candidate in evaluated if not candidate.blocker_codes]
    blocked = [candidate for candidate in evaluated if candidate.blocker_codes]
    ranked.sort(key=lambda candidate: _candidate_sort_key(need.strategy, candidate))
    blocked.sort(key=lambda candidate: candidate.provider_ref)

    ranked_for_presentation = ranked[: need.maximum_presented_candidates]
    ranked_with_positions = [
        candidate.model_copy(update={"rank": index})
        for index, candidate in enumerate(ranked_for_presentation, start=1)
    ]
    remaining_slots = need.maximum_presented_candidates - len(ranked_with_positions)
    presented = ranked_with_positions + blocked[:remaining_slots]
    recommended = (
        ranked_with_positions[0].candidate_ref if ranked_with_positions else None
    )
    request_fingerprint = _request_fingerprint(need)
    observation_fingerprint_refs = sorted(_observation_fingerprint(row) for row in rows)
    observation_set_fingerprint_ref = _observation_set_fingerprint(
        observation_fingerprint_refs
    )
    blocker_codes = sorted(
        {code for candidate in evaluated for code in candidate.blocker_codes}
    )
    reason_codes = ["PROVIDER_ROUTING_PROPOSAL_ONLY"]
    reason_codes.append(
        "PROVIDER_ROUTING_CANDIDATE_AVAILABLE"
        if recommended is not None
        else "PROVIDER_ROUTING_NO_ELIGIBLE_CANDIDATE"
    )
    observed_candidate_count = len(rows)
    omitted_candidate_count = len(rows) - len(presented)
    safe_summary = (
        "Provider routing proposal ranks bounded candidates using injected "
        "readiness, cost, latency, quality, and context observations. It does "
        "not authorize or perform provider invocation."
    )
    proposal_ref = _proposal_ref(
        request_ref=need.request_ref,
        request_fingerprint_ref=request_fingerprint,
        observation_set_fingerprint_ref=observation_set_fingerprint_ref,
        strategy=need.strategy,
        presented_candidate_refs=[candidate.candidate_ref for candidate in presented],
        evaluated_candidate_refs=[candidate.candidate_ref for candidate in evaluated],
        observed_candidate_count=observed_candidate_count,
        omitted_candidate_count=omitted_candidate_count,
        recommended_candidate_ref=recommended,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
        maximum_presented_candidates=need.maximum_presented_candidates,
        approval_queue_route_ref="route-ref:control-center-approval-queue",
        run_detail_group_ref="run-detail-group-ref:provider-routing-decision",
        bounded_fanout_presentation_ref=(
            "presentation-ref:provider-routing:bounded-candidates"
        ),
        source_ref=PROVIDER_ROUTING_INTELLIGENCE_SOURCE_REF,
        safe_summary=safe_summary,
    )
    return ProviderRoutingProposal(
        proposal_ref=proposal_ref,
        request=need,
        request_ref=need.request_ref,
        request_fingerprint_ref=request_fingerprint,
        observation_fingerprint_refs=observation_fingerprint_refs,
        observation_set_fingerprint_ref=observation_set_fingerprint_ref,
        strategy=need.strategy,
        observations=rows,
        candidates=presented,
        evaluated_candidates=evaluated,
        observed_candidate_count=observed_candidate_count,
        presented_candidate_count=len(presented),
        omitted_candidate_count=omitted_candidate_count,
        recommended_candidate_ref=recommended,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
        safe_summary=safe_summary,
        maximum_presented_candidates=need.maximum_presented_candidates,
    )


def observations_from_provider_readiness(
    provider_readiness_items: Iterable[object],
    *,
    checked_at: datetime,
) -> list[ProviderRoutingObservation]:
    rows = list(
        islice(iter(provider_readiness_items), PROVIDER_ROUTING_MAX_OBSERVATIONS + 1)
    )
    if len(rows) > PROVIDER_ROUTING_MAX_OBSERVATIONS:
        raise ValueError("PROVIDER_ROUTING_OBSERVATION_LIMIT_EXCEEDED")
    return [_observation_from_readiness(item, checked_at=checked_at) for item in rows]


def _observation_from_readiness(
    item: object,
    *,
    checked_at: datetime,
) -> ProviderRoutingObservation:
    provider_ref = str(_safe_get(item, "provider_id", "provider-ref:unknown:missing"))
    slug = _safe_slug(provider_ref)
    binding = _safe_get(item, "cost_governor_binding", {})
    model_ref = str(_safe_get(binding, "model_ref", f"model-ref:{slug}:not-selected"))
    readiness_posture = _enum_text(_safe_get(item, "readiness_posture", "unknown"))
    configured = bool(_safe_get(item, "credential_configured", False))
    manifest_ref = str(
        _safe_get(
            item, "provider_manifest_ref", f"provider-manifest-ref:{slug}:missing"
        )
    )
    adapter_ref = str(
        _safe_get(item, "adapter_ref", f"provider-adapter-ref:{slug}:not-scoped")
    )
    source_ref = "source-ref:python-core:provider-credential-readiness"
    evidence_refs = [
        str(
            _safe_get(
                binding, "binding_ref", f"provider-cost-binding-ref:{slug}:missing"
            )
        ),
        str(_safe_get(item, "policy_ref", f"policy-ref:{slug}:missing")),
    ]
    runtime_class_value = _enum_text(_safe_get(item, "runtime_class", "unknown"))
    runtime_class = (
        ProviderRoutingRuntimeClass(runtime_class_value)
        if runtime_class_value in {item.value for item in ProviderRoutingRuntimeClass}
        else ProviderRoutingRuntimeClass.unknown
    )
    configuration_status = ConfigurationStatus.unknown
    if readiness_posture == "configured" and configured:
        configuration_status = ConfigurationStatus.configured
    elif readiness_posture == "not_configured":
        configuration_status = ConfigurationStatus.not_configured
    elif readiness_posture == "revoked":
        configuration_status = ConfigurationStatus.invalid
    snapshot_blockers = [str(code) for code in _safe_get(item, "blocker_codes", [])]
    snapshot_blockers.append("PROVIDER_INVOCATION_AUTHORITY_BLOCKED")
    if bool(_safe_get(item, "provider_model_refs_bound", False)) is False:
        snapshot_blockers.append("PROVIDER_MODEL_REFS_REQUIRED")
    snapshot = build_capability_availability_snapshot(
        snapshot_ref=f"capability-availability-ref:provider-routing:{slug}",
        capability_ref=PROVIDER_ROUTING_INVOCATION_CAPABILITY_REF,
        provider_ref=provider_ref,
        adapter_ref=adapter_ref,
        catalog_status=CatalogStatus.unknown,
        compatibility_status=CompatibilityStatus.unknown,
        configuration_status=configuration_status,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.blocked,
        resource_status=ResourceBudgetStatus.unknown,
        cost_posture=CostPosture.metered,
        safe_disable_status=SafeDisableStatus.unknown,
        checked_at=checked_at,
        freshness_status=FreshnessStatus.unknown,
        source_ref=source_ref,
        safe_summary=(
            "Provider credential readiness preserves unknown compatibility, health, "
            "budget, freshness, and safe-disable truth; invocation remains blocked."
        ),
        reason_codes=["PROVIDER_CREDENTIAL_READINESS_ADAPTED"],
        blocker_codes=snapshot_blockers,
        evidence_refs=evidence_refs,
    )
    return ProviderRoutingObservation(
        observation_ref=f"provider-routing-observation-ref:{slug}:credential-readiness",
        provider_ref=provider_ref,
        provider_label=str(_safe_get(item, "provider_label", "Provider")),
        provider_manifest_ref=manifest_ref,
        model_ref=model_ref,
        adapter_ref=adapter_ref,
        runtime_class=runtime_class,
        availability_snapshot=snapshot,
        metered=True,
        evidence_refs=evidence_refs,
        source_ref=source_ref,
    )


def _evaluate_candidate(
    need: ProviderRoutingNeed,
    observation: ProviderRoutingObservation,
) -> ProviderRoutingCandidate:
    snapshot = observation.availability_snapshot
    blockers = list(snapshot.blocker_codes)
    reasons = ["PROVIDER_OBSERVATION_EVALUATED", *snapshot.reason_codes]
    if snapshot.authority_posture == AuthorityPosture.blocked:
        blockers.append("PROVIDER_INVOCATION_AUTHORITY_BLOCKED")
    elif snapshot.authority_posture == AuthorityPosture.approval_required:
        reasons.append("PROVIDER_APPROVAL_REQUIRED_BEFORE_INVOCATION")
    elif snapshot.authority_posture == AuthorityPosture.lease_required:
        reasons.append("PROVIDER_LEASE_REQUIRED_BEFORE_INVOCATION")
    else:
        reasons.append("PROVIDER_ELIGIBLE_FOR_POLICY_EVALUATION")
    reasons.extend(
        [
            "PROVIDER_REQUEST_SCOPED_APPROVAL_REVALIDATION_REQUIRED",
            "PROVIDER_REQUEST_SCOPED_AUTHORITY_LEASE_REVALIDATION_REQUIRED",
        ]
    )
    if snapshot.runtime_readiness_status != DerivedRuntimeReadinessStatus.ready:
        blockers.append("PROVIDER_RUNTIME_NOT_READY")
    if observation.metered and observation.estimated_cost_usd is None:
        blockers.append("METERED_PROVIDER_COST_UNKNOWN")
    missing_capabilities = set(need.required_capability_refs) - set(
        observation.capability_refs
    )
    if missing_capabilities:
        blockers.append("REQUIRED_CAPABILITY_MISSING")
    if need.minimum_context_tokens:
        if observation.context_tokens is None:
            blockers.append("CONTEXT_CAPACITY_UNKNOWN")
        elif observation.context_tokens < need.minimum_context_tokens:
            blockers.append("CONTEXT_CAPACITY_INSUFFICIENT")
    blockers = list(dict.fromkeys(blockers))
    reasons = list(dict.fromkeys(reasons))
    if blockers:
        status = ProviderRoutingCandidateStatus.blocked
        summary = "Provider candidate is blocked by fail-closed runtime evidence."
    else:
        status = ProviderRoutingCandidateStatus.eligible_for_request_scoped_evaluation
        reasons.append("ELIGIBLE_FOR_REQUEST_SCOPED_EVALUATION")
        summary = (
            "Provider candidate may proceed to exact request-scoped authority evaluation; "
            "this proposal grants no invocation authority."
        )
    candidate_fields = {
        "observation_ref": observation.observation_ref,
        "observation_fingerprint_ref": _observation_fingerprint(observation),
        "provider_ref": observation.provider_ref,
        "provider_label": observation.provider_label,
        "provider_manifest_ref": observation.provider_manifest_ref,
        "model_ref": observation.model_ref,
        "adapter_ref": observation.adapter_ref,
        "runtime_class": observation.runtime_class,
        "status": status,
        "availability_snapshot": snapshot,
        "estimated_cost_usd": observation.estimated_cost_usd,
        "estimated_latency_ms": observation.estimated_latency_ms,
        "quality_score": observation.quality_score,
        "reason_codes": tuple(reasons),
        "blocker_codes": tuple(blockers),
        "evidence_refs": tuple(observation.evidence_refs),
        "safe_summary": summary,
    }
    draft = ProviderRoutingCandidate.model_construct(
        candidate_ref="provider-routing-candidate-ref:" + "0" * 64,
        **candidate_fields,
    )
    return ProviderRoutingCandidate(
        candidate_ref=_candidate_decision_ref(draft),
        **candidate_fields,
    )


def _candidate_sort_key(
    strategy: ProviderRoutingStrategy | str,
    candidate: ProviderRoutingCandidate,
) -> tuple[float, float, float, str]:
    cost = (
        candidate.estimated_cost_usd
        if candidate.estimated_cost_usd is not None
        else float("inf")
    )
    latency = (
        candidate.estimated_latency_ms
        if candidate.estimated_latency_ms is not None
        else float("inf")
    )
    quality = candidate.quality_score if candidate.quality_score is not None else 0.0
    if strategy == ProviderRoutingStrategy.lowest_cost.value:
        return (cost, latency, -quality, candidate.provider_ref)
    if strategy == ProviderRoutingStrategy.lowest_latency.value:
        return (latency, cost, -quality, candidate.provider_ref)
    if strategy == ProviderRoutingStrategy.best_quality.value:
        return (-quality, cost, latency, candidate.provider_ref)
    if strategy == ProviderRoutingStrategy.local_first.value:
        local_rank = {
            ProviderRoutingRuntimeClass.local.value: 0,
            ProviderRoutingRuntimeClass.hosted.value: 1,
            ProviderRoutingRuntimeClass.unknown.value: 2,
        }[candidate.runtime_class]
        return (float(local_rank), cost, latency, candidate.provider_ref)
    value = quality / (1.0 + cost)
    return (-value, latency, cost, candidate.provider_ref)


def _candidate_decision_ref(candidate: ProviderRoutingCandidate) -> str:
    payload = json.dumps(
        candidate.model_dump(
            mode="json",
            exclude={"candidate_ref", "rank"},
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        f"provider-routing-candidate-ref:{hashlib.sha256(payload.encode()).hexdigest()}"
    )


def _request_fingerprint(need: ProviderRoutingNeed) -> str:
    payload = json.dumps(
        need.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return f"request-fingerprint-ref:{hashlib.sha256(payload.encode()).hexdigest()}"


def _observation_fingerprint(observation: ProviderRoutingObservation) -> str:
    payload = json.dumps(
        observation.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"observation-fingerprint-ref:{hashlib.sha256(payload.encode()).hexdigest()}"


def _observation_set_fingerprint(observation_fingerprint_refs: list[str]) -> str:
    payload = json.dumps(
        sorted(observation_fingerprint_refs),
        separators=(",", ":"),
    )
    return (
        "observation-set-fingerprint-ref:"
        f"{hashlib.sha256(payload.encode()).hexdigest()}"
    )


def _proposal_ref(
    *,
    request_ref: str,
    request_fingerprint_ref: str,
    observation_set_fingerprint_ref: str,
    strategy: ProviderRoutingStrategy | str,
    presented_candidate_refs: list[str],
    evaluated_candidate_refs: list[str],
    observed_candidate_count: int,
    omitted_candidate_count: int,
    recommended_candidate_ref: str | None,
    reason_codes: list[str],
    blocker_codes: list[str],
    maximum_presented_candidates: int,
    approval_queue_route_ref: str,
    run_detail_group_ref: str,
    bounded_fanout_presentation_ref: str,
    source_ref: str,
    safe_summary: str,
) -> str:
    payload = json.dumps(
        {
            "contract_ref": PROVIDER_ROUTING_INTELLIGENCE_CONTRACT_REF,
            "request_ref": request_ref,
            "request_fingerprint_ref": request_fingerprint_ref,
            "observation_set_fingerprint_ref": observation_set_fingerprint_ref,
            "strategy": _enum_text(strategy),
            "presented_candidate_refs": presented_candidate_refs,
            "evaluated_candidate_refs": evaluated_candidate_refs,
            "observed_candidate_count": observed_candidate_count,
            "omitted_candidate_count": omitted_candidate_count,
            "recommended_candidate_ref": recommended_candidate_ref,
            "reason_codes": reason_codes,
            "blocker_codes": blocker_codes,
            "maximum_presented_candidates": maximum_presented_candidates,
            "approval_queue_route_ref": approval_queue_route_ref,
            "run_detail_group_ref": run_detail_group_ref,
            "bounded_fanout_presentation_ref": bounded_fanout_presentation_ref,
            "source_ref": source_ref,
            "safe_summary": safe_summary,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        f"provider-routing-proposal-ref:{hashlib.sha256(payload.encode()).hexdigest()}"
    )


def _validate_safe_refs(values: Iterable[str], error_code: str) -> None:
    for value in values:
        if _SAFE_REF_RE.fullmatch(value) is None:
            raise ValueError(error_code)
        if _IPV4_LITERAL_RE.search(value) or _LOCALHOST_RE.search(value):
            raise ValueError(error_code)
        try:
            validate_capability_availability_safe_text(
                value,
                "provider_routing_ref",
            )
        except ValueError as exc:
            raise ValueError(error_code) from exc


def _validate_codes(values: Iterable[str], error_code: str) -> None:
    if any(_SAFE_CODE_RE.fullmatch(value) is None for value in values):
        raise ValueError(error_code)
    if len(list(values)) != len(set(values)):
        raise ValueError(f"{error_code}_DUPLICATE")


def _reject_unsafe(payload: object, error_code: str) -> None:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    if _IPV4_LITERAL_RE.search(serialized) or _LOCALHOST_RE.search(serialized):
        raise ValueError(error_code)
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


def _safe_get(value: object, field_name: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _enum_text(value: object) -> str:
    return str(value.value) if isinstance(value, Enum) else str(value)


def _safe_slug(value: str) -> str:
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", value.lower()) if token]
    return "-".join(tokens[:4]) or "provider"
