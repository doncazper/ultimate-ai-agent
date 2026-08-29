from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capabilities.awareness import (
    CapabilityAwarenessCatalog,
    CapabilityAwarenessEnvelope,
    validate_capability_awareness_catalog,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityHealthStatus,
    PolicyDecisionStatus,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW02_CONTRACT_REF = "contract-ref:taw02:familiarity-assessment:v1"
TAW02_ASSESSOR_REF = "assessor-ref:taw02:table-driven-precedence:v1"


class FamiliarityState(StrEnum):
    familiar_supported = "familiar_supported"
    familiar_input_required = "familiar_input_required"
    familiar_unavailable = "familiar_unavailable"
    familiar_requires_approval = "familiar_requires_approval"
    familiar_authority_blocked = "familiar_authority_blocked"
    capability_evidence_unavailable = "capability_evidence_unavailable"
    ambiguous = "ambiguous"
    novel_unsupported = "novel_unsupported"
    outcome_uncertain = "outcome_uncertain"


class FamiliarityReasonCode(StrEnum):
    outcome_terminal_proof_missing = "outcome_terminal_proof_missing"
    outcome_terminal_proof_inconsistent = "outcome_terminal_proof_inconsistent"
    policy_denied = "policy_denied"
    policy_degraded = "policy_degraded"
    safety_denied = "safety_denied"
    catalog_missing = "catalog_missing"
    catalog_corrupt = "catalog_corrupt"
    catalog_stale = "catalog_stale"
    catalog_over_budget = "catalog_over_budget"
    capability_evidence_substituted = "capability_evidence_substituted"
    multiple_interpretations = "multiple_interpretations"
    multiple_capability_matches = "multiple_capability_matches"
    authority_lane_missing = "authority_lane_missing"
    authority_lane_blocked = "authority_lane_blocked"
    capability_disabled = "capability_disabled"
    capability_unhealthy = "capability_unhealthy"
    capability_stale = "capability_stale"
    capability_absent = "capability_absent"
    required_input_missing = "required_input_missing"
    typed_input_invalid = "typed_input_invalid"
    exact_approval_required = "exact_approval_required"
    exact_capability_supported = "exact_capability_supported"
    no_capability_match = "no_capability_match"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("familiarity evidence must be canonical JSON") from exc


def _fingerprint(payload: object, *, prefix: str) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _json_ready(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _validate_ref(value, field_name)


def _validate_sha256_ref(value: str, field_name: str, prefix: str) -> None:
    expected = f"{prefix}:sha256:"
    suffix = value.removeprefix(expected)
    if (
        not value.startswith(expected)
        or len(suffix) != 64
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise ValueError(f"{field_name} must be an exact {prefix} sha256 ref")


class CapabilityMatchEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw02-capability-match-evidence.v1"] = (
        "uaa-taw02-capability-match-evidence.v1"
    )
    operation_id: str
    envelope_fingerprint_ref: str
    match_kind: Literal["deterministic", "semantic"]
    match_evidence_ref: str
    relevance_basis_points: int = Field(..., ge=0, le=10_000)
    availability_status: Literal[
        "available", "disabled", "unhealthy", "stale", "absent"
    ]
    availability_ref: str
    availability_epoch_ref: str

    @model_validator(mode="after")
    def validate_match(self) -> "CapabilityMatchEvidence":
        for value, field_name in (
            (self.operation_id, "operation_id"),
            (self.match_evidence_ref, "match_evidence_ref"),
            (self.availability_ref, "availability_ref"),
            (self.availability_epoch_ref, "availability_epoch_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_sha256_ref(
            self.envelope_fingerprint_ref,
            "envelope_fingerprint_ref",
            "awareness-envelope-ref:taw01",
        )
        return self


class TerminalOutcomeEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw02-terminal-outcome-evidence.v1"] = (
        "uaa-taw02-terminal-outcome-evidence.v1"
    )
    status: Literal[
        "not_started", "terminal_proven", "terminal_missing", "terminal_inconsistent"
    ] = "not_started"
    execution_attempt_ref: str | None = None
    durable_start_evidence_ref: str | None = None
    terminal_proof_ref: str | None = None
    terminal_status_ref: str | None = None

    @model_validator(mode="after")
    def validate_terminal_evidence(self) -> "TerminalOutcomeEvidence":
        refs = (
            self.execution_attempt_ref,
            self.durable_start_evidence_ref,
            self.terminal_proof_ref,
            self.terminal_status_ref,
        )
        for index, value in enumerate(refs):
            if value is not None:
                _validate_ref(value, f"terminal_evidence_ref_{index}")
        if self.status == "not_started" and any(value is not None for value in refs):
            raise ValueError(
                "not-started terminal evidence cannot include execution refs"
            )
        if self.status != "not_started" and (
            self.execution_attempt_ref is None
            or self.durable_start_evidence_ref is None
        ):
            raise ValueError(
                "started execution evidence requires exact attempt and start refs"
            )
        if self.status == "terminal_proven" and (
            self.terminal_proof_ref is None or self.terminal_status_ref is None
        ):
            raise ValueError(
                "terminal-proven evidence requires exact terminal proof refs"
            )
        if self.status == "terminal_missing" and (
            self.terminal_proof_ref is not None or self.terminal_status_ref is not None
        ):
            raise ValueError("terminal-missing evidence cannot claim terminal proof")
        if self.status == "terminal_inconsistent" and self.terminal_proof_ref is None:
            raise ValueError(
                "terminal-inconsistent evidence requires the conflicting proof ref"
            )
        return self


class FamiliarityAssessmentEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw02-familiarity-assessment-evidence.v1"] = (
        "uaa-taw02-familiarity-assessment-evidence.v1"
    )
    possible_tool_intent: bool
    sentinel_evidence_ref: str
    catalog_evidence_status: Literal[
        "valid", "missing", "corrupt", "stale", "over_budget"
    ]
    expected_catalog_epoch_ref: str
    expected_availability_epoch_ref: str
    expected_policy_snapshot_ref: str
    observed_at_epoch_seconds: int = Field(..., ge=0)
    interpretation_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)
    candidate_matches: tuple[CapabilityMatchEvidence, ...] = Field(
        default=(), max_length=16
    )
    selected_operation_id: str | None = None
    policy_decision_status: PolicyDecisionStatus
    policy_reason_refs: tuple[str, ...] = ()
    safety_decision_status: Literal["allowed", "denied"]
    safety_snapshot_ref: str
    safety_reason_refs: tuple[str, ...] = ()
    validated_input_field_refs: tuple[str, ...] = ()
    missing_input_field_refs: tuple[str, ...] = ()
    invalid_input_field_refs: tuple[str, ...] = ()
    approval_validation_status: Literal["not_applicable", "required", "validated"]
    approval_scope_ref: str | None = None
    approval_operation_ref: str | None = None
    approval_authority_lane_ref: str | None = None
    approval_policy_snapshot_ref: str | None = None
    approval_binding_evidence_ref: str | None = None
    readiness_status: Literal["not_applicable", "ready", "not_ready"]
    terminal_outcome: TerminalOutcomeEvidence = Field(
        default_factory=TerminalOutcomeEvidence
    )
    evaluation_set_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_evidence(self) -> "FamiliarityAssessmentEvidence":
        for value, field_name in (
            (self.sentinel_evidence_ref, "sentinel_evidence_ref"),
            (self.expected_catalog_epoch_ref, "expected_catalog_epoch_ref"),
            (self.expected_availability_epoch_ref, "expected_availability_epoch_ref"),
            (self.expected_policy_snapshot_ref, "expected_policy_snapshot_ref"),
            (self.safety_snapshot_ref, "safety_snapshot_ref"),
        ):
            _validate_ref(value, field_name)
        if self.selected_operation_id is not None:
            _validate_ref(self.selected_operation_id, "selected_operation_id")
        approval_refs = (
            self.approval_scope_ref,
            self.approval_operation_ref,
            self.approval_authority_lane_ref,
            self.approval_policy_snapshot_ref,
            self.approval_binding_evidence_ref,
        )
        for index, value in enumerate(approval_refs):
            if value is not None:
                _validate_ref(value, f"approval_evidence_ref_{index}")
        for values, field_name in (
            (self.interpretation_refs, "interpretation_refs"),
            (self.policy_reason_refs, "policy_reason_refs"),
            (self.safety_reason_refs, "safety_reason_refs"),
            (self.validated_input_field_refs, "validated_input_field_refs"),
            (self.missing_input_field_refs, "missing_input_field_refs"),
            (self.invalid_input_field_refs, "invalid_input_field_refs"),
        ):
            _validate_refs(values, field_name)
        match_ids = tuple(item.operation_id for item in self.candidate_matches)
        if match_ids != tuple(sorted(match_ids)) or len(match_ids) != len(
            set(match_ids)
        ):
            raise ValueError(
                "candidate matches must be unique and sorted by operation ID"
            )
        input_sets = (
            set(self.validated_input_field_refs),
            set(self.missing_input_field_refs),
            set(self.invalid_input_field_refs),
        )
        if any(
            input_sets[i].intersection(input_sets[j])
            for i, j in ((0, 1), (0, 2), (1, 2))
        ):
            raise ValueError("input evidence partitions must be disjoint")
        if self.approval_validation_status == "validated" and any(
            value is None for value in approval_refs
        ):
            raise ValueError("validated approval evidence requires exact binding refs")
        if self.approval_validation_status != "validated" and any(
            value is not None for value in approval_refs
        ):
            raise ValueError(
                "approval binding refs are valid only for validated approval evidence"
            )
        if (
            self.policy_decision_status
            in {
                PolicyDecisionStatus.denied,
                PolicyDecisionStatus.degraded,
            }
            and not self.policy_reason_refs
        ):
            raise ValueError(
                "blocked or degraded policy evidence requires exact reason refs"
            )
        if self.safety_decision_status == "denied" and not self.safety_reason_refs:
            raise ValueError("denied safety evidence requires exact reason refs")
        _validate_sha256_ref(
            self.evaluation_set_fingerprint_ref,
            "evaluation_set_fingerprint_ref",
            "evaluation-set-ref:taw02",
        )
        return self


class FamiliarityDimensions(_FrozenModel):
    terminal_proof_status: Literal[
        "not_started", "terminal_proven", "terminal_missing", "terminal_inconsistent"
    ]
    interpretation_count: int = Field(..., ge=1, le=8)
    capability_match_count: int = Field(..., ge=0, le=16)
    deterministic_match_count: int = Field(..., ge=0, le=16)
    semantic_match_count: int = Field(..., ge=0, le=16)
    capability_identity_status: Literal[
        "exact", "ambiguous", "unsupported", "evidence_unavailable"
    ]
    policy_decision_status: PolicyDecisionStatus
    safety_decision_status: Literal["allowed", "denied"]
    authority_lane_status: Literal[
        "not_applicable", "blocked", "graduated", "mixed", "unknown"
    ]
    availability_status: Literal[
        "available", "disabled", "unhealthy", "stale", "absent", "mixed", "unknown"
    ]
    input_completeness_status: Literal[
        "not_applicable", "complete", "missing", "invalid"
    ]
    approval_validation_status: Literal["not_applicable", "required", "validated"]
    readiness_status: Literal["not_applicable", "ready", "not_ready"]


class FamiliarityAssessment(_FrozenModel):
    schema_version: Literal["uaa-taw02-familiarity-assessment.v1"] = (
        "uaa-taw02-familiarity-assessment.v1"
    )
    contract_ref: Literal["contract-ref:taw02:familiarity-assessment:v1"] = (
        TAW02_CONTRACT_REF
    )
    assessor_ref: Literal["assessor-ref:taw02:table-driven-precedence:v1"] = (
        TAW02_ASSESSOR_REF
    )
    state: FamiliarityState
    reason_codes: tuple[FamiliarityReasonCode, ...] = Field(..., min_length=1)
    dimensions: FamiliarityDimensions
    interpretation_refs: tuple[str, ...]
    candidate_match_evidence: tuple[CapabilityMatchEvidence, ...]
    candidate_operation_refs: tuple[str, ...]
    candidate_envelope_fingerprint_refs: tuple[str, ...]
    candidate_operation_schema_fingerprint_refs: tuple[str, ...]
    selected_operation_ref: str | None
    catalog_fingerprint_ref: str | None
    catalog_epoch_ref: str
    availability_epoch_ref: str
    policy_snapshot_ref: str
    safety_snapshot_ref: str
    policy_reason_refs: tuple[str, ...]
    safety_reason_refs: tuple[str, ...]
    validated_input_field_refs: tuple[str, ...]
    missing_input_field_refs: tuple[str, ...]
    invalid_input_field_refs: tuple[str, ...]
    approval_scope_ref: str | None
    approval_operation_ref: str | None
    approval_authority_lane_ref: str | None
    approval_policy_snapshot_ref: str | None
    approval_binding_evidence_ref: str | None
    execution_attempt_ref: str | None
    durable_start_evidence_ref: str | None
    terminal_proof_ref: str | None
    terminal_status_ref: str | None
    evaluation_set_fingerprint_ref: str
    assessment_fingerprint_ref: str
    raw_operator_content_persisted: Literal[False] = False
    raw_model_content_persisted: Literal[False] = False
    model_call_performed: Literal[False] = False
    provider_call_performed: Literal[False] = False
    proposal_constructed: Literal[False] = False
    approval_requested: Literal[False] = False
    execution_performed: Literal[False] = False
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_assessment(self) -> "FamiliarityAssessment":
        for values, field_name in (
            (self.interpretation_refs, "interpretation_refs"),
            (self.candidate_operation_refs, "candidate_operation_refs"),
            (
                self.candidate_envelope_fingerprint_refs,
                "candidate_envelope_fingerprint_refs",
            ),
            (
                self.candidate_operation_schema_fingerprint_refs,
                "candidate_operation_schema_fingerprint_refs",
            ),
            (self.policy_reason_refs, "policy_reason_refs"),
            (self.safety_reason_refs, "safety_reason_refs"),
            (self.validated_input_field_refs, "validated_input_field_refs"),
            (self.missing_input_field_refs, "missing_input_field_refs"),
            (self.invalid_input_field_refs, "invalid_input_field_refs"),
        ):
            _validate_refs(values, field_name)
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("reason_codes must be unique")
        candidate_count = len(self.candidate_match_evidence)
        if any(
            len(values) != candidate_count
            for values in (
                self.candidate_operation_refs,
                self.candidate_envelope_fingerprint_refs,
                self.candidate_operation_schema_fingerprint_refs,
            )
        ):
            raise ValueError("candidate assessment evidence cardinality drift")
        expected_operation_refs = tuple(
            sorted(item.operation_id for item in self.candidate_match_evidence)
        )
        expected_envelope_refs = tuple(
            sorted(
                item.envelope_fingerprint_ref for item in self.candidate_match_evidence
            )
        )
        if self.candidate_operation_refs != expected_operation_refs:
            raise ValueError("candidate operation binding drift")
        if self.candidate_envelope_fingerprint_refs != expected_envelope_refs:
            raise ValueError("candidate envelope binding drift")
        if self.dimensions.capability_match_count != candidate_count:
            raise ValueError("candidate match-count dimension drift")
        if self.dimensions.deterministic_match_count != sum(
            item.match_kind == "deterministic" for item in self.candidate_match_evidence
        ) or self.dimensions.semantic_match_count != sum(
            item.match_kind == "semantic" for item in self.candidate_match_evidence
        ):
            raise ValueError("candidate relevance dimension drift")
        for value, field_name in (
            (self.catalog_epoch_ref, "catalog_epoch_ref"),
            (self.availability_epoch_ref, "availability_epoch_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.safety_snapshot_ref, "safety_snapshot_ref"),
        ):
            _validate_ref(value, field_name)
        if self.selected_operation_ref is not None:
            _validate_ref(self.selected_operation_ref, "selected_operation_ref")
        for value, field_name in (
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.approval_operation_ref, "approval_operation_ref"),
            (self.approval_authority_lane_ref, "approval_authority_lane_ref"),
            (self.approval_policy_snapshot_ref, "approval_policy_snapshot_ref"),
            (self.approval_binding_evidence_ref, "approval_binding_evidence_ref"),
            (self.execution_attempt_ref, "execution_attempt_ref"),
            (self.durable_start_evidence_ref, "durable_start_evidence_ref"),
            (self.terminal_proof_ref, "terminal_proof_ref"),
            (self.terminal_status_ref, "terminal_status_ref"),
        ):
            if value is not None:
                _validate_ref(value, field_name)
        approval_refs = (
            self.approval_scope_ref,
            self.approval_operation_ref,
            self.approval_authority_lane_ref,
            self.approval_policy_snapshot_ref,
            self.approval_binding_evidence_ref,
        )
        if self.dimensions.approval_validation_status == "validated" and any(
            value is None for value in approval_refs
        ):
            raise ValueError("validated assessment approval binding is incomplete")
        if self.dimensions.approval_validation_status != "validated" and any(
            value is not None for value in approval_refs
        ):
            raise ValueError(
                "unvalidated assessment cannot carry approval binding refs"
            )
        if self.catalog_fingerprint_ref is not None:
            _validate_sha256_ref(
                self.catalog_fingerprint_ref,
                "catalog_fingerprint_ref",
                "awareness-catalog-ref:taw01",
            )
        for value in self.candidate_envelope_fingerprint_refs:
            _validate_sha256_ref(
                value,
                "candidate_envelope_fingerprint_refs",
                "awareness-envelope-ref:taw01",
            )
        for value in self.candidate_operation_schema_fingerprint_refs:
            _validate_sha256_ref(
                value,
                "candidate_operation_schema_fingerprint_refs",
                "operation-schema-ref:taw01",
            )
        _validate_sha256_ref(
            self.evaluation_set_fingerprint_ref,
            "evaluation_set_fingerprint_ref",
            "evaluation-set-ref:taw02",
        )
        _validate_sha256_ref(
            self.assessment_fingerprint_ref,
            "assessment_fingerprint_ref",
            "familiarity-assessment-ref:taw02",
        )
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"assessment_fingerprint_ref"}),
            prefix="familiarity-assessment-ref:taw02",
        )
        if self.assessment_fingerprint_ref != expected:
            raise ValueError("familiarity assessment fingerprint binding drift")
        allowed_reasons = {
            FamiliarityState.outcome_uncertain: {
                FamiliarityReasonCode.outcome_terminal_proof_missing,
                FamiliarityReasonCode.outcome_terminal_proof_inconsistent,
            },
            FamiliarityState.familiar_authority_blocked: {
                FamiliarityReasonCode.policy_denied,
                FamiliarityReasonCode.policy_degraded,
                FamiliarityReasonCode.safety_denied,
                FamiliarityReasonCode.authority_lane_missing,
                FamiliarityReasonCode.authority_lane_blocked,
            },
            FamiliarityState.capability_evidence_unavailable: {
                FamiliarityReasonCode.catalog_missing,
                FamiliarityReasonCode.catalog_corrupt,
                FamiliarityReasonCode.catalog_stale,
                FamiliarityReasonCode.catalog_over_budget,
                FamiliarityReasonCode.capability_evidence_substituted,
            },
            FamiliarityState.ambiguous: {
                FamiliarityReasonCode.multiple_interpretations,
                FamiliarityReasonCode.multiple_capability_matches,
            },
            FamiliarityState.familiar_unavailable: {
                FamiliarityReasonCode.capability_disabled,
                FamiliarityReasonCode.capability_unhealthy,
                FamiliarityReasonCode.capability_stale,
                FamiliarityReasonCode.capability_absent,
            },
            FamiliarityState.familiar_input_required: {
                FamiliarityReasonCode.required_input_missing,
                FamiliarityReasonCode.typed_input_invalid,
            },
            FamiliarityState.familiar_requires_approval: {
                FamiliarityReasonCode.exact_approval_required,
            },
            FamiliarityState.familiar_supported: {
                FamiliarityReasonCode.exact_capability_supported,
            },
            FamiliarityState.novel_unsupported: {
                FamiliarityReasonCode.no_capability_match,
            },
        }
        if not set(self.reason_codes).issubset(allowed_reasons[self.state]):
            raise ValueError("familiarity state and reason-code binding drift")
        if self.state == FamiliarityState.outcome_uncertain and (
            self.dimensions.terminal_proof_status
            not in {"terminal_missing", "terminal_inconsistent"}
        ):
            raise ValueError("outcome-uncertain state lacks exact terminal evidence")
        if (
            self.state == FamiliarityState.capability_evidence_unavailable
            and self.dimensions.capability_identity_status != "evidence_unavailable"
        ):
            raise ValueError("capability-evidence-unavailable dimension drift")
        if self.state == FamiliarityState.ambiguous and (
            self.dimensions.capability_identity_status != "ambiguous"
        ):
            raise ValueError("ambiguous familiarity dimension drift")
        if self.state == FamiliarityState.novel_unsupported and (
            self.dimensions.capability_identity_status != "unsupported"
        ):
            raise ValueError("unsupported familiarity dimension drift")
        exact_states = {
            FamiliarityState.familiar_supported,
            FamiliarityState.familiar_input_required,
            FamiliarityState.familiar_unavailable,
            FamiliarityState.familiar_requires_approval,
        }
        if self.state in exact_states and (
            self.dimensions.capability_identity_status != "exact"
        ):
            raise ValueError("familiar state lacks one exact capability identity")
        if self.state == FamiliarityState.familiar_supported and (
            self.dimensions.availability_status != "available"
            or self.dimensions.input_completeness_status != "complete"
            or self.dimensions.readiness_status != "ready"
            or self.dimensions.approval_validation_status
            not in {"not_applicable", "validated"}
        ):
            raise ValueError("supported familiarity dimensions are inconsistent")
        return self


def _aggregate(values: list[str], *, empty: str, mixed: str) -> str:
    unique = set(values)
    if not unique:
        return empty
    if len(unique) == 1:
        return unique.pop()
    return mixed


def _input_status(
    evidence: FamiliarityAssessmentEvidence,
    envelope: CapabilityAwarenessEnvelope | None,
) -> Literal["not_applicable", "complete", "missing", "invalid"]:
    supplied = (
        set(evidence.validated_input_field_refs)
        | set(evidence.missing_input_field_refs)
        | set(evidence.invalid_input_field_refs)
    )
    if envelope is None:
        if supplied:
            raise ValueError("input evidence requires one exact capability identity")
        return "not_applicable"
    known = set(envelope.required_input_field_refs) | set(
        envelope.optional_input_field_refs
    )
    if not supplied.issubset(known):
        raise ValueError("input evidence contains substituted field refs")
    required = set(envelope.required_input_field_refs)
    classified_required = supplied.intersection(required)
    if classified_required != required:
        raise ValueError("every required input field needs explicit typed evidence")
    if evidence.invalid_input_field_refs:
        return "invalid"
    if evidence.missing_input_field_refs:
        return "missing"
    return "complete"


def _catalog_failure_reason(status: str) -> FamiliarityReasonCode:
    return {
        "missing": FamiliarityReasonCode.catalog_missing,
        "corrupt": FamiliarityReasonCode.catalog_corrupt,
        "stale": FamiliarityReasonCode.catalog_stale,
        "over_budget": FamiliarityReasonCode.catalog_over_budget,
    }[status]


def _assessment_payload(
    *,
    evidence: FamiliarityAssessmentEvidence,
    state: FamiliarityState,
    reason_codes: tuple[FamiliarityReasonCode, ...],
    catalog: CapabilityAwarenessCatalog | None,
    envelopes: tuple[CapabilityAwarenessEnvelope, ...],
    dimensions: FamiliarityDimensions,
) -> dict[str, Any]:
    match_by_operation = {
        item.operation_id: item for item in evidence.candidate_matches
    }
    trusted_identity = dimensions.capability_identity_status != "evidence_unavailable"
    payload: dict[str, Any] = {
        "schema_version": "uaa-taw02-familiarity-assessment.v1",
        "contract_ref": TAW02_CONTRACT_REF,
        "assessor_ref": TAW02_ASSESSOR_REF,
        "state": state,
        "reason_codes": reason_codes,
        "dimensions": dimensions,
        "interpretation_refs": evidence.interpretation_refs,
        "candidate_match_evidence": tuple(
            match_by_operation[item.operation_id] for item in envelopes
        ),
        "candidate_operation_refs": tuple(
            sorted(item.operation_id for item in envelopes)
        ),
        "candidate_envelope_fingerprint_refs": tuple(
            sorted(item.envelope_fingerprint_ref for item in envelopes)
        ),
        "candidate_operation_schema_fingerprint_refs": tuple(
            sorted(item.operation_schema_fingerprint_ref for item in envelopes)
        ),
        "selected_operation_ref": (
            evidence.selected_operation_id if len(envelopes) == 1 else None
        ),
        "catalog_fingerprint_ref": (
            catalog.catalog_fingerprint_ref if catalog is not None else None
        ),
        "catalog_epoch_ref": evidence.expected_catalog_epoch_ref,
        "availability_epoch_ref": evidence.expected_availability_epoch_ref,
        "policy_snapshot_ref": evidence.expected_policy_snapshot_ref,
        "safety_snapshot_ref": evidence.safety_snapshot_ref,
        "policy_reason_refs": evidence.policy_reason_refs,
        "safety_reason_refs": evidence.safety_reason_refs,
        "validated_input_field_refs": (
            evidence.validated_input_field_refs if trusted_identity else ()
        ),
        "missing_input_field_refs": (
            evidence.missing_input_field_refs if trusted_identity else ()
        ),
        "invalid_input_field_refs": (
            evidence.invalid_input_field_refs if trusted_identity else ()
        ),
        "approval_scope_ref": evidence.approval_scope_ref if trusted_identity else None,
        "approval_operation_ref": (
            evidence.approval_operation_ref if trusted_identity else None
        ),
        "approval_authority_lane_ref": (
            evidence.approval_authority_lane_ref if trusted_identity else None
        ),
        "approval_policy_snapshot_ref": (
            evidence.approval_policy_snapshot_ref if trusted_identity else None
        ),
        "approval_binding_evidence_ref": (
            evidence.approval_binding_evidence_ref if trusted_identity else None
        ),
        "execution_attempt_ref": evidence.terminal_outcome.execution_attempt_ref,
        "durable_start_evidence_ref": (
            evidence.terminal_outcome.durable_start_evidence_ref
        ),
        "terminal_proof_ref": evidence.terminal_outcome.terminal_proof_ref,
        "terminal_status_ref": evidence.terminal_outcome.terminal_status_ref,
        "evaluation_set_fingerprint_ref": evidence.evaluation_set_fingerprint_ref,
        "raw_operator_content_persisted": False,
        "raw_model_content_persisted": False,
        "model_call_performed": False,
        "provider_call_performed": False,
        "proposal_constructed": False,
        "approval_requested": False,
        "execution_performed": False,
        "authority_granted": False,
    }
    fingerprint_payload = _json_ready(payload)
    payload["assessment_fingerprint_ref"] = _fingerprint(
        fingerprint_payload, prefix="familiarity-assessment-ref:taw02"
    )
    return payload


def assess_familiarity(
    evidence: FamiliarityAssessmentEvidence | Mapping[str, Any],
    *,
    catalog: CapabilityAwarenessCatalog | Mapping[str, Any] | None,
) -> FamiliarityAssessment:
    """Derive one canonical familiarity state without proposing or executing work."""

    evidence_payload = (
        evidence.model_dump(mode="python")
        if isinstance(evidence, FamiliarityAssessmentEvidence)
        else dict(evidence)
    )
    validated_evidence = FamiliarityAssessmentEvidence.model_validate(evidence_payload)

    validated_catalog: CapabilityAwarenessCatalog | None = None
    catalog_failure: FamiliarityReasonCode | None = None
    if validated_evidence.catalog_evidence_status == "valid":
        if catalog is None:
            catalog_failure = FamiliarityReasonCode.catalog_missing
        else:
            try:
                validated_catalog = validate_capability_awareness_catalog(
                    catalog,
                    expected_catalog_epoch_ref=validated_evidence.expected_catalog_epoch_ref,
                    expected_availability_epoch_ref=validated_evidence.expected_availability_epoch_ref,
                    expected_policy_snapshot_ref=validated_evidence.expected_policy_snapshot_ref,
                    observed_at_epoch_seconds=validated_evidence.observed_at_epoch_seconds,
                )
            except ValueError as exc:
                catalog_failure = (
                    FamiliarityReasonCode.catalog_stale
                    if "stale" in str(exc)
                    else FamiliarityReasonCode.catalog_corrupt
                )
    else:
        if catalog is not None:
            raise ValueError(
                "unavailable catalog evidence cannot include a trusted catalog"
            )
        catalog_failure = _catalog_failure_reason(
            validated_evidence.catalog_evidence_status
        )

    match_by_operation = {
        item.operation_id: item for item in validated_evidence.candidate_matches
    }
    envelopes: tuple[CapabilityAwarenessEnvelope, ...] = ()
    substitution_detected = False
    if validated_catalog is not None:
        envelope_by_operation = {
            item.operation_id: item for item in validated_catalog.envelopes
        }
        selected: list[CapabilityAwarenessEnvelope] = []
        for operation_id, match in match_by_operation.items():
            envelope = envelope_by_operation.get(operation_id)
            if (
                envelope is None
                or envelope.envelope_fingerprint_ref != match.envelope_fingerprint_ref
                or envelope.availability_ref != match.availability_ref
                or envelope.availability_epoch_ref != match.availability_epoch_ref
            ):
                substitution_detected = True
                break
            selected.append(envelope)
        envelopes = tuple(sorted(selected, key=lambda item: item.operation_id))
    elif validated_evidence.candidate_matches:
        substitution_detected = True

    if catalog_failure is not None or substitution_detected:
        envelopes = ()

    candidate_count = len(validated_evidence.candidate_matches)
    exact_envelope: CapabilityAwarenessEnvelope | None = None
    if candidate_count == 1 and not substitution_detected:
        exact_envelope = envelopes[0]
        if validated_evidence.selected_operation_id != exact_envelope.operation_id:
            substitution_detected = True
            exact_envelope = None
    elif validated_evidence.selected_operation_id is not None:
        substitution_detected = True

    terminal_status = validated_evidence.terminal_outcome.status
    authority_values = [item.authority_lane_status for item in envelopes]
    availability_values = [
        match_by_operation[item.operation_id].availability_status for item in envelopes
    ]
    identity_status: Literal[
        "exact", "ambiguous", "unsupported", "evidence_unavailable"
    ]
    if catalog_failure is not None or substitution_detected:
        identity_status = "evidence_unavailable"
    elif len(validated_evidence.interpretation_refs) > 1 or candidate_count > 1:
        identity_status = "ambiguous"
    elif candidate_count == 1:
        identity_status = "exact"
    else:
        identity_status = "unsupported"

    if exact_envelope is not None:
        availability_status = availability_values[0]
        if (
            availability_status == "available"
            and exact_envelope.health_status != CapabilityHealthStatus.healthy
        ) or (
            availability_status != "available"
            and exact_envelope.health_status == CapabilityHealthStatus.healthy
        ):
            raise ValueError(
                "selected capability availability contradicts its awareness envelope"
            )
        if validated_evidence.policy_decision_status not in {
            PolicyDecisionStatus.denied,
            PolicyDecisionStatus.degraded,
        } and (
            exact_envelope.policy_decision_status
            != validated_evidence.policy_decision_status
        ):
            raise ValueError("selected capability policy evidence is inconsistent")
        valid_approval_statuses = (
            {"required", "validated"}
            if exact_envelope.approval_class == "exact_approval_required"
            else {"not_applicable"}
        )
        if validated_evidence.approval_validation_status not in valid_approval_statuses:
            raise ValueError("selected capability approval evidence is inconsistent")
        if validated_evidence.approval_validation_status == "validated" and (
            validated_evidence.approval_operation_ref != exact_envelope.operation_id
            or validated_evidence.approval_authority_lane_ref
            != exact_envelope.authority_lane_ref
            or validated_evidence.approval_policy_snapshot_ref
            != exact_envelope.policy_snapshot_ref
        ):
            raise ValueError("validated approval evidence is scope-substituted")
    elif identity_status in {"ambiguous", "unsupported"} and (
        validated_evidence.approval_validation_status != "not_applicable"
        or validated_evidence.readiness_status != "not_applicable"
    ):
        raise ValueError(
            "non-exact capability evidence cannot claim approval or readiness"
        )
    if (
        validated_evidence.policy_decision_status
        == PolicyDecisionStatus.approval_required
        and exact_envelope is None
        and identity_status != "evidence_unavailable"
    ):
        raise ValueError(
            "approval-required policy evidence needs exact capability identity"
        )

    input_status = (
        "not_applicable"
        if identity_status == "evidence_unavailable"
        else _input_status(validated_evidence, exact_envelope)
    )
    dimensions = FamiliarityDimensions(
        terminal_proof_status=terminal_status,
        interpretation_count=len(validated_evidence.interpretation_refs),
        capability_match_count=len(envelopes),
        deterministic_match_count=sum(
            match_by_operation[item.operation_id].match_kind == "deterministic"
            for item in envelopes
        ),
        semantic_match_count=sum(
            match_by_operation[item.operation_id].match_kind == "semantic"
            for item in envelopes
        ),
        capability_identity_status=identity_status,
        policy_decision_status=validated_evidence.policy_decision_status,
        safety_decision_status=validated_evidence.safety_decision_status,
        authority_lane_status=_aggregate(
            authority_values, empty="unknown", mixed="mixed"
        ),
        availability_status=_aggregate(
            availability_values, empty="unknown", mixed="mixed"
        ),
        input_completeness_status=input_status,
        approval_validation_status=(
            "not_applicable"
            if identity_status == "evidence_unavailable"
            else validated_evidence.approval_validation_status
        ),
        readiness_status=(
            "not_applicable"
            if identity_status == "evidence_unavailable"
            else validated_evidence.readiness_status
        ),
    )

    state: FamiliarityState
    reasons: tuple[FamiliarityReasonCode, ...]
    if terminal_status in {"terminal_missing", "terminal_inconsistent"}:
        state = FamiliarityState.outcome_uncertain
        reasons = (
            FamiliarityReasonCode.outcome_terminal_proof_missing
            if terminal_status == "terminal_missing"
            else FamiliarityReasonCode.outcome_terminal_proof_inconsistent,
        )
    elif validated_evidence.safety_decision_status == "denied":
        state = FamiliarityState.familiar_authority_blocked
        reasons = (FamiliarityReasonCode.safety_denied,)
    elif validated_evidence.policy_decision_status in {
        PolicyDecisionStatus.denied,
        PolicyDecisionStatus.degraded,
    }:
        state = FamiliarityState.familiar_authority_blocked
        reasons = (
            FamiliarityReasonCode.policy_denied
            if validated_evidence.policy_decision_status == PolicyDecisionStatus.denied
            else FamiliarityReasonCode.policy_degraded,
        )
    elif catalog_failure is not None or substitution_detected:
        if not validated_evidence.possible_tool_intent:
            raise ValueError(
                "catalog evidence failure without possible tool intent belongs to direct-chat fallback"
            )
        state = FamiliarityState.capability_evidence_unavailable
        reasons = (
            catalog_failure
            if catalog_failure is not None
            else FamiliarityReasonCode.capability_evidence_substituted,
        )
    elif len(validated_evidence.interpretation_refs) > 1 or candidate_count > 1:
        state = FamiliarityState.ambiguous
        reasons = tuple(
            reason
            for predicate, reason in (
                (
                    len(validated_evidence.interpretation_refs) > 1,
                    FamiliarityReasonCode.multiple_interpretations,
                ),
                (
                    candidate_count > 1,
                    FamiliarityReasonCode.multiple_capability_matches,
                ),
            )
            if predicate
        )
    elif exact_envelope is not None and exact_envelope.authority_lane_status in {
        "blocked",
    }:
        state = FamiliarityState.familiar_authority_blocked
        reasons = (FamiliarityReasonCode.authority_lane_blocked,)
    elif (
        exact_envelope is not None
        and exact_envelope.approval_class == "exact_approval_required"
        and exact_envelope.authority_lane_status != "graduated"
    ):
        state = FamiliarityState.familiar_authority_blocked
        reasons = (FamiliarityReasonCode.authority_lane_missing,)
    elif exact_envelope is not None and availability_values[0] != "available":
        if validated_evidence.readiness_status == "ready":
            raise ValueError("unavailable capability evidence cannot be decision-ready")
        state = FamiliarityState.familiar_unavailable
        reasons = (
            {
                "disabled": FamiliarityReasonCode.capability_disabled,
                "unhealthy": FamiliarityReasonCode.capability_unhealthy,
                "stale": FamiliarityReasonCode.capability_stale,
                "absent": FamiliarityReasonCode.capability_absent,
            }[availability_values[0]],
        )
    elif input_status in {"missing", "invalid"}:
        if validated_evidence.readiness_status == "ready":
            raise ValueError("incomplete input evidence cannot be decision-ready")
        state = FamiliarityState.familiar_input_required
        reasons = tuple(
            reason
            for predicate, reason in (
                (
                    bool(validated_evidence.missing_input_field_refs),
                    FamiliarityReasonCode.required_input_missing,
                ),
                (
                    bool(validated_evidence.invalid_input_field_refs),
                    FamiliarityReasonCode.typed_input_invalid,
                ),
            )
            if predicate
        )
    elif exact_envelope is not None and (
        exact_envelope.approval_class == "exact_approval_required"
        and validated_evidence.approval_validation_status == "required"
    ):
        if validated_evidence.readiness_status != "ready":
            raise ValueError("approval-required evidence must be decision-ready")
        state = FamiliarityState.familiar_requires_approval
        reasons = (FamiliarityReasonCode.exact_approval_required,)
    elif exact_envelope is not None:
        if validated_evidence.readiness_status != "ready":
            raise ValueError("exact capability evidence is not decision-ready")
        state = FamiliarityState.familiar_supported
        reasons = (FamiliarityReasonCode.exact_capability_supported,)
    else:
        if not validated_evidence.possible_tool_intent:
            raise ValueError("unsupported assessment requires possible tool intent")
        if any(
            (
                validated_evidence.validated_input_field_refs,
                validated_evidence.missing_input_field_refs,
                validated_evidence.invalid_input_field_refs,
            )
        ):
            raise ValueError(
                "unsupported assessment cannot retain unbound input evidence"
            )
        if validated_evidence.approval_validation_status != "not_applicable":
            raise ValueError("unsupported assessment cannot retain approval evidence")
        if validated_evidence.readiness_status != "not_applicable":
            raise ValueError("unsupported assessment cannot claim readiness")
        state = FamiliarityState.novel_unsupported
        reasons = (FamiliarityReasonCode.no_capability_match,)

    payload = _assessment_payload(
        evidence=validated_evidence,
        state=state,
        reason_codes=reasons,
        catalog=validated_catalog,
        envelopes=envelopes,
        dimensions=dimensions,
    )
    return FamiliarityAssessment.model_validate(payload)


__all__ = [
    "CapabilityMatchEvidence",
    "FamiliarityAssessment",
    "FamiliarityAssessmentEvidence",
    "FamiliarityDimensions",
    "FamiliarityReasonCode",
    "FamiliarityState",
    "TAW02_ASSESSOR_REF",
    "TAW02_CONTRACT_REF",
    "TerminalOutcomeEvidence",
    "assess_familiarity",
]
