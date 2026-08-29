from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW05_CONTRACT_REF = "contract-ref:taw05:outcome-evidence:v1"
TAW05_PROJECTOR_REF = "projector-ref:taw05:recomputable-receipts:v1"
TAW05_MAX_OBSERVATIONS = 4_096


class TerminalReceiptStatus(StrEnum):
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"
    rolled_back = "rolled_back"


class OutcomeObservationClass(StrEnum):
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"
    rolled_back = "rolled_back"
    still_live = "still_live"
    unresolved_overdue = "unresolved_overdue"


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
        raise ValueError("TAW-05 evidence must be canonical JSON") from exc


def _fingerprint(payload: object, *, prefix: str) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


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


T = TypeVar("T")


def _bounded_tuple(
    values: Iterable[T],
    field_name: str,
    *,
    max_items: int = TAW05_MAX_OBSERVATIONS,
) -> tuple[T, ...]:
    bounded: list[T] = []
    for value in values:
        if len(bounded) >= max_items:
            raise ValueError(f"{field_name} exceeds the TAW-05 bound of {max_items}")
        bounded.append(value)
    return tuple(bounded)


class OutcomeEvaluationPolicy(_FrozenModel):
    schema_version: Literal["uaa-taw05-outcome-evaluation-policy.v1"] = (
        "uaa-taw05-outcome-evaluation-policy.v1"
    )
    policy_snapshot_ref: str
    evaluator_revision_ref: str
    reviewed_completion_sla_ref: str
    reviewed_completion_sla_seconds: int = Field(..., ge=1)
    repository_hard_max_window_seconds: int = Field(..., ge=1)
    clock_source_ref: str
    policy_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_policy(self) -> "OutcomeEvaluationPolicy":
        for value, field_name in (
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.evaluator_revision_ref, "evaluator_revision_ref"),
            (self.reviewed_completion_sla_ref, "reviewed_completion_sla_ref"),
            (self.clock_source_ref, "clock_source_ref"),
        ):
            _validate_ref(value, field_name)
        if (
            self.reviewed_completion_sla_seconds
            > self.repository_hard_max_window_seconds
        ):
            raise ValueError("reviewed completion SLA exceeds repository hard maximum")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"policy_fingerprint_ref"}),
            prefix="outcome-policy-ref:taw05",
        )
        if self.policy_fingerprint_ref != expected:
            raise ValueError("outcome evaluation policy fingerprint binding drift")
        return self


class TerminalStatusBinding(_FrozenModel):
    status: TerminalReceiptStatus
    terminal_status_ref: str

    @model_validator(mode="after")
    def validate_binding(self) -> "TerminalStatusBinding":
        _validate_ref(self.terminal_status_ref, "terminal_status_ref")
        return self


class CapabilityOutcomeContract(_FrozenModel):
    schema_version: Literal["uaa-taw05-capability-outcome-contract.v1"] = (
        "uaa-taw05-capability-outcome-contract.v1"
    )
    operation_id: str
    capability_contract_version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    operation_schema_fingerprint_ref: str
    policy_snapshot_ref: str
    evaluator_revision_ref: str
    reviewed_completion_sla_ref: str
    completion_window_seconds: int = Field(..., ge=1)
    clock_source_ref: str
    environment_class_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    terminal_status_bindings: tuple[TerminalStatusBinding, ...] = Field(
        ..., min_length=4, max_length=4
    )
    contract_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_contract(self) -> "CapabilityOutcomeContract":
        for value, field_name in (
            (self.operation_id, "operation_id"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.evaluator_revision_ref, "evaluator_revision_ref"),
            (self.reviewed_completion_sla_ref, "reviewed_completion_sla_ref"),
            (self.clock_source_ref, "clock_source_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_sha256_ref(
            self.operation_schema_fingerprint_ref,
            "operation_schema_fingerprint_ref",
            "operation-schema-ref:taw01",
        )
        _validate_refs(self.environment_class_refs, "environment_class_refs")
        statuses = tuple(item.status for item in self.terminal_status_bindings)
        if statuses != tuple(
            sorted(TerminalReceiptStatus, key=lambda item: item.value)
        ):
            raise ValueError("terminal status bindings must cover each status in order")
        refs = tuple(item.terminal_status_ref for item in self.terminal_status_bindings)
        if len(refs) != len(set(refs)):
            raise ValueError("terminal status refs must be unique")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"contract_fingerprint_ref"}),
            prefix="outcome-contract-ref:taw05",
        )
        if self.contract_fingerprint_ref != expected:
            raise ValueError("capability outcome contract fingerprint binding drift")
        return self


class AttemptStartEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw05-attempt-start-evidence.v1"] = (
        "uaa-taw05-attempt-start-evidence.v1"
    )
    operation_id: str
    execution_attempt_ref: str
    durable_start_evidence_ref: str
    contract_fingerprint_ref: str
    operation_schema_fingerprint_ref: str
    policy_snapshot_ref: str
    evaluator_revision_ref: str
    environment_class_ref: str
    started_at_epoch_seconds: int = Field(..., ge=0)
    durable_start_recorded: Literal[True] = True
    content_redacted: Literal[True] = True
    raw_content_included: Literal[False] = False
    start_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_start(self) -> "AttemptStartEvidence":
        for value, field_name in (
            (self.operation_id, "operation_id"),
            (self.execution_attempt_ref, "execution_attempt_ref"),
            (self.durable_start_evidence_ref, "durable_start_evidence_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.evaluator_revision_ref, "evaluator_revision_ref"),
            (self.environment_class_ref, "environment_class_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_sha256_ref(
            self.contract_fingerprint_ref,
            "contract_fingerprint_ref",
            "outcome-contract-ref:taw05",
        )
        _validate_sha256_ref(
            self.operation_schema_fingerprint_ref,
            "operation_schema_fingerprint_ref",
            "operation-schema-ref:taw01",
        )
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"start_fingerprint_ref"}),
            prefix="attempt-start-ref:taw05",
        )
        if self.start_fingerprint_ref != expected:
            raise ValueError("attempt start fingerprint binding drift")
        return self


class TerminalReceiptEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw05-terminal-receipt-evidence.v1"] = (
        "uaa-taw05-terminal-receipt-evidence.v1"
    )
    operation_id: str
    execution_attempt_ref: str
    durable_start_evidence_ref: str
    start_fingerprint_ref: str
    terminal_receipt_ref: str
    terminal_status: TerminalReceiptStatus
    terminal_status_ref: str
    contract_fingerprint_ref: str
    operation_schema_fingerprint_ref: str
    policy_snapshot_ref: str
    evaluator_revision_ref: str
    environment_class_ref: str
    terminal_at_epoch_seconds: int = Field(..., ge=0)
    terminal_evidence_refs: tuple[str, ...] = Field(default=(), max_length=16)
    immutable_receipt: Literal[True] = True
    durable_receipt: Literal[True] = True
    content_redacted: Literal[True] = True
    raw_content_included: Literal[False] = False
    receipt_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "TerminalReceiptEvidence":
        for value, field_name in (
            (self.operation_id, "operation_id"),
            (self.execution_attempt_ref, "execution_attempt_ref"),
            (self.durable_start_evidence_ref, "durable_start_evidence_ref"),
            (self.terminal_receipt_ref, "terminal_receipt_ref"),
            (self.terminal_status_ref, "terminal_status_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.evaluator_revision_ref, "evaluator_revision_ref"),
            (self.environment_class_ref, "environment_class_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_sha256_ref(
            self.start_fingerprint_ref,
            "start_fingerprint_ref",
            "attempt-start-ref:taw05",
        )
        _validate_sha256_ref(
            self.contract_fingerprint_ref,
            "contract_fingerprint_ref",
            "outcome-contract-ref:taw05",
        )
        _validate_sha256_ref(
            self.operation_schema_fingerprint_ref,
            "operation_schema_fingerprint_ref",
            "operation-schema-ref:taw01",
        )
        _validate_refs(self.terminal_evidence_refs, "terminal_evidence_refs")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"receipt_fingerprint_ref"}),
            prefix="terminal-receipt-ref:taw05",
        )
        if self.receipt_fingerprint_ref != expected:
            raise ValueError("terminal receipt fingerprint binding drift")
        return self


class OutcomePriorEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw05-outcome-prior-evidence.v1"] = (
        "uaa-taw05-outcome-prior-evidence.v1"
    )
    prior_evidence_ref: str
    projection_fingerprint_ref: str
    contract_fingerprint_ref: str
    operation_schema_fingerprint_ref: str
    policy_snapshot_ref: str
    evaluator_revision_ref: str

    @model_validator(mode="after")
    def validate_prior(self) -> "OutcomePriorEvidence":
        for value, field_name in (
            (self.prior_evidence_ref, "prior_evidence_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.evaluator_revision_ref, "evaluator_revision_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_sha256_ref(
            self.projection_fingerprint_ref,
            "projection_fingerprint_ref",
            "outcome-projection-ref:taw05",
        )
        _validate_sha256_ref(
            self.contract_fingerprint_ref,
            "contract_fingerprint_ref",
            "outcome-contract-ref:taw05",
        )
        _validate_sha256_ref(
            self.operation_schema_fingerprint_ref,
            "operation_schema_fingerprint_ref",
            "operation-schema-ref:taw01",
        )
        return self


class AttemptOutcomeObservation(_FrozenModel):
    execution_attempt_ref: str
    durable_start_evidence_ref: str
    start_fingerprint_ref: str
    terminal_receipt_ref: str | None
    receipt_fingerprint_ref: str | None
    outcome_class: OutcomeObservationClass
    outcome_posture: Literal["terminal_proven", "outcome_uncertain"]
    included_in_outcome_rate_denominator: bool
    counts_as_success: bool

    @model_validator(mode="after")
    def validate_observation(self) -> "AttemptOutcomeObservation":
        _validate_ref(self.execution_attempt_ref, "execution_attempt_ref")
        _validate_ref(self.durable_start_evidence_ref, "durable_start_evidence_ref")
        _validate_sha256_ref(
            self.start_fingerprint_ref,
            "start_fingerprint_ref",
            "attempt-start-ref:taw05",
        )
        terminal = self.outcome_class in {
            OutcomeObservationClass.succeeded,
            OutcomeObservationClass.failed,
            OutcomeObservationClass.canceled,
            OutcomeObservationClass.rolled_back,
        }
        if terminal:
            if (
                self.terminal_receipt_ref is None
                or self.receipt_fingerprint_ref is None
                or self.outcome_posture != "terminal_proven"
                or not self.included_in_outcome_rate_denominator
            ):
                raise ValueError("terminal observations require exact receipt evidence")
        elif (
            self.terminal_receipt_ref is not None
            or self.receipt_fingerprint_ref is not None
        ):
            raise ValueError("non-terminal observations cannot claim receipt evidence")
        elif self.outcome_posture != "outcome_uncertain":
            raise ValueError("non-terminal observations must remain outcome-uncertain")
        if self.terminal_receipt_ref is not None:
            _validate_ref(self.terminal_receipt_ref, "terminal_receipt_ref")
        if self.receipt_fingerprint_ref is not None:
            _validate_sha256_ref(
                self.receipt_fingerprint_ref,
                "receipt_fingerprint_ref",
                "terminal-receipt-ref:taw05",
            )
        if self.outcome_class == OutcomeObservationClass.still_live:
            if self.included_in_outcome_rate_denominator:
                raise ValueError("still-live attempts are excluded from outcome rates")
        elif not self.included_in_outcome_rate_denominator:
            raise ValueError(
                "terminal and overdue outcomes must remain in denominators"
            )
        if self.counts_as_success != (
            self.outcome_class == OutcomeObservationClass.succeeded
        ):
            raise ValueError("success accounting does not match outcome class")
        return self


class CapabilityOutcomeProjection(_FrozenModel):
    schema_version: Literal["uaa-taw05-capability-outcome-projection.v1"] = (
        "uaa-taw05-capability-outcome-projection.v1"
    )
    contract_ref: Literal["contract-ref:taw05:outcome-evidence:v1"] = TAW05_CONTRACT_REF
    projector_ref: Literal["projector-ref:taw05:recomputable-receipts:v1"] = (
        TAW05_PROJECTOR_REF
    )
    operation_id: str
    contract_fingerprint_ref: str
    policy_fingerprint_ref: str
    as_of_epoch_seconds: int = Field(..., ge=0)
    completion_window_seconds: int = Field(..., ge=1)
    clock_source_ref: str
    attempt_inventory_count: int = Field(..., ge=0)
    still_live_count: int = Field(..., ge=0)
    unresolved_overdue_count: int = Field(..., ge=0)
    terminal_count: int = Field(..., ge=0)
    succeeded_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    canceled_count: int = Field(..., ge=0)
    rolled_back_count: int = Field(..., ge=0)
    non_success_count: int = Field(..., ge=0)
    health_rate_denominator: int = Field(..., ge=0)
    reliability_rate_denominator: int = Field(..., ge=0)
    familiarity_rate_denominator: int = Field(..., ge=0)
    success_basis_points: int | None = Field(default=None, ge=0, le=10_000)
    prior_status: Literal["absent", "current_non_authoritative", "invalidated_stale"]
    prior_reason_refs: tuple[str, ...]
    observations: tuple[AttemptOutcomeObservation, ...] = Field(
        ..., max_length=TAW05_MAX_OBSERVATIONS
    )
    non_authoritative: Literal[True] = True
    durable_statistics_store_mutated: Literal[False] = False
    receipt_arrival_handler_registered: Literal[False] = False
    online_training_performed: Literal[False] = False
    automatic_policy_or_alias_promotion: Literal[False] = False
    provider_call_performed: Literal[False] = False
    model_call_count: Literal[0] = 0
    second_ordinary_chat_model_call_count: Literal[0] = 0
    runtime_execution_performed: Literal[False] = False
    connector_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False
    public_claim_made: Literal[False] = False
    authority_granted: Literal[False] = False
    production_authority_granted: Literal[False] = False
    projection_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_projection(self) -> "CapabilityOutcomeProjection":
        _validate_ref(self.operation_id, "operation_id")
        _validate_ref(self.clock_source_ref, "clock_source_ref")
        _validate_sha256_ref(
            self.contract_fingerprint_ref,
            "contract_fingerprint_ref",
            "outcome-contract-ref:taw05",
        )
        _validate_sha256_ref(
            self.policy_fingerprint_ref,
            "policy_fingerprint_ref",
            "outcome-policy-ref:taw05",
        )
        _validate_refs(self.prior_reason_refs, "prior_reason_refs")
        if self.attempt_inventory_count != len(self.observations):
            raise ValueError("attempt inventory count must equal observation census")
        observation_counts = {
            outcome_class: sum(
                item.outcome_class == outcome_class for item in self.observations
            )
            for outcome_class in OutcomeObservationClass
        }
        claimed_counts = {
            OutcomeObservationClass.succeeded: self.succeeded_count,
            OutcomeObservationClass.failed: self.failed_count,
            OutcomeObservationClass.canceled: self.canceled_count,
            OutcomeObservationClass.rolled_back: self.rolled_back_count,
            OutcomeObservationClass.still_live: self.still_live_count,
            OutcomeObservationClass.unresolved_overdue: (self.unresolved_overdue_count),
        }
        if observation_counts != claimed_counts:
            raise ValueError("outcome counts must be recomputed from observations")
        if (
            self.attempt_inventory_count
            != self.still_live_count
            + self.unresolved_overdue_count
            + self.terminal_count
        ):
            raise ValueError("attempt inventory population does not reconcile")
        if self.terminal_count != (
            self.succeeded_count
            + self.failed_count
            + self.canceled_count
            + self.rolled_back_count
        ):
            raise ValueError("terminal outcome population does not reconcile")
        denominator = self.terminal_count + self.unresolved_overdue_count
        if any(
            value != denominator
            for value in (
                self.health_rate_denominator,
                self.reliability_rate_denominator,
                self.familiarity_rate_denominator,
            )
        ):
            raise ValueError("outcome rate denominators must retain overdue attempts")
        if self.non_success_count != denominator - self.succeeded_count:
            raise ValueError("non-success count does not reconcile")
        expected_basis_points = (
            None if denominator == 0 else self.succeeded_count * 10_000 // denominator
        )
        if self.success_basis_points != expected_basis_points:
            raise ValueError("success basis points do not match the census")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"projection_fingerprint_ref"}),
            prefix="outcome-projection-ref:taw05",
        )
        if self.projection_fingerprint_ref != expected:
            raise ValueError("outcome projection fingerprint binding drift")
        return self


class OperatorCorrectionEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw05-operator-correction-evidence.v1"] = (
        "uaa-taw05-operator-correction-evidence.v1"
    )
    correction_ref: str
    source_revision_ref: str
    execution_attempt_ref: str | None = None
    transformation_kind: Literal["untransformed", "synthetic", "fully_redacted"]
    transformed_fixture_ref: str | None = None
    review_status: Literal["pending", "accepted", "rejected"]
    independent_review_ref: str | None = None
    content_safety_status: Literal["not_run", "passed", "failed"]
    content_safety_receipt_ref: str | None = None
    raw_correction_content_included: Literal[False] = False
    raw_prompt_content_included: Literal[False] = False
    raw_response_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_correction(self) -> "OperatorCorrectionEvidence":
        _validate_ref(self.correction_ref, "correction_ref")
        _validate_ref(self.source_revision_ref, "source_revision_ref")
        for value, field_name in (
            (self.execution_attempt_ref, "execution_attempt_ref"),
            (self.transformed_fixture_ref, "transformed_fixture_ref"),
            (self.independent_review_ref, "independent_review_ref"),
            (self.content_safety_receipt_ref, "content_safety_receipt_ref"),
        ):
            if value is not None:
                _validate_ref(value, field_name)
        return self


class OperatorCorrectionDecision(_FrozenModel):
    schema_version: Literal["uaa-taw05-operator-correction-decision.v1"] = (
        "uaa-taw05-operator-correction-decision.v1"
    )
    correction_ref: str
    disposition: Literal["blocked", "eligible_for_separate_durable_promotion"]
    reason_refs: tuple[str, ...] = Field(..., min_length=1)
    durable_eval_eligible: bool
    automatic_eval_promotion_performed: Literal[False] = False
    durable_fixture_written: Literal[False] = False
    policy_or_alias_updated: Literal[False] = False
    online_training_performed: Literal[False] = False
    provider_call_performed: Literal[False] = False
    model_call_count: Literal[0] = 0
    second_ordinary_chat_model_call_count: Literal[0] = 0
    runtime_execution_performed: Literal[False] = False
    connector_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False
    public_claim_made: Literal[False] = False
    authority_granted: Literal[False] = False
    production_authority_granted: Literal[False] = False
    decision_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_decision(self) -> "OperatorCorrectionDecision":
        _validate_ref(self.correction_ref, "correction_ref")
        _validate_refs(self.reason_refs, "reason_refs")
        if self.durable_eval_eligible != (
            self.disposition == "eligible_for_separate_durable_promotion"
        ):
            raise ValueError("correction disposition and eligibility disagree")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"decision_fingerprint_ref"}),
            prefix="correction-decision-ref:taw05",
        )
        if self.decision_fingerprint_ref != expected:
            raise ValueError("operator correction decision fingerprint binding drift")
        return self


class OutcomeLifecycleEvidence(_FrozenModel):
    proposal_ref: str | None = None
    approval_ref: str | None = None
    start_evidence: AttemptStartEvidence | None = None
    terminal_receipt: TerminalReceiptEvidence | None = None

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "OutcomeLifecycleEvidence":
        for value, field_name in (
            (self.proposal_ref, "proposal_ref"),
            (self.approval_ref, "approval_ref"),
        ):
            if value is not None:
                _validate_ref(value, field_name)
        if self.terminal_receipt is not None and self.start_evidence is None:
            raise ValueError("terminal receipt requires exact durable start evidence")
        if self.start_evidence is not None and self.terminal_receipt is not None:
            _validate_start_receipt_binding(
                self.start_evidence,
                self.terminal_receipt,
            )
        return self


class OutcomeLifecycleProjection(_FrozenModel):
    posture: Literal[
        "ordinary_canonical_lifecycle",
        "outcome_uncertain",
        "terminal_evidence_available",
    ]
    ordinary_lifecycle_posture_preserved: bool
    execution_start_present: bool
    terminal_receipt_present: bool
    runtime_execution_performed: Literal[False] = False
    model_call_count: Literal[0] = 0
    second_ordinary_chat_model_call_count: Literal[0] = 0
    provider_call_performed: Literal[False] = False
    connector_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False
    public_claim_made: Literal[False] = False
    authority_granted: Literal[False] = False
    production_authority_granted: Literal[False] = False
    projection_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_lifecycle_projection(self) -> "OutcomeLifecycleProjection":
        if not self.execution_start_present:
            expected_posture = "ordinary_canonical_lifecycle"
        elif not self.terminal_receipt_present:
            expected_posture = "outcome_uncertain"
        else:
            expected_posture = "terminal_evidence_available"
        if self.posture != expected_posture:
            raise ValueError("lifecycle posture does not match terminal evidence")
        if self.ordinary_lifecycle_posture_preserved != (
            expected_posture == "ordinary_canonical_lifecycle"
        ):
            raise ValueError("ordinary lifecycle preservation is inconsistent")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"projection_fingerprint_ref"}),
            prefix="outcome-lifecycle-ref:taw05",
        )
        if self.projection_fingerprint_ref != expected:
            raise ValueError("outcome lifecycle fingerprint binding drift")
        return self


def build_outcome_evaluation_policy(
    *,
    policy_snapshot_ref: str,
    evaluator_revision_ref: str,
    reviewed_completion_sla_ref: str,
    reviewed_completion_sla_seconds: int,
    repository_hard_max_window_seconds: int,
    clock_source_ref: str,
) -> OutcomeEvaluationPolicy:
    payload: dict[str, Any] = {
        "policy_snapshot_ref": policy_snapshot_ref,
        "evaluator_revision_ref": evaluator_revision_ref,
        "reviewed_completion_sla_ref": reviewed_completion_sla_ref,
        "reviewed_completion_sla_seconds": reviewed_completion_sla_seconds,
        "repository_hard_max_window_seconds": repository_hard_max_window_seconds,
        "clock_source_ref": clock_source_ref,
    }
    payload["policy_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw05-outcome-evaluation-policy.v1",
        },
        prefix="outcome-policy-ref:taw05",
    )
    return OutcomeEvaluationPolicy.model_validate(payload)


def build_capability_outcome_contract(
    *,
    operation_id: str,
    capability_contract_version: str,
    operation_schema_fingerprint_ref: str,
    policy: OutcomeEvaluationPolicy | dict[str, Any],
    completion_window_seconds: int,
    environment_class_refs: Iterable[str],
    terminal_status_refs: dict[TerminalReceiptStatus | str, str],
) -> CapabilityOutcomeContract:
    policy_model = OutcomeEvaluationPolicy.model_validate(
        policy.model_dump(mode="python")
        if isinstance(policy, OutcomeEvaluationPolicy)
        else dict(policy)
    )
    normalized_status_refs = {
        TerminalReceiptStatus(status): value
        for status, value in terminal_status_refs.items()
    }
    if set(normalized_status_refs) != set(TerminalReceiptStatus):
        raise ValueError("terminal status refs must cover each terminal status exactly")
    bounded_environment_refs = _bounded_tuple(
        environment_class_refs,
        "environment class refs",
        max_items=16,
    )
    bindings = tuple(
        TerminalStatusBinding(
            status=status,
            terminal_status_ref=normalized_status_refs[status],
        )
        for status in sorted(TerminalReceiptStatus, key=lambda item: item.value)
    )
    payload: dict[str, Any] = {
        "operation_id": operation_id,
        "capability_contract_version": capability_contract_version,
        "operation_schema_fingerprint_ref": operation_schema_fingerprint_ref,
        "policy_snapshot_ref": policy_model.policy_snapshot_ref,
        "evaluator_revision_ref": policy_model.evaluator_revision_ref,
        "reviewed_completion_sla_ref": policy_model.reviewed_completion_sla_ref,
        "completion_window_seconds": completion_window_seconds,
        "clock_source_ref": policy_model.clock_source_ref,
        "environment_class_refs": tuple(sorted(bounded_environment_refs)),
        "terminal_status_bindings": tuple(
            item.model_dump(mode="json") for item in bindings
        ),
    }
    payload["contract_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw05-capability-outcome-contract.v1",
        },
        prefix="outcome-contract-ref:taw05",
    )
    contract = CapabilityOutcomeContract.model_validate(payload)
    _validate_policy_contract_binding(policy_model, contract)
    return contract


def build_attempt_start_evidence(
    *,
    contract: CapabilityOutcomeContract,
    execution_attempt_ref: str,
    durable_start_evidence_ref: str,
    environment_class_ref: str,
    started_at_epoch_seconds: int,
) -> AttemptStartEvidence:
    contract_model = CapabilityOutcomeContract.model_validate(
        contract.model_dump(mode="python")
    )
    payload: dict[str, Any] = {
        "operation_id": contract_model.operation_id,
        "execution_attempt_ref": execution_attempt_ref,
        "durable_start_evidence_ref": durable_start_evidence_ref,
        "contract_fingerprint_ref": contract_model.contract_fingerprint_ref,
        "operation_schema_fingerprint_ref": (
            contract_model.operation_schema_fingerprint_ref
        ),
        "policy_snapshot_ref": contract_model.policy_snapshot_ref,
        "evaluator_revision_ref": contract_model.evaluator_revision_ref,
        "environment_class_ref": environment_class_ref,
        "started_at_epoch_seconds": started_at_epoch_seconds,
    }
    payload["start_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw05-attempt-start-evidence.v1",
            "durable_start_recorded": True,
            "content_redacted": True,
            "raw_content_included": False,
        },
        prefix="attempt-start-ref:taw05",
    )
    start = AttemptStartEvidence.model_validate(payload)
    _validate_start_contract_binding(contract_model, start)
    return start


def build_terminal_receipt_evidence(
    *,
    contract: CapabilityOutcomeContract,
    start: AttemptStartEvidence,
    terminal_receipt_ref: str,
    terminal_status: TerminalReceiptStatus,
    terminal_at_epoch_seconds: int,
    terminal_evidence_refs: Iterable[str] = (),
) -> TerminalReceiptEvidence:
    contract_model = CapabilityOutcomeContract.model_validate(
        contract.model_dump(mode="python")
    )
    start_model = AttemptStartEvidence.model_validate(start.model_dump(mode="python"))
    _validate_start_contract_binding(contract_model, start_model)
    terminal_status_ref = {
        item.status: item.terminal_status_ref
        for item in contract_model.terminal_status_bindings
    }[terminal_status]
    payload: dict[str, Any] = {
        "operation_id": contract_model.operation_id,
        "execution_attempt_ref": start_model.execution_attempt_ref,
        "durable_start_evidence_ref": start_model.durable_start_evidence_ref,
        "start_fingerprint_ref": start_model.start_fingerprint_ref,
        "terminal_receipt_ref": terminal_receipt_ref,
        "terminal_status": terminal_status,
        "terminal_status_ref": terminal_status_ref,
        "contract_fingerprint_ref": contract_model.contract_fingerprint_ref,
        "operation_schema_fingerprint_ref": (
            contract_model.operation_schema_fingerprint_ref
        ),
        "policy_snapshot_ref": contract_model.policy_snapshot_ref,
        "evaluator_revision_ref": contract_model.evaluator_revision_ref,
        "environment_class_ref": start_model.environment_class_ref,
        "terminal_at_epoch_seconds": terminal_at_epoch_seconds,
        "terminal_evidence_refs": tuple(
            sorted(
                _bounded_tuple(
                    terminal_evidence_refs,
                    "terminal evidence refs",
                    max_items=16,
                )
            )
        ),
    }
    payload["receipt_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw05-terminal-receipt-evidence.v1",
            "immutable_receipt": True,
            "durable_receipt": True,
            "content_redacted": True,
            "raw_content_included": False,
        },
        prefix="terminal-receipt-ref:taw05",
    )
    receipt = TerminalReceiptEvidence.model_validate(payload)
    _validate_receipt_contract_binding(contract_model, receipt)
    _validate_start_receipt_binding(start_model, receipt)
    return receipt


def _validate_policy_contract_binding(
    policy: OutcomeEvaluationPolicy,
    contract: CapabilityOutcomeContract,
) -> None:
    if (
        contract.policy_snapshot_ref != policy.policy_snapshot_ref
        or contract.evaluator_revision_ref != policy.evaluator_revision_ref
        or contract.reviewed_completion_sla_ref != policy.reviewed_completion_sla_ref
        or contract.clock_source_ref != policy.clock_source_ref
    ):
        raise ValueError("outcome contract and evaluation policy binding mismatch")
    if contract.completion_window_seconds != policy.reviewed_completion_sla_seconds:
        raise ValueError("completion window must equal the reviewed completion SLA")
    if contract.completion_window_seconds > policy.repository_hard_max_window_seconds:
        raise ValueError("completion window exceeds repository hard maximum")


def _validate_start_contract_binding(
    contract: CapabilityOutcomeContract,
    start: AttemptStartEvidence,
) -> None:
    if (
        start.operation_id != contract.operation_id
        or start.contract_fingerprint_ref != contract.contract_fingerprint_ref
        or start.operation_schema_fingerprint_ref
        != contract.operation_schema_fingerprint_ref
        or start.policy_snapshot_ref != contract.policy_snapshot_ref
        or start.evaluator_revision_ref != contract.evaluator_revision_ref
        or start.environment_class_ref not in contract.environment_class_refs
    ):
        raise ValueError("attempt start and outcome contract binding mismatch")


def _validate_receipt_contract_binding(
    contract: CapabilityOutcomeContract,
    receipt: TerminalReceiptEvidence,
) -> None:
    status_refs = {
        item.status: item.terminal_status_ref
        for item in contract.terminal_status_bindings
    }
    if (
        receipt.operation_id != contract.operation_id
        or receipt.contract_fingerprint_ref != contract.contract_fingerprint_ref
        or receipt.operation_schema_fingerprint_ref
        != contract.operation_schema_fingerprint_ref
        or receipt.policy_snapshot_ref != contract.policy_snapshot_ref
        or receipt.evaluator_revision_ref != contract.evaluator_revision_ref
        or receipt.environment_class_ref not in contract.environment_class_refs
        or receipt.terminal_status_ref != status_refs[receipt.terminal_status]
    ):
        raise ValueError("terminal receipt and outcome contract binding mismatch")


def _validate_start_receipt_binding(
    start: AttemptStartEvidence,
    receipt: TerminalReceiptEvidence,
) -> None:
    if (
        receipt.operation_id != start.operation_id
        or receipt.execution_attempt_ref != start.execution_attempt_ref
        or receipt.durable_start_evidence_ref != start.durable_start_evidence_ref
        or receipt.start_fingerprint_ref != start.start_fingerprint_ref
        or receipt.contract_fingerprint_ref != start.contract_fingerprint_ref
        or receipt.operation_schema_fingerprint_ref
        != start.operation_schema_fingerprint_ref
        or receipt.policy_snapshot_ref != start.policy_snapshot_ref
        or receipt.evaluator_revision_ref != start.evaluator_revision_ref
        or receipt.environment_class_ref != start.environment_class_ref
        or receipt.terminal_at_epoch_seconds < start.started_at_epoch_seconds
    ):
        raise ValueError("terminal receipt and durable start binding mismatch")


def _deduplicate_starts(
    starts: Iterable[AttemptStartEvidence | dict[str, Any]],
) -> tuple[AttemptStartEvidence, ...]:
    unique_by_fingerprint: dict[str, AttemptStartEvidence] = {}
    fingerprint_by_attempt: dict[str, str] = {}
    fingerprint_by_start_ref: dict[str, str] = {}
    for raw in _bounded_tuple(starts, "attempt starts"):
        start = AttemptStartEvidence.model_validate(
            raw.model_dump(mode="python")
            if isinstance(raw, AttemptStartEvidence)
            else dict(raw)
        )
        for identity, seen, label in (
            (start.execution_attempt_ref, fingerprint_by_attempt, "attempt ref"),
            (
                start.durable_start_evidence_ref,
                fingerprint_by_start_ref,
                "durable start ref",
            ),
        ):
            previous = seen.get(identity)
            if previous is not None and previous != start.start_fingerprint_ref:
                raise ValueError(f"conflicting reuse of {label}")
            seen[identity] = start.start_fingerprint_ref
        unique_by_fingerprint.setdefault(start.start_fingerprint_ref, start)
    return tuple(
        sorted(
            unique_by_fingerprint.values(), key=lambda item: item.execution_attempt_ref
        )
    )


def _deduplicate_receipts(
    receipts: Iterable[TerminalReceiptEvidence | dict[str, Any]],
) -> tuple[TerminalReceiptEvidence, ...]:
    unique_by_fingerprint: dict[str, TerminalReceiptEvidence] = {}
    fingerprint_by_receipt: dict[str, str] = {}
    fingerprint_by_attempt: dict[str, str] = {}
    for raw in _bounded_tuple(receipts, "terminal receipts"):
        receipt = TerminalReceiptEvidence.model_validate(
            raw.model_dump(mode="python")
            if isinstance(raw, TerminalReceiptEvidence)
            else dict(raw)
        )
        for identity, seen, label in (
            (receipt.terminal_receipt_ref, fingerprint_by_receipt, "receipt ref"),
            (receipt.execution_attempt_ref, fingerprint_by_attempt, "attempt receipt"),
        ):
            previous = seen.get(identity)
            if previous is not None and previous != receipt.receipt_fingerprint_ref:
                raise ValueError(f"conflicting reuse of {label}")
            seen[identity] = receipt.receipt_fingerprint_ref
        unique_by_fingerprint.setdefault(receipt.receipt_fingerprint_ref, receipt)
    return tuple(
        sorted(
            unique_by_fingerprint.values(), key=lambda item: item.execution_attempt_ref
        )
    )


def project_capability_outcomes(
    *,
    policy: OutcomeEvaluationPolicy | dict[str, Any],
    contract: CapabilityOutcomeContract | dict[str, Any],
    starts: Iterable[AttemptStartEvidence | dict[str, Any]],
    receipts: Iterable[TerminalReceiptEvidence | dict[str, Any]],
    as_of_epoch_seconds: int,
    prior: OutcomePriorEvidence | dict[str, Any] | None = None,
) -> CapabilityOutcomeProjection:
    policy_model = OutcomeEvaluationPolicy.model_validate(
        policy.model_dump(mode="python")
        if isinstance(policy, OutcomeEvaluationPolicy)
        else dict(policy)
    )
    contract_model = CapabilityOutcomeContract.model_validate(
        contract.model_dump(mode="python")
        if isinstance(contract, CapabilityOutcomeContract)
        else dict(contract)
    )
    _validate_policy_contract_binding(policy_model, contract_model)
    if as_of_epoch_seconds < 0:
        raise ValueError("as-of cutoff must be non-negative")

    start_models = _deduplicate_starts(starts)
    receipt_models = _deduplicate_receipts(receipts)
    starts_by_attempt = {item.execution_attempt_ref: item for item in start_models}
    receipts_by_attempt = {item.execution_attempt_ref: item for item in receipt_models}
    for start in start_models:
        _validate_start_contract_binding(contract_model, start)
        if start.started_at_epoch_seconds > as_of_epoch_seconds:
            raise ValueError("attempt start occurs after the as-of cutoff")
    for receipt in receipt_models:
        _validate_receipt_contract_binding(contract_model, receipt)
        start = starts_by_attempt.get(receipt.execution_attempt_ref)
        if start is None:
            raise ValueError("terminal receipt has no exact bound start evidence")
        _validate_start_receipt_binding(start, receipt)
        if receipt.terminal_at_epoch_seconds > as_of_epoch_seconds:
            raise ValueError("terminal receipt occurs after the as-of cutoff")

    observations: list[AttemptOutcomeObservation] = []
    for start in start_models:
        receipt = receipts_by_attempt.get(start.execution_attempt_ref)
        if receipt is None:
            elapsed = as_of_epoch_seconds - start.started_at_epoch_seconds
            outcome_class = (
                OutcomeObservationClass.still_live
                if elapsed <= contract_model.completion_window_seconds
                else OutcomeObservationClass.unresolved_overdue
            )
            observations.append(
                AttemptOutcomeObservation(
                    execution_attempt_ref=start.execution_attempt_ref,
                    durable_start_evidence_ref=start.durable_start_evidence_ref,
                    start_fingerprint_ref=start.start_fingerprint_ref,
                    terminal_receipt_ref=None,
                    receipt_fingerprint_ref=None,
                    outcome_class=outcome_class,
                    outcome_posture="outcome_uncertain",
                    included_in_outcome_rate_denominator=(
                        outcome_class == OutcomeObservationClass.unresolved_overdue
                    ),
                    counts_as_success=False,
                )
            )
            continue
        outcome_class = OutcomeObservationClass(receipt.terminal_status.value)
        observations.append(
            AttemptOutcomeObservation(
                execution_attempt_ref=start.execution_attempt_ref,
                durable_start_evidence_ref=start.durable_start_evidence_ref,
                start_fingerprint_ref=start.start_fingerprint_ref,
                terminal_receipt_ref=receipt.terminal_receipt_ref,
                receipt_fingerprint_ref=receipt.receipt_fingerprint_ref,
                outcome_class=outcome_class,
                outcome_posture="terminal_proven",
                included_in_outcome_rate_denominator=True,
                counts_as_success=(outcome_class == OutcomeObservationClass.succeeded),
            )
        )

    prior_status: Literal[
        "absent", "current_non_authoritative", "invalidated_stale"
    ] = "absent"
    prior_reason_refs: tuple[str, ...] = ("reason-ref:taw05:prior-absent",)
    if prior is not None:
        prior_model = OutcomePriorEvidence.model_validate(
            prior.model_dump(mode="python")
            if isinstance(prior, OutcomePriorEvidence)
            else dict(prior)
        )
        current = (
            prior_model.contract_fingerprint_ref
            == contract_model.contract_fingerprint_ref
            and prior_model.operation_schema_fingerprint_ref
            == contract_model.operation_schema_fingerprint_ref
            and prior_model.policy_snapshot_ref == policy_model.policy_snapshot_ref
            and prior_model.evaluator_revision_ref
            == policy_model.evaluator_revision_ref
        )
        prior_status = "current_non_authoritative" if current else "invalidated_stale"
        prior_reason_refs = (
            "reason-ref:taw05:prior-bindings-current"
            if current
            else "reason-ref:taw05:prior-bindings-stale",
        )

    counts = {
        outcome_class: sum(item.outcome_class == outcome_class for item in observations)
        for outcome_class in OutcomeObservationClass
    }
    terminal_count = sum(
        counts[OutcomeObservationClass(status.value)]
        for status in TerminalReceiptStatus
    )
    denominator = terminal_count + counts[OutcomeObservationClass.unresolved_overdue]
    succeeded_count = counts[OutcomeObservationClass.succeeded]
    payload: dict[str, Any] = {
        "operation_id": contract_model.operation_id,
        "contract_fingerprint_ref": contract_model.contract_fingerprint_ref,
        "policy_fingerprint_ref": policy_model.policy_fingerprint_ref,
        "as_of_epoch_seconds": as_of_epoch_seconds,
        "completion_window_seconds": contract_model.completion_window_seconds,
        "clock_source_ref": contract_model.clock_source_ref,
        "attempt_inventory_count": len(observations),
        "still_live_count": counts[OutcomeObservationClass.still_live],
        "unresolved_overdue_count": counts[OutcomeObservationClass.unresolved_overdue],
        "terminal_count": terminal_count,
        "succeeded_count": succeeded_count,
        "failed_count": counts[OutcomeObservationClass.failed],
        "canceled_count": counts[OutcomeObservationClass.canceled],
        "rolled_back_count": counts[OutcomeObservationClass.rolled_back],
        "non_success_count": denominator - succeeded_count,
        "health_rate_denominator": denominator,
        "reliability_rate_denominator": denominator,
        "familiarity_rate_denominator": denominator,
        "success_basis_points": (
            None if denominator == 0 else succeeded_count * 10_000 // denominator
        ),
        "prior_status": prior_status,
        "prior_reason_refs": prior_reason_refs,
        "observations": tuple(item.model_dump(mode="json") for item in observations),
    }
    payload["projection_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw05-capability-outcome-projection.v1",
            "contract_ref": TAW05_CONTRACT_REF,
            "projector_ref": TAW05_PROJECTOR_REF,
            "non_authoritative": True,
            "durable_statistics_store_mutated": False,
            "receipt_arrival_handler_registered": False,
            "online_training_performed": False,
            "automatic_policy_or_alias_promotion": False,
            "provider_call_performed": False,
            "model_call_count": 0,
            "second_ordinary_chat_model_call_count": 0,
            "runtime_execution_performed": False,
            "connector_call_performed": False,
            "external_write_performed": False,
            "public_claim_made": False,
            "authority_granted": False,
            "production_authority_granted": False,
        },
        prefix="outcome-projection-ref:taw05",
    )
    return CapabilityOutcomeProjection.model_validate(payload)


def evaluate_operator_correction(
    evidence: OperatorCorrectionEvidence | dict[str, Any],
) -> OperatorCorrectionDecision:
    evidence_model = OperatorCorrectionEvidence.model_validate(
        evidence.model_dump(mode="python")
        if isinstance(evidence, OperatorCorrectionEvidence)
        else dict(evidence)
    )
    eligible = (
        evidence_model.transformation_kind in {"synthetic", "fully_redacted"}
        and evidence_model.transformed_fixture_ref is not None
        and evidence_model.review_status == "accepted"
        and evidence_model.independent_review_ref is not None
        and evidence_model.content_safety_status == "passed"
        and evidence_model.content_safety_receipt_ref is not None
    )
    reason_refs = (
        ("reason-ref:taw05:correction-reviewed-safe",)
        if eligible
        else ("reason-ref:taw05:correction-promotion-blocked",)
    )
    payload: dict[str, Any] = {
        "correction_ref": evidence_model.correction_ref,
        "disposition": (
            "eligible_for_separate_durable_promotion" if eligible else "blocked"
        ),
        "reason_refs": reason_refs,
        "durable_eval_eligible": eligible,
    }
    payload["decision_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw05-operator-correction-decision.v1",
            "automatic_eval_promotion_performed": False,
            "durable_fixture_written": False,
            "policy_or_alias_updated": False,
            "online_training_performed": False,
            "provider_call_performed": False,
            "model_call_count": 0,
            "second_ordinary_chat_model_call_count": 0,
            "runtime_execution_performed": False,
            "connector_call_performed": False,
            "external_write_performed": False,
            "public_claim_made": False,
            "authority_granted": False,
            "production_authority_granted": False,
        },
        prefix="correction-decision-ref:taw05",
    )
    return OperatorCorrectionDecision.model_validate(payload)


def project_outcome_lifecycle(
    evidence: OutcomeLifecycleEvidence | dict[str, Any],
) -> OutcomeLifecycleProjection:
    evidence_model = OutcomeLifecycleEvidence.model_validate(
        evidence.model_dump(mode="python")
        if isinstance(evidence, OutcomeLifecycleEvidence)
        else dict(evidence)
    )
    start_present = evidence_model.start_evidence is not None
    receipt_present = evidence_model.terminal_receipt is not None
    if not start_present:
        posture = "ordinary_canonical_lifecycle"
    elif not receipt_present:
        posture = "outcome_uncertain"
    else:
        posture = "terminal_evidence_available"
    payload: dict[str, Any] = {
        "posture": posture,
        "ordinary_lifecycle_posture_preserved": not start_present,
        "execution_start_present": start_present,
        "terminal_receipt_present": receipt_present,
    }
    payload["projection_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "runtime_execution_performed": False,
            "model_call_count": 0,
            "second_ordinary_chat_model_call_count": 0,
            "provider_call_performed": False,
            "connector_call_performed": False,
            "external_write_performed": False,
            "public_claim_made": False,
            "authority_granted": False,
            "production_authority_granted": False,
        },
        prefix="outcome-lifecycle-ref:taw05",
    )
    return OutcomeLifecycleProjection.model_validate(payload)


__all__ = [
    "AttemptOutcomeObservation",
    "AttemptStartEvidence",
    "CapabilityOutcomeContract",
    "CapabilityOutcomeProjection",
    "OperatorCorrectionDecision",
    "OperatorCorrectionEvidence",
    "OutcomeEvaluationPolicy",
    "OutcomeLifecycleEvidence",
    "OutcomeLifecycleProjection",
    "OutcomeObservationClass",
    "OutcomePriorEvidence",
    "TAW05_CONTRACT_REF",
    "TAW05_MAX_OBSERVATIONS",
    "TAW05_PROJECTOR_REF",
    "TerminalReceiptEvidence",
    "TerminalReceiptStatus",
    "TerminalStatusBinding",
    "build_attempt_start_evidence",
    "build_capability_outcome_contract",
    "build_outcome_evaluation_policy",
    "build_terminal_receipt_evidence",
    "evaluate_operator_correction",
    "project_capability_outcomes",
    "project_outcome_lifecycle",
]
