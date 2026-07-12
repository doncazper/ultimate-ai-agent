from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, model_validator

from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_REDACTIONS,
)
from ultimate_ai_agent.core.authority.budget_contracts import (
    AuthorityBudgetReceipt,
    AuthorityBudgetStatus,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityLease,
    AuthorityLeaseScope,
    authority_state_lock_manager,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchReceipt,
    AuthorityDispatchStatus,
)
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanReceipt,
)
from ultimate_ai_agent.core.execution.durable_mission_controls import (
    MissionControlEvent,
    MissionControlReceipt,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepReceipt,
    MissionStepStatus,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.time import utc_now


MISSION_COMPLETION_SCHEMA_VERSION = "uaa-mission-completion.v1"
MISSION_COMPLETION_LEDGER_FILE = "mission_completion_receipts.jsonl"
MISSION_COMPLETION_LOCK_KEY = "authority-mission-completions"
MISSION_COMPLETION_LEDGER_MAX_BYTES = 4 * 1024 * 1024
MISSION_COMPLETION_LEDGER_MAX_RECEIPTS = 1_000


class MissionCompletionError(RuntimeError):
    pass


class MissionCompletionConflictError(MissionCompletionError):
    pass


class MissionCompletionCorruptionError(MissionCompletionError):
    pass


class _MissionCompletionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)


class MissionCompletionStepBinding(_MissionCompletionModel):
    step_ref: str
    definition_fingerprint_ref: str
    dispatch_ref: str
    dispatch_request_fingerprint_ref: str
    step_receipt_ref: str
    step_entry_hash_ref: str
    dispatch_receipt_ref: str
    dispatch_entry_hash_ref: str
    evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_binding(self) -> "MissionCompletionStepBinding":
        _validate_refs(self.model_dump(mode="python"), "mission_completion_step")
        return self


class MissionCompletionDispatchBinding(_MissionCompletionModel):
    dispatch_ref: str
    receipt_ref: str
    entry_hash_ref: str
    request_fingerprint_ref: str
    lease_ref: str
    action_ref: str
    adapter_ref: str
    capability_ref: str
    authority_decision_ref: str
    authority_policy_receipt_ref: str
    approval_required: StrictBool
    approval_ref: str | None = None
    approval_validation_ref: str | None = None
    budget_reservation_ref: str
    budget_reservation_receipt_ref: str
    budget_start_receipt_ref: str
    budget_settlement_receipt_ref: str
    execution_ref: str
    actual_operation_count: StrictInt = Field(..., ge=1)
    actual_cost_microusd: StrictInt = Field(..., ge=0)
    actual_cost_ref: str
    evidence_refs: tuple[str, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_binding(self) -> "MissionCompletionDispatchBinding":
        _validate_refs(self.model_dump(mode="python"), "mission_completion_dispatch")
        if self.approval_required and (
            self.approval_ref is None or self.approval_validation_ref is None
        ):
            raise ValueError("MISSION_COMPLETION_APPROVAL_BINDING_REQUIRED")
        return self


class MissionCompletionBudgetBinding(_MissionCompletionModel):
    reservation_ref: str
    reserve_receipt_ref: str
    reserve_entry_hash_ref: str
    start_receipt_ref: str
    start_entry_hash_ref: str
    settlement_receipt_ref: str
    settlement_entry_hash_ref: str
    lease_ref: str
    action_ref: str
    execution_ref: str
    reserved_operation_count: StrictInt = Field(..., ge=1)
    reserved_cost_microusd: StrictInt = Field(..., ge=0)
    actual_operation_count: StrictInt = Field(..., ge=1)
    actual_cost_microusd: StrictInt = Field(..., ge=0)
    actual_cost_ref: str
    settlement_status: Literal["settled"] = "settled"
    unresolved_cost: Literal[False] = False

    @model_validator(mode="after")
    def validate_binding(self) -> "MissionCompletionBudgetBinding":
        _validate_refs(self.model_dump(mode="python"), "mission_completion_budget")
        return self


class MissionCompletionManifest(_MissionCompletionModel):
    schema_version: Literal["uaa-mission-completion.v1"] = (
        MISSION_COMPLETION_SCHEMA_VERSION
    )
    sequence: StrictInt = Field(..., ge=1)
    completion_ref: str
    plan_ref: str
    plan_fingerprint_ref: str
    plan_receipt_ref: str
    plan_entry_hash_ref: str
    mission_ref: str
    run_ref: str
    lease_ref: str
    lease_scope_fingerprint_ref: str | None = None
    lease_scope: Literal["mission"] = "mission"
    lease_mission_ref: str
    lease_issued_at: datetime
    lease_expires_at: datetime
    mission_deadline: datetime
    concurrency_limit: Literal[1] = 1
    parallel_execution_performed: Literal[False] = False
    status: Literal["succeeded"] = "succeeded"
    step_bindings: tuple[MissionCompletionStepBinding, ...] = Field(
        ..., min_length=1, max_length=16
    )
    dispatch_bindings: tuple[MissionCompletionDispatchBinding, ...] = Field(
        ..., min_length=1, max_length=16
    )
    budget_bindings: tuple[MissionCompletionBudgetBinding, ...] = Field(
        ..., min_length=1, max_length=16
    )
    approval_refs: tuple[str, ...] = ()
    approval_validation_refs: tuple[str, ...] = ()
    control_snapshot_ref: str
    control_receipt_refs: tuple[str, ...] = ()
    cancellation_receipt_refs: tuple[str, ...] = ()
    dead_letter_receipt_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = Field(..., min_length=1)
    memory_candidate_ref: str
    memory_candidate_posture: Literal["review_required_recall_only"] = (
        "review_required_recall_only"
    )
    memory_truth_authority: Literal[False] = False
    context_injection_authorized: Literal[False] = False
    execution_evidence_grants_authority: Literal[False] = False
    signature_present: Literal[False] = False
    integrity_posture: Literal["content_free_hash_chain"] = (
        "content_free_hash_chain"
    )
    redactions_applied: tuple[str, ...] = Field(
        default_factory=lambda: tuple(AUTHORITY_STATE_REDACTIONS)
    )
    raw_paths_included: Literal[False] = False
    raw_prompt_included: Literal[False] = False
    raw_response_included: Literal[False] = False
    raw_provider_payload_included: Literal[False] = False
    previous_entry_hash_ref: str | None = None
    entry_hash_ref: str
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_manifest(self) -> "MissionCompletionManifest":
        _validate_refs(self.model_dump(mode="python"), "mission_completion")
        if self.lease_mission_ref != self.mission_ref:
            raise ValueError("MISSION_COMPLETION_LEASE_MISSION_MISMATCH")
        if not self.lease_issued_at.tzinfo or not self.lease_expires_at.tzinfo:
            raise ValueError("MISSION_COMPLETION_LEASE_TIMEZONE_REQUIRED")
        if not self.mission_deadline.tzinfo or not self.created_at.tzinfo:
            raise ValueError("MISSION_COMPLETION_TIMEZONE_REQUIRED")
        if self.mission_deadline > self.lease_expires_at:
            raise ValueError("MISSION_COMPLETION_DEADLINE_EXCEEDS_LEASE")
        if len(self.step_bindings) != len(self.dispatch_bindings):
            raise ValueError("MISSION_COMPLETION_STEP_DISPATCH_COUNT_MISMATCH")
        if len(self.dispatch_bindings) != len(self.budget_bindings):
            raise ValueError("MISSION_COMPLETION_DISPATCH_BUDGET_COUNT_MISMATCH")
        if tuple(item.dispatch_ref for item in self.step_bindings) != tuple(
            item.dispatch_ref for item in self.dispatch_bindings
        ):
            raise ValueError("MISSION_COMPLETION_DISPATCH_ORDER_MISMATCH")
        if any(
            dispatch.lease_ref != self.lease_ref
            or budget.lease_ref != self.lease_ref
            or step.dispatch_receipt_ref != dispatch.receipt_ref
            or step.dispatch_entry_hash_ref != dispatch.entry_hash_ref
            or step.dispatch_request_fingerprint_ref
            != dispatch.request_fingerprint_ref
            or dispatch.budget_reservation_ref != budget.reservation_ref
            or dispatch.budget_reservation_receipt_ref
            != budget.reserve_receipt_ref
            or dispatch.budget_start_receipt_ref != budget.start_receipt_ref
            or dispatch.budget_settlement_receipt_ref
            != budget.settlement_receipt_ref
            or budget.action_ref != dispatch.action_ref
            or budget.execution_ref != dispatch.execution_ref
            or budget.actual_operation_count != dispatch.actual_operation_count
            or budget.actual_cost_microusd != dispatch.actual_cost_microusd
            or budget.actual_cost_ref != dispatch.actual_cost_ref
            for step, dispatch, budget in zip(
                self.step_bindings,
                self.dispatch_bindings,
                self.budget_bindings,
                strict=True,
            )
        ):
            raise ValueError("MISSION_COMPLETION_EXECUTION_BINDING_MISMATCH")
        expected_approval_refs = tuple(
            item.approval_ref for item in self.dispatch_bindings if item.approval_ref
        )
        expected_validation_refs = tuple(
            item.approval_validation_ref
            for item in self.dispatch_bindings
            if item.approval_validation_ref
        )
        if (
            self.approval_refs != expected_approval_refs
            or self.approval_validation_refs != expected_validation_refs
        ):
            raise ValueError("MISSION_COMPLETION_APPROVAL_SUMMARY_MISMATCH")
        if set(AUTHORITY_STATE_REDACTIONS) - set(self.redactions_applied):
            raise ValueError("MISSION_COMPLETION_REQUIRED_REDACTIONS_MISSING")
        completion_payload: dict[str, Any] = {
                "plan_ref": self.plan_ref,
                "plan_fingerprint_ref": self.plan_fingerprint_ref,
                "mission_ref": self.mission_ref,
                "run_ref": self.run_ref,
                "lease_ref": self.lease_ref,
                "lease_issued_at": self.lease_issued_at.isoformat(),
                "lease_expires_at": self.lease_expires_at.isoformat(),
                "mission_deadline": self.mission_deadline.isoformat(),
                "plan_receipt_ref": self.plan_receipt_ref,
                "plan_entry_hash_ref": self.plan_entry_hash_ref,
                "step_bindings": [
                    item.model_dump(mode="json") for item in self.step_bindings
                ],
                "dispatch_bindings": [
                    item.model_dump(mode="json") for item in self.dispatch_bindings
                ],
                "budget_bindings": [
                    item.model_dump(mode="json") for item in self.budget_bindings
                ],
                "approval_refs": self.approval_refs,
                "approval_validation_refs": self.approval_validation_refs,
                "control_snapshot_ref": self.control_snapshot_ref,
                "control_receipt_refs": self.control_receipt_refs,
                "cancellation_receipt_refs": self.cancellation_receipt_refs,
                "dead_letter_receipt_refs": self.dead_letter_receipt_refs,
                "evidence_refs": self.evidence_refs,
            }
        if self.lease_scope_fingerprint_ref is not None:
            completion_payload["lease_scope_fingerprint_ref"] = (
                self.lease_scope_fingerprint_ref
            )
        expected_ref = _stable_ref("mission-completion-ref", completion_payload)
        if self.completion_ref != expected_ref:
            raise ValueError("MISSION_COMPLETION_REF_INVALID")
        expected_memory_ref = _stable_ref(
            "business-memory-candidate-ref:mission-completion",
            {"completion_ref": self.completion_ref},
        )
        if self.memory_candidate_ref != expected_memory_ref:
            raise ValueError("MISSION_COMPLETION_MEMORY_CANDIDATE_REF_INVALID")
        return self


class MissionCompletionVerificationResult(_MissionCompletionModel):
    valid: StrictBool
    completion_ref: str | None = None
    reason_refs: tuple[str, ...] = ()
    signature_verified: Literal[False] = False
    raw_content_inspected: Literal[False] = False
    source_ledgers_verified: StrictBool = False


class MissionCompletionIntegritySummary(_MissionCompletionModel):
    schema_version: Literal["uaa-mission-completion-integrity-summary.v1"] = (
        "uaa-mission-completion-integrity-summary.v1"
    )
    verifier_version_ref: str = (
        "verifier-ref:mission-completion:sha256-chain:v1"
    )
    manifest_count: StrictInt = Field(..., ge=0, le=MISSION_COMPLETION_LEDGER_MAX_RECEIPTS)
    chain_ref: str
    genesis_entry_hash_ref: str | None = None
    terminal_entry_hash_ref: str | None = None
    hash_chain_verified: Literal[True] = True
    source_ledgers_verified: Literal[False] = False
    signature_present: Literal[False] = False
    signing_status: Literal["blocked_signing_lifecycle_not_implemented"] = (
        "blocked_signing_lifecycle_not_implemented"
    )
    cryptographic_authenticity_verified: Literal[False] = False
    external_anchor_verified: Literal[False] = False
    execution_evidence_grants_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_summary(self) -> "MissionCompletionIntegritySummary":
        _validate_refs(self.model_dump(mode="python"), "mission_completion_integrity")
        if self.manifest_count == 0 and (
            self.genesis_entry_hash_ref is not None
            or self.terminal_entry_hash_ref is not None
        ):
            raise ValueError("MISSION_COMPLETION_EMPTY_CHAIN_HASH_INVALID")
        if self.manifest_count > 0 and (
            self.genesis_entry_hash_ref is None
            or self.terminal_entry_hash_ref is None
        ):
            raise ValueError("MISSION_COMPLETION_CHAIN_HASH_REQUIRED")
        return self


class PortableMissionEvidenceInspectionSummary(_MissionCompletionModel):
    schema_version: Literal["uaa-portable-mission-evidence-inspection.v1"] = (
        "uaa-portable-mission-evidence-inspection.v1"
    )
    status: Literal[
        "verified_local_hash_chain",
        "not_recorded",
        "not_evaluated",
        "unavailable",
    ]
    bundle_ref: str | None = None
    completion_count: StrictInt = Field(..., ge=0, le=MISSION_COMPLETION_LEDGER_MAX_RECEIPTS)
    envelope_count: StrictInt = Field(..., ge=0, le=MISSION_COMPLETION_LEDGER_MAX_RECEIPTS)
    terminal_entry_hash_ref: str | None = None
    local_hash_chain_verified: StrictBool = False
    source_receipts_bound: StrictBool = False
    source_ledgers_verified: Literal[False] = False
    caller_expected_binding_matched: Literal[False] = False
    signature_verified: Literal[False] = False
    signing_status: Literal["blocked_signing_lifecycle_not_implemented"] = (
        "blocked_signing_lifecycle_not_implemented"
    )
    cryptographic_authenticity_verified: Literal[False] = False
    external_anchor_verified: Literal[False] = False
    execution_evidence_grants_authority: Literal[False] = False
    reason_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_summary(self) -> "PortableMissionEvidenceInspectionSummary":
        _validate_refs(self.model_dump(mode="python"), "portable_evidence_inspection")
        if self.status == "verified_local_hash_chain":
            if (
                not self.bundle_ref
                or not self.terminal_entry_hash_ref
                or self.completion_count < 1
                or self.envelope_count < 1
                or not self.local_hash_chain_verified
                or not self.source_receipts_bound
            ):
                raise ValueError("PORTABLE_EVIDENCE_VERIFIED_SUMMARY_INVALID")
        elif (
            self.bundle_ref is not None
            or self.terminal_entry_hash_ref is not None
            or self.envelope_count != 0
            or self.local_hash_chain_verified
            or self.source_receipts_bound
        ):
            raise ValueError("PORTABLE_EVIDENCE_UNVERIFIED_SUMMARY_INVALID")
        return self


class MissionCompletionReadModel(_MissionCompletionModel):
    schema_version: Literal["uaa-mission-completion-read-model.v1"] = (
        "uaa-mission-completion-read-model.v1"
    )
    ledger_ref: str = "ledger-ref:mission-completion-receipts"
    completion_count: StrictInt = Field(..., ge=0)
    latest_manifests: tuple[MissionCompletionManifest, ...] = Field(
        default=(), max_length=12
    )
    integrity_summary: MissionCompletionIntegritySummary
    portable_evidence_summary: PortableMissionEvidenceInspectionSummary
    operator_summary: str
    request_scoped_authority_still_required: Literal[True] = True
    execution_available_from_read_model: Literal[False] = False
    approval_or_lease_minted: Literal[False] = False
    raw_content_included: Literal[False] = False
    raw_paths_included: Literal[False] = False
    source_ledgers_verified: Literal[False] = False

    @model_validator(mode="after")
    def validate_read_model(self) -> "MissionCompletionReadModel":
        validate_task_ref(self.ledger_ref, "mission_completion_ledger_ref")
        if len(self.latest_manifests) > self.completion_count:
            raise ValueError("MISSION_COMPLETION_READ_MODEL_COUNT_INVALID")
        if self.portable_evidence_summary.completion_count != self.completion_count:
            raise ValueError("MISSION_COMPLETION_PORTABLE_COUNT_MISMATCH")
        return self


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def authority_lease_issuance_scope_fingerprint_ref(lease: AuthorityLease) -> str:
    """Hash immutable issuance scope while excluding later revocation posture."""

    payload = lease.model_dump(mode="json", exclude={"status", "safe_summary"})
    constraints = dict(payload.get("constraints", {}))
    constraints.pop("revocation_reason_ref", None)
    constraints.pop("revocation_idempotency_ref", None)
    payload["constraints"] = constraints
    return _stable_ref("authority-lease-scope-fingerprint-ref", payload)


def _validate_refs(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"{field_name}_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"{field_name}_{name}")
            else:
                _validate_refs(nested, field_name)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested, field_name)


def _entry_hash(manifest: MissionCompletionManifest) -> str:
    payload = manifest.model_dump(mode="json", exclude={"entry_hash_ref"})
    if manifest.lease_scope_fingerprint_ref is None:
        payload.pop("lease_scope_fingerprint_ref", None)
    return _stable_ref("mission-completion-entry-hash-ref", payload)


def verify_mission_completion(
    manifest: MissionCompletionManifest | dict[str, Any],
    *,
    plan_receipt: DurableMissionPlanReceipt | None = None,
    lease: AuthorityLease | None = None,
    step_receipts: list[MissionStepReceipt] | None = None,
    dispatch_receipts: list[AuthorityDispatchReceipt] | None = None,
    budget_receipts: list[AuthorityBudgetReceipt] | None = None,
    control_receipts: list[MissionControlReceipt] | None = None,
) -> MissionCompletionVerificationResult:
    try:
        parsed = MissionCompletionManifest.model_validate(manifest)
    except ValueError:
        return MissionCompletionVerificationResult(
            valid=False,
            reason_refs=("reason-ref:mission-completion:contract-invalid",),
        )
    if parsed.entry_hash_ref != _entry_hash(parsed):
        return MissionCompletionVerificationResult(
            valid=False,
            completion_ref=parsed.completion_ref,
            reason_refs=("reason-ref:mission-completion:entry-hash-invalid",),
        )
    bundles = (
        plan_receipt,
        lease,
        step_receipts,
        dispatch_receipts,
        budget_receipts,
        control_receipts,
    )
    if any(item is not None for item in bundles):
        if any(item is None for item in bundles):
            return MissionCompletionVerificationResult(
                valid=False,
                completion_ref=parsed.completion_ref,
                reason_refs=(
                    "reason-ref:mission-completion:source-bundle-incomplete",
                ),
            )
        assert plan_receipt is not None
        assert lease is not None
        assert step_receipts is not None
        assert dispatch_receipts is not None
        assert budget_receipts is not None
        assert control_receipts is not None
        try:
            expected = build_mission_completion_manifest(
                sequence=parsed.sequence,
                plan_receipt=plan_receipt,
                lease=lease,
                step_receipts=step_receipts,
                dispatch_receipts=dispatch_receipts,
                budget_receipts=budget_receipts,
                control_receipts=control_receipts,
                previous_entry_hash_ref=parsed.previous_entry_hash_ref,
                created_at=parsed.created_at,
            )
        except ValueError:
            return MissionCompletionVerificationResult(
                valid=False,
                completion_ref=parsed.completion_ref,
                reason_refs=(
                    "reason-ref:mission-completion:source-bundle-invalid",
                ),
            )
        if expected != parsed:
            return MissionCompletionVerificationResult(
                valid=False,
                completion_ref=parsed.completion_ref,
                reason_refs=(
                    "reason-ref:mission-completion:source-bundle-mismatch",
                ),
            )
        return MissionCompletionVerificationResult(
            valid=True,
            completion_ref=parsed.completion_ref,
            reason_refs=(
                "reason-ref:mission-completion:offline-source-ledgers-verified",
            ),
            source_ledgers_verified=True,
        )
    return MissionCompletionVerificationResult(
        valid=True,
        completion_ref=parsed.completion_ref,
        reason_refs=("reason-ref:mission-completion:manifest-hash-verified",),
    )


def build_mission_completion_manifest(
    *,
    sequence: int,
    plan_receipt: DurableMissionPlanReceipt,
    lease: AuthorityLease,
    step_receipts: list[MissionStepReceipt],
    dispatch_receipts: list[AuthorityDispatchReceipt],
    budget_receipts: list[AuthorityBudgetReceipt],
    control_receipts: list[MissionControlReceipt],
    previous_entry_hash_ref: str | None,
    created_at: datetime | None = None,
) -> MissionCompletionManifest:
    plan = plan_receipt.plan
    if lease.scope != AuthorityLeaseScope.mission.value:
        raise ValueError("MISSION_COMPLETION_MISSION_LEASE_REQUIRED")
    if lease.mission_ref != plan.mission_ref:
        raise ValueError("MISSION_COMPLETION_LEASE_MISSION_MISMATCH")
    ordered_steps = {item.definition.step_ref: item for item in step_receipts}
    ordered_dispatches = {item.dispatch_ref: item for item in dispatch_receipts}
    plan_step_refs = [item.step_ref for item in plan.ordered_steps]
    if (
        len(ordered_steps) != len(step_receipts)
        or len(step_receipts) != len(plan_step_refs)
        or set(ordered_steps) != set(plan_step_refs)
    ):
        raise ValueError("MISSION_COMPLETION_EXACT_STEP_MEMBERSHIP_REQUIRED")
    selected_steps = [ordered_steps[step_ref] for step_ref in plan_step_refs]
    selected_dispatch_refs = [item.dispatch_ref for item in selected_steps]
    if (
        any(ref is None for ref in selected_dispatch_refs)
        or len(ordered_dispatches) != len(dispatch_receipts)
        or len(dispatch_receipts) != len(plan_step_refs)
        or set(ordered_dispatches) != set(selected_dispatch_refs)
    ):
        raise ValueError("MISSION_COMPLETION_EXACT_DISPATCH_MEMBERSHIP_REQUIRED")
    budgets_by_ref = {item.receipt_ref: item for item in budget_receipts}
    step_bindings: list[MissionCompletionStepBinding] = []
    dispatch_bindings: list[MissionCompletionDispatchBinding] = []
    budget_bindings: list[MissionCompletionBudgetBinding] = []
    evidence_refs: list[str] = [
        plan_receipt.receipt_ref,
        plan_receipt.entry_hash_ref,
    ]
    mission_controls = [
        receipt
        for receipt in control_receipts
        if receipt.request.plan_ref == plan.plan_ref
        and receipt.request.mission_ref == plan.mission_ref
        and receipt.request.run_ref == plan.run_ref
    ]
    cancellation_receipt_refs = tuple(
        receipt.receipt_ref
        for receipt in mission_controls
        if receipt.request.event == MissionControlEvent.cancellation_requested.value
    )
    dead_letter_receipt_refs = tuple(
        receipt.receipt_ref
        for receipt in mission_controls
        if receipt.request.event
        == MissionControlEvent.dead_letter_recovery_requested.value
    )
    if cancellation_receipt_refs:
        raise ValueError("MISSION_COMPLETION_CANCELLATION_CONFLICT")
    control_receipt_refs = tuple(receipt.receipt_ref for receipt in mission_controls)
    control_snapshot_ref = _stable_ref(
        "mission-control-snapshot-ref",
        [
            {
                "receipt_ref": receipt.receipt_ref,
                "entry_hash_ref": receipt.entry_hash_ref,
            }
            for receipt in mission_controls
        ],
    )
    for plan_step in plan.ordered_steps:
        step = ordered_steps.get(plan_step.step_ref)
        dispatch = (
            ordered_dispatches.get(step.dispatch_ref)
            if step is not None and step.dispatch_ref is not None
            else None
        )
        permitted_attempts = {
            plan_step.dispatch_ref: plan_step.dispatch_request_fingerprint_ref,
            **{
                attempt.dispatch_ref: attempt.dispatch_request_fingerprint_ref
                for attempt in plan_step.retry_attempts
            },
        }
        if (
            step is None
            or step.status != MissionStepStatus.succeeded.value
            or dispatch is None
            or dispatch.status != AuthorityDispatchStatus.succeeded.value
        ):
            raise ValueError("MISSION_COMPLETION_TERMINAL_SUCCESS_REQUIRED")
        if (
            step.definition_fingerprint_ref != plan_step.definition_fingerprint_ref
            or step.dispatch_ref not in permitted_attempts
            or step.dispatch_request_fingerprint_ref
            != permitted_attempts.get(step.dispatch_ref or "")
            or step.dispatch_receipt_ref != dispatch.receipt_ref
            or step.dispatch_entry_hash_ref != dispatch.entry_hash_ref
            or dispatch.request_fingerprint_ref
            != permitted_attempts.get(dispatch.dispatch_ref)
            or dispatch.lease_ref != lease.lease_ref
        ):
            raise ValueError("MISSION_COMPLETION_CROSS_LEDGER_BINDING_INVALID")
        required_budget_refs = (
            dispatch.budget_reservation_receipt_ref,
            dispatch.budget_start_receipt_ref,
            dispatch.budget_settlement_receipt_ref,
        )
        if any(ref is None for ref in required_budget_refs):
            raise ValueError("MISSION_COMPLETION_BUDGET_BINDING_REQUIRED")
        reserve, start, settle = (
            budgets_by_ref.get(str(ref)) for ref in required_budget_refs
        )
        if reserve is None or start is None or settle is None:
            raise ValueError("MISSION_COMPLETION_BUDGET_RECEIPT_MISSING")
        if (
            reserve.status != AuthorityBudgetStatus.reserved.value
            or start.status != AuthorityBudgetStatus.started.value
            or settle.status != AuthorityBudgetStatus.settled.value
            or settle.actual_cost_microusd is None
            or settle.actual_cost_ref is None
            or settle.actual_operation_count is None
            or settle.execution_ref != dispatch.execution_ref
            or reserve.lease_ref != lease.lease_ref
            or start.lease_ref != lease.lease_ref
            or settle.lease_ref != lease.lease_ref
            or reserve.action_ref != dispatch.action_ref
            or start.action_ref != dispatch.action_ref
            or settle.action_ref != dispatch.action_ref
        ):
            raise ValueError("MISSION_COMPLETION_BUDGET_NOT_SETTLED")
        if (
            dispatch.authority_decision_ref is None
            or dispatch.authority_policy_receipt_ref is None
            or dispatch.execution_ref is None
            or dispatch.actual_operation_count is None
            or dispatch.actual_cost_microusd is None
            or dispatch.actual_cost_ref is None
        ):
            raise ValueError("MISSION_COMPLETION_DISPATCH_EVIDENCE_INCOMPLETE")
        step_bindings.append(
            MissionCompletionStepBinding(
                step_ref=step.definition.step_ref,
                definition_fingerprint_ref=step.definition_fingerprint_ref,
                dispatch_ref=dispatch.dispatch_ref,
                dispatch_request_fingerprint_ref=dispatch.request_fingerprint_ref,
                step_receipt_ref=step.receipt_ref,
                step_entry_hash_ref=step.entry_hash_ref,
                dispatch_receipt_ref=dispatch.receipt_ref,
                dispatch_entry_hash_ref=dispatch.entry_hash_ref,
                evidence_refs=tuple(step.evidence_refs),
            )
        )
        dispatch_bindings.append(
            MissionCompletionDispatchBinding(
                dispatch_ref=dispatch.dispatch_ref,
                receipt_ref=dispatch.receipt_ref,
                entry_hash_ref=dispatch.entry_hash_ref,
                request_fingerprint_ref=dispatch.request_fingerprint_ref,
                lease_ref=dispatch.lease_ref,
                action_ref=dispatch.action_ref,
                adapter_ref=dispatch.adapter_ref,
                capability_ref=dispatch.capability_ref,
                authority_decision_ref=dispatch.authority_decision_ref,
                authority_policy_receipt_ref=dispatch.authority_policy_receipt_ref,
                approval_required=dispatch.approval_required,
                approval_ref=dispatch.approval_ref,
                approval_validation_ref=dispatch.approval_validation_ref,
                budget_reservation_ref=str(dispatch.budget_reservation_ref),
                budget_reservation_receipt_ref=str(
                    dispatch.budget_reservation_receipt_ref
                ),
                budget_start_receipt_ref=str(dispatch.budget_start_receipt_ref),
                budget_settlement_receipt_ref=str(
                    dispatch.budget_settlement_receipt_ref
                ),
                execution_ref=dispatch.execution_ref,
                actual_operation_count=dispatch.actual_operation_count,
                actual_cost_microusd=dispatch.actual_cost_microusd,
                actual_cost_ref=dispatch.actual_cost_ref,
                evidence_refs=tuple(dispatch.evidence_refs),
            )
        )
        budget_bindings.append(
            MissionCompletionBudgetBinding(
                reservation_ref=reserve.reservation_ref,
                reserve_receipt_ref=reserve.receipt_ref,
                reserve_entry_hash_ref=reserve.entry_hash_ref,
                start_receipt_ref=start.receipt_ref,
                start_entry_hash_ref=start.entry_hash_ref,
                settlement_receipt_ref=settle.receipt_ref,
                settlement_entry_hash_ref=settle.entry_hash_ref,
                lease_ref=lease.lease_ref,
                action_ref=dispatch.action_ref,
                execution_ref=dispatch.execution_ref,
                reserved_operation_count=reserve.reserved_operation_count,
                reserved_cost_microusd=reserve.reserved_cost_microusd or 0,
                actual_operation_count=settle.actual_operation_count,
                actual_cost_microusd=settle.actual_cost_microusd,
                actual_cost_ref=settle.actual_cost_ref,
            )
        )
        evidence_refs.extend(
            [
                step.receipt_ref,
                step.entry_hash_ref,
                dispatch.receipt_ref,
                dispatch.entry_hash_ref,
                reserve.receipt_ref,
                start.receipt_ref,
                settle.receipt_ref,
                *step.evidence_refs,
                *dispatch.evidence_refs,
            ]
        )
    lease_scope_fingerprint_ref = authority_lease_issuance_scope_fingerprint_ref(
        lease
    )
    completion_payload: dict[str, Any] = {
            "plan_ref": plan.plan_ref,
            "plan_fingerprint_ref": plan_receipt.plan_fingerprint_ref,
            "mission_ref": plan.mission_ref,
            "run_ref": plan.run_ref,
            "lease_ref": lease.lease_ref,
            "lease_issued_at": lease.issued_at.isoformat(),
            "lease_expires_at": lease.expires_at.isoformat(),
            "mission_deadline": min(
                lease.expires_at,
                max(item.definition.deadline for item in selected_steps),
            ).isoformat(),
            "plan_receipt_ref": plan_receipt.receipt_ref,
            "plan_entry_hash_ref": plan_receipt.entry_hash_ref,
            "step_bindings": [
                item.model_dump(mode="json") for item in step_bindings
            ],
            "dispatch_bindings": [
                item.model_dump(mode="json") for item in dispatch_bindings
            ],
            "budget_bindings": [
                item.model_dump(mode="json") for item in budget_bindings
            ],
            "approval_refs": [
                item.approval_ref for item in dispatch_bindings if item.approval_ref
            ],
            "approval_validation_refs": [
                item.approval_validation_ref
                for item in dispatch_bindings
                if item.approval_validation_ref
            ],
            "control_snapshot_ref": control_snapshot_ref,
            "control_receipt_refs": control_receipt_refs,
            "cancellation_receipt_refs": cancellation_receipt_refs,
            "dead_letter_receipt_refs": dead_letter_receipt_refs,
            "evidence_refs": list(dict.fromkeys(evidence_refs)),
            "lease_scope_fingerprint_ref": lease_scope_fingerprint_ref,
        }
    completion_ref = _stable_ref(
        "mission-completion-ref",
        completion_payload,
    )
    base = MissionCompletionManifest(
        sequence=sequence,
        completion_ref=completion_ref,
        plan_ref=plan.plan_ref,
        plan_fingerprint_ref=plan_receipt.plan_fingerprint_ref,
        plan_receipt_ref=plan_receipt.receipt_ref,
        plan_entry_hash_ref=plan_receipt.entry_hash_ref,
        mission_ref=plan.mission_ref,
        run_ref=plan.run_ref,
        lease_ref=lease.lease_ref,
        lease_scope_fingerprint_ref=lease_scope_fingerprint_ref,
        lease_mission_ref=lease.mission_ref or "",
        lease_issued_at=lease.issued_at,
        lease_expires_at=lease.expires_at,
        mission_deadline=min(
            lease.expires_at,
            max(item.definition.deadline for item in selected_steps),
        ),
        step_bindings=tuple(step_bindings),
        dispatch_bindings=tuple(dispatch_bindings),
        budget_bindings=tuple(budget_bindings),
        approval_refs=tuple(
            item.approval_ref for item in dispatch_bindings if item.approval_ref
        ),
        approval_validation_refs=tuple(
            item.approval_validation_ref
            for item in dispatch_bindings
            if item.approval_validation_ref
        ),
        control_snapshot_ref=control_snapshot_ref,
        control_receipt_refs=control_receipt_refs,
        cancellation_receipt_refs=cancellation_receipt_refs,
        dead_letter_receipt_refs=dead_letter_receipt_refs,
        evidence_refs=tuple(dict.fromkeys(evidence_refs)),
        memory_candidate_ref=_stable_ref(
            "business-memory-candidate-ref:mission-completion",
            {"completion_ref": completion_ref},
        ),
        previous_entry_hash_ref=previous_entry_hash_ref,
        entry_hash_ref="mission-completion-entry-hash-ref:pending",
        created_at=created_at or utc_now(),
    )
    return base.model_copy(update={"entry_hash_ref": _entry_hash(base)})


class MissionCompletionStore:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.receipts_path = state_dir / MISSION_COMPLETION_LEDGER_FILE
        self.lock_manager = authority_state_lock_manager(str(state_dir.resolve()))
        self._source_resolvers: tuple[
            Callable[[], list[DurableMissionPlanReceipt]],
            Callable[[], list[AuthorityLease]],
            Callable[[], list[MissionStepReceipt]],
            Callable[[], list[AuthorityDispatchReceipt]],
            Callable[[], list[AuthorityBudgetReceipt]],
            Callable[[], list[MissionControlReceipt]],
        ] | None = None

    def bind_source_resolvers(
        self,
        *,
        plan_receipts: Callable[[], list[DurableMissionPlanReceipt]],
        leases: Callable[[], list[AuthorityLease]],
        step_receipts: Callable[[], list[MissionStepReceipt]],
        dispatch_receipts: Callable[[], list[AuthorityDispatchReceipt]],
        budget_receipts: Callable[[], list[AuthorityBudgetReceipt]],
        control_receipts: Callable[[], list[MissionControlReceipt]],
    ) -> None:
        if self._source_resolvers is not None:
            raise ValueError("MISSION_COMPLETION_SOURCE_RESOLVERS_ALREADY_BOUND")
        self._source_resolvers = (
            plan_receipts,
            leases,
            step_receipts,
            dispatch_receipts,
            budget_receipts,
            control_receipts,
        )

    def list_manifests(self) -> list[MissionCompletionManifest]:
        with self.lock_manager.acquire(MISSION_COMPLETION_LOCK_KEY):
            return self._load()

    def build_read_model(
        self,
        *,
        recent_limit: int = 12,
        portable_evidence_summary: PortableMissionEvidenceInspectionSummary | None = None,
    ) -> MissionCompletionReadModel:
        if recent_limit < 0 or recent_limit > 12:
            raise ValueError("MISSION_COMPLETION_RECENT_LIMIT_INVALID")
        manifests = self.list_manifests()
        latest = tuple(manifests[-recent_limit:]) if recent_limit else ()
        integrity_summary = MissionCompletionIntegritySummary(
            manifest_count=len(manifests),
            chain_ref=_stable_ref(
                "mission-completion-chain-ref",
                [item.entry_hash_ref for item in manifests],
            ),
            genesis_entry_hash_ref=(manifests[0].entry_hash_ref if manifests else None),
            terminal_entry_hash_ref=(manifests[-1].entry_hash_ref if manifests else None),
        )
        return MissionCompletionReadModel(
            completion_count=len(manifests),
            latest_manifests=latest,
            integrity_summary=integrity_summary,
            portable_evidence_summary=(
                portable_evidence_summary
                or PortableMissionEvidenceInspectionSummary(
                    status="not_evaluated",
                    completion_count=len(manifests),
                    envelope_count=0,
                    reason_refs=(
                        "reason-ref:portable-mission-evidence:not-evaluated",
                    ),
                )
            ),
            operator_summary=(
                f"{len(manifests)} content-free hash-chained mission completion "
                "manifest(s) are available for review; source-ledger verification "
                "is performed only in the completion transaction."
            ),
        )

    def record(
        self,
        *,
        plan_receipt: DurableMissionPlanReceipt,
        lease: AuthorityLease,
        step_receipts: list[MissionStepReceipt],
        dispatch_receipts: list[AuthorityDispatchReceipt],
        budget_receipts: list[AuthorityBudgetReceipt],
    ) -> MissionCompletionManifest:
        if self._source_resolvers is None:
            raise MissionCompletionError(
                "MISSION_COMPLETION_SOURCE_LEDGERS_REQUIRED"
            )
        (
            plan_resolver,
            lease_resolver,
            step_resolver,
            dispatch_resolver,
            budget_resolver,
            control_resolver,
        ) = self._source_resolvers
        local_plans = plan_resolver()
        local_leases = lease_resolver()
        local_steps = step_resolver()
        local_dispatches = dispatch_resolver()
        local_budgets = budget_resolver()
        local_controls = control_resolver()
        if (
            plan_receipt not in local_plans
            or lease not in local_leases
            or any(item not in local_steps for item in step_receipts)
            or any(item not in local_dispatches for item in dispatch_receipts)
            or any(item not in local_budgets for item in budget_receipts)
        ):
            raise MissionCompletionConflictError(
                "MISSION_COMPLETION_SOURCE_LEDGER_BINDING_INVALID"
            )
        with self.lock_manager.acquire(MISSION_COMPLETION_LOCK_KEY):
            manifests = self._load()
            candidate = build_mission_completion_manifest(
                sequence=len(manifests) + 1,
                plan_receipt=plan_receipt,
                lease=lease,
                step_receipts=step_receipts,
                dispatch_receipts=dispatch_receipts,
                budget_receipts=budget_receipts,
                control_receipts=local_controls,
                previous_entry_hash_ref=(
                    manifests[-1].entry_hash_ref if manifests else None
                ),
            )
            existing = next(
                (
                    item
                    for item in manifests
                    if item.plan_ref == candidate.plan_ref
                    or (item.mission_ref, item.run_ref)
                    == (candidate.mission_ref, candidate.run_ref)
                ),
                None,
            )
            if existing is not None:
                if existing.completion_ref == candidate.completion_ref:
                    return existing
                raise MissionCompletionConflictError(
                    "MISSION_COMPLETION_IMMUTABLE_CONFLICT"
                )
            if not verify_mission_completion(
                candidate,
                plan_receipt=plan_receipt,
                lease=lease,
                step_receipts=step_receipts,
                dispatch_receipts=dispatch_receipts,
                budget_receipts=budget_receipts,
                control_receipts=local_controls,
            ).valid:
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_OFFLINE_VERIFY_FAILED"
                )
            self._append(candidate)
            return candidate

    def _load(self) -> list[MissionCompletionManifest]:
        directory_fd = self._open_state_dir(create=False)
        if directory_fd is None:
            return []
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
            os, "O_NOFOLLOW", 0
        ) | getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(
                MISSION_COMPLETION_LEDGER_FILE,
                flags,
                dir_fd=directory_fd,
            )
        except FileNotFoundError:
            try:
                self._assert_state_dir_binding(directory_fd)
            finally:
                os.close(directory_fd)
            return []
        except OSError as exc:
            os.close(directory_fd)
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_READ_FAILED"
            ) from exc
        try:
            self._assert_state_dir_binding(directory_fd)
            metadata = os.fstat(descriptor)
            path_metadata = os.stat(
                MISSION_COMPLETION_LEDGER_FILE,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_REGULAR_FILE_REQUIRED"
                )
            if metadata.st_size > MISSION_COMPLETION_LEDGER_MAX_BYTES:
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_SIZE_LIMIT_EXCEEDED"
                )
            payload = os.read(descriptor, MISSION_COMPLETION_LEDGER_MAX_BYTES + 1)
        finally:
            os.close(descriptor)
            os.close(directory_fd)
        return self._decode(payload)

    @staticmethod
    def _decode(payload: bytes) -> list[MissionCompletionManifest]:
        if len(payload) > MISSION_COMPLETION_LEDGER_MAX_BYTES or (
            payload and not payload.endswith(b"\n")
        ):
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_SIZE_LIMIT_EXCEEDED"
            )
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_INVALID"
            ) from exc
        if len(lines) > MISSION_COMPLETION_LEDGER_MAX_RECEIPTS:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        manifests: list[MissionCompletionManifest] = []
        previous: str | None = None
        seen: set[tuple[str, str]] = set()
        for sequence, line in enumerate((item for item in lines if item.strip()), 1):
            try:
                manifest = MissionCompletionManifest.model_validate_json(line)
            except ValueError as exc:
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_HISTORY_INVALID"
                ) from exc
            if (
                manifest.sequence != sequence
                or manifest.previous_entry_hash_ref != previous
                or manifest.entry_hash_ref != _entry_hash(manifest)
                or (manifest.mission_ref, manifest.run_ref) in seen
            ):
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_HISTORY_INVALID"
                )
            manifests.append(manifest)
            previous = manifest.entry_hash_ref
            seen.add((manifest.mission_ref, manifest.run_ref))
        return manifests

    def _open_state_dir(self, *, create: bool) -> int | None:
        if create:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(self.state_dir, flags)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_STATE_DIR_INVALID"
            ) from exc
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            os.close(descriptor)
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_STATE_DIR_INVALID"
            )
        try:
            self._assert_state_dir_binding(descriptor)
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    def _assert_state_dir_binding(self, descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        try:
            path_metadata = os.lstat(self.state_dir)
        except OSError as exc:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_STATE_DIR_INVALID"
            ) from exc
        if (
            not stat.S_ISDIR(path_metadata.st_mode)
            or stat.S_ISLNK(path_metadata.st_mode)
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_STATE_DIR_INVALID"
            )

    def _append(self, manifest: MissionCompletionManifest) -> None:
        if manifest.sequence > MISSION_COMPLETION_LEDGER_MAX_RECEIPTS:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_RECEIPT_LIMIT_EXCEEDED"
            )
        directory_fd = self._open_state_dir(create=True)
        if directory_fd is None:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_STATE_DIR_INVALID"
            )
        flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | getattr(
            os, "O_CLOEXEC", 0
        ) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(
                MISSION_COMPLETION_LEDGER_FILE,
                flags,
                0o600,
                dir_fd=directory_fd,
            )
        except OSError as exc:
            os.close(directory_fd)
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_WRITE_FAILED"
            ) from exc
        try:
            self._assert_state_dir_binding(directory_fd)
            metadata = os.fstat(descriptor)
            path_metadata = os.stat(
                MISSION_COMPLETION_LEDGER_FILE,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (path_metadata.st_dev, path_metadata.st_ino)
            ):
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_REGULAR_FILE_REQUIRED"
                )
            encoded = (
                json.dumps(manifest.model_dump(mode="json"), sort_keys=True) + "\n"
            ).encode("utf-8")
            if metadata.st_size + len(encoded) > MISSION_COMPLETION_LEDGER_MAX_BYTES:
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_SIZE_LIMIT_EXCEEDED"
                )
            existing = self._decode(os.pread(descriptor, metadata.st_size, 0))
            if (
                manifest.sequence != len(existing) + 1
                or manifest.previous_entry_hash_ref
                != (existing[-1].entry_hash_ref if existing else None)
                or manifest.entry_hash_ref != _entry_hash(manifest)
            ):
                raise MissionCompletionCorruptionError(
                    "MISSION_COMPLETION_LEDGER_APPEND_BINDING_INVALID"
                )
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("mission completion append failed")
                view = view[written:]
            os.fsync(descriptor)
            self._assert_state_dir_binding(directory_fd)
            os.fsync(directory_fd)
        except OSError as exc:
            raise MissionCompletionCorruptionError(
                "MISSION_COMPLETION_LEDGER_WRITE_FAILED"
            ) from exc
        finally:
            os.close(descriptor)
            os.close(directory_fd)
