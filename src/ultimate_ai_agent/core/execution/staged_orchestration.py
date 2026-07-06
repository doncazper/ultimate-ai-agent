from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.enums import ExecutionStepMode
from ultimate_ai_agent.core.execution.validation import (
    hidden_side_effect_reasons,
    step_mode_reason,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


STAGED_ORCHESTRATION_SCHEMA_VERSION = "staged_orchestration_engine.v1"
STAGED_ORCHESTRATION_CONTRACT_REF = "contract-ref:staged-orchestration-engine:v1"
STAGED_ORCHESTRATION_CLI_REF = "repo-local-command:uaa-runtime-inspect-staged-orchestration"
STAGED_ORCHESTRATION_API_REF = "GET /api/runtime/staged-orchestration"
STAGED_ORCHESTRATION_SOURCE = "python_core_staged_orchestration_read_model"
STAGED_ORCHESTRATION_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:staged-orchestration:no-autonomous-worker",
    "blocked-state:staged-orchestration:no-hidden-model-call",
    "blocked-state:staged-orchestration:no-unrestricted-command-execution",
    "blocked-state:staged-orchestration:no-browser-automation",
    "blocked-state:staged-orchestration:no-connector-write",
    "blocked-state:staged-orchestration:no-production-authority",
    "blocked-state:staged-orchestration:no-raw-payload-persistence",
)
STAGED_ORCHESTRATION_APPROVED_RUNTIME_STEP_AUTHORITY_REF = (
    "authority-ref:staged-orchestration:approved-runtime-command-step"
)
STAGED_ORCHESTRATION_APPROVED_RUNTIME_COMMAND_PROMOTED_INTENTS = (
    "focused_pytest",
)
STAGED_ORCHESTRATION_REDACTIONS = (
    "raw_prompt_omitted",
    "raw_response_omitted",
    "provider_payload_omitted",
    "raw_log_omitted",
    "local_path_omitted",
)

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw response",
    "provider payload",
    "raw log",
    "local path",
    "credential",
)


class StagedOrchestrationStatus(str, Enum):
    pending = "pending"
    running = "running"
    waiting = "waiting"
    degraded = "degraded"
    skipped = "skipped"
    blocked = "blocked"
    failed = "failed"
    completed = "completed"


class StagedOrchestrationCallbackKind(str, Enum):
    deterministic_no_effect = "deterministic_no_effect"
    existing_authority_lane_required = "existing_authority_lane_required"


class StagedOrchestrationValidationStatus(str, Enum):
    accepted = "accepted"
    denied = "denied"


class StagedOrchestrationReplayStatus(str, Enum):
    accepted = "accepted"
    denied = "denied"
    idempotent_replay = "idempotent_replay"


class _StagedOrchestrationModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()[:24]}"


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe orchestration language")


def _validate_refs(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(ref, field_name)


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _runtime_value(value: Any) -> Any:
    return getattr(value, "value", value)


class StagedOrchestrationCallbackRef(_StagedOrchestrationModel):
    callback_ref: str = Field(..., min_length=1)
    callback_kind: StagedOrchestrationCallbackKind = (
        StagedOrchestrationCallbackKind.deterministic_no_effect
    )
    safe_summary: str = Field(..., min_length=1)
    deterministic: bool = True
    no_effect: bool = True
    execution_enabled: bool = False
    authority_lane_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_callback(self) -> "StagedOrchestrationCallbackRef":
        _validate_ref(self.callback_ref, "callback_ref")
        _validate_safe_text(self.safe_summary, "callback_safe_summary")
        _validate_refs(self.evidence_refs, "callback_evidence_ref")
        if self.authority_lane_ref:
            _validate_ref(self.authority_lane_ref, "callback_authority_lane_ref")
        if (
            self.callback_kind
            != StagedOrchestrationCallbackKind.deterministic_no_effect.value
            or not self.deterministic
            or not self.no_effect
            or self.execution_enabled
        ):
            raise ValueError("STAGED_ORCHESTRATION_CALLBACK_EXECUTION_DENIED")
        return self


class StagedOrchestrationCheckpoint(_StagedOrchestrationModel):
    checkpoint_ref: str = Field(..., min_length=1)
    stage_ref: str = Field(..., min_length=1)
    step_ref: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=1)
    safe_summary: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    raw_payload_persisted: bool = False
    execution_performed: bool = False

    @model_validator(mode="after")
    def validate_checkpoint(self) -> "StagedOrchestrationCheckpoint":
        for value, field_name in [
            (self.checkpoint_ref, "checkpoint_ref"),
            (self.stage_ref, "checkpoint_stage_ref"),
            (self.step_ref, "checkpoint_step_ref"),
            (self.idempotency_ref, "checkpoint_idempotency_ref"),
            (self.replay_ref, "checkpoint_replay_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "checkpoint_safe_summary")
        _validate_refs(self.evidence_refs, "checkpoint_evidence_ref")
        _validate_refs(self.receipt_refs, "checkpoint_receipt_ref")
        _validate_refs(self.rollback_refs, "checkpoint_rollback_ref")
        if self.raw_payload_persisted or self.execution_performed:
            raise ValueError("STAGED_ORCHESTRATION_CHECKPOINT_AUTHORITY_DENIED")
        return self

    @property
    def fingerprint_ref(self) -> str:
        return _stable_ref(
            "checkpoint-fingerprint-ref",
            {
                "checkpoint_ref": self.checkpoint_ref,
                "stage_ref": self.stage_ref,
                "step_ref": self.step_ref,
                "sequence": self.sequence,
                "idempotency_ref": self.idempotency_ref,
                "replay_ref": self.replay_ref,
                "evidence_refs": self.evidence_refs,
                "receipt_refs": self.receipt_refs,
                "rollback_refs": self.rollback_refs,
            },
        )


class StagedOrchestrationDegradedHandoff(_StagedOrchestrationModel):
    handoff_ref: str = Field(..., min_length=1)
    source_step_ref: str = Field(..., min_length=1)
    target_stage_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    reason_refs: list[str] = Field(default_factory=list)
    checkpoint_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    execution_enabled: bool = False

    @model_validator(mode="after")
    def validate_handoff(self) -> "StagedOrchestrationDegradedHandoff":
        for value, field_name in [
            (self.handoff_ref, "handoff_ref"),
            (self.source_step_ref, "handoff_source_step_ref"),
            (self.target_stage_ref, "handoff_target_stage_ref"),
            (self.checkpoint_ref, "handoff_checkpoint_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "handoff_safe_summary")
        _validate_refs(self.reason_refs, "handoff_reason_ref")
        _validate_refs(self.evidence_refs, "handoff_evidence_ref")
        _validate_refs(self.receipt_refs, "handoff_receipt_ref")
        if self.execution_enabled:
            raise ValueError("STAGED_ORCHESTRATION_HANDOFF_EXECUTION_DENIED")
        return self


class StagedOrchestrationApprovedRuntimeCommandBinding(_StagedOrchestrationModel):
    binding_ref: str = Field(..., min_length=1)
    authority_ref: str = STAGED_ORCHESTRATION_APPROVED_RUNTIME_STEP_AUTHORITY_REF
    runtime_invocation_ref: str = Field(..., min_length=1)
    runtime_action_envelope_ref: str = Field(..., min_length=1)
    runtime_approval_ref: str = Field(..., min_length=1)
    runtime_exact_scope_ref: str = Field(..., min_length=1)
    expected_payload_fingerprint_ref: str = Field(..., min_length=1)
    expected_policy_decision_ref: str = Field(..., min_length=1)
    command_intent: str = Field(default="focused_pytest", min_length=1)
    safe_disable_ref: str = "safe-disable-ref:governed-runtime-pilot"
    rollback_ref: str = "rollback-ref:governed-runtime-pilot:disable-profile"
    receipt_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=420)

    @model_validator(mode="after")
    def validate_binding(self) -> "StagedOrchestrationApprovedRuntimeCommandBinding":
        for value, field_name in [
            (self.binding_ref, "runtime_binding_ref"),
            (self.authority_ref, "runtime_binding_authority_ref"),
            (self.runtime_invocation_ref, "runtime_binding_invocation_ref"),
            (self.runtime_action_envelope_ref, "runtime_binding_action_envelope_ref"),
            (self.runtime_approval_ref, "runtime_binding_approval_ref"),
            (self.runtime_exact_scope_ref, "runtime_binding_exact_scope_ref"),
            (
                self.expected_payload_fingerprint_ref,
                "runtime_binding_payload_fingerprint_ref",
            ),
            (self.expected_policy_decision_ref, "runtime_binding_policy_decision_ref"),
            (self.safe_disable_ref, "runtime_binding_safe_disable_ref"),
            (self.rollback_ref, "runtime_binding_rollback_ref"),
            (self.receipt_ref, "runtime_binding_receipt_ref"),
        ]:
            if value is not None:
                _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "runtime_binding_safe_summary")
        _validate_safe_text(str(self.command_intent), "runtime_binding_command_intent")
        if self.authority_ref != STAGED_ORCHESTRATION_APPROVED_RUNTIME_STEP_AUTHORITY_REF:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_BINDING_AUTHORITY_REF_REQUIRED")
        if str(self.command_intent) not in STAGED_ORCHESTRATION_APPROVED_RUNTIME_COMMAND_PROMOTED_INTENTS:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_COMMAND_INTENT_NOT_PROMOTED")
        return self


class StagedOrchestrationStep(_StagedOrchestrationModel):
    step_ref: str = Field(..., min_length=1)
    stage_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    status: StagedOrchestrationStatus = StagedOrchestrationStatus.pending
    mode: ExecutionStepMode = ExecutionStepMode.validation_only
    depends_on_step_refs: list[str] = Field(default_factory=list)
    callback_refs: list[StagedOrchestrationCallbackRef] = Field(default_factory=list)
    policy_ref: str | None = None
    approval_posture_ref: str | None = None
    checkpoint_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    reason_refs: list[str] = Field(default_factory=list)
    safe_metadata: dict[str, Any] = Field(default_factory=dict)
    runtime_command_binding: StagedOrchestrationApprovedRuntimeCommandBinding | None = None
    execution_ready: bool = False
    execution_performed: bool = False
    raw_payload_persisted: bool = False

    @model_validator(mode="after")
    def validate_step(self) -> "StagedOrchestrationStep":
        for value, field_name in [
            (self.step_ref, "step_ref"),
            (self.stage_ref, "step_stage_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "step_safe_summary")
        _validate_refs(self.depends_on_step_refs, "step_dependency_ref")
        _validate_refs(self.evidence_refs, "step_evidence_ref")
        _validate_refs(self.receipt_refs, "step_receipt_ref")
        _validate_refs(self.blocked_authority_refs, "step_blocked_authority_ref")
        _validate_refs(self.reason_refs, "step_reason_ref")
        if self.policy_ref:
            _validate_ref(self.policy_ref, "step_policy_ref")
        if self.approval_posture_ref:
            _validate_ref(self.approval_posture_ref, "step_approval_posture_ref")
        if self.checkpoint_ref:
            _validate_ref(self.checkpoint_ref, "step_checkpoint_ref")
        validate_safe_execution_payload(self.safe_metadata, "step_safe_metadata")
        side_effect_reasons = hidden_side_effect_reasons(self.safe_metadata)
        if side_effect_reasons:
            raise ValueError(";".join(side_effect_reasons))
        if self.execution_performed or self.raw_payload_persisted:
            raise ValueError("STAGED_ORCHESTRATION_STEP_AUTHORITY_DENIED")
        mode = ExecutionStepMode(self.mode)
        if self.execution_ready and not (self.policy_ref and self.approval_posture_ref):
            raise ValueError("STAGED_ORCHESTRATION_EXECUTION_READY_SCOPE_REQUIRED")
        if mode == ExecutionStepMode.approved_runtime_command:
            if self.runtime_command_binding is None:
                raise ValueError("STAGED_ORCHESTRATION_RUNTIME_BINDING_REQUIRED")
            if not self.execution_ready:
                raise ValueError("STAGED_ORCHESTRATION_RUNTIME_STEP_NOT_READY")
            return self
        if self.runtime_command_binding is not None:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_BINDING_MODE_REQUIRED")
        reason = step_mode_reason(mode)
        if reason is not None and self.execution_ready:
            raise ValueError("STAGED_ORCHESTRATION_EFFECTFUL_STEP_BLOCKED")
        return self


class StagedOrchestrationStage(_StagedOrchestrationModel):
    stage_ref: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=1)
    safe_summary: str = Field(..., min_length=1)
    status: StagedOrchestrationStatus = StagedOrchestrationStatus.pending
    step_refs: list[str] = Field(default_factory=list)
    checkpoint_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    degraded_handoff_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_stage(self) -> "StagedOrchestrationStage":
        _validate_ref(self.stage_ref, "stage_ref")
        _validate_safe_text(self.safe_summary, "stage_safe_summary")
        _validate_refs(self.step_refs, "stage_step_ref")
        _validate_refs(self.checkpoint_refs, "stage_checkpoint_ref")
        _validate_refs(self.evidence_refs, "stage_evidence_ref")
        _validate_refs(self.degraded_handoff_refs, "stage_degraded_handoff_ref")
        return self


class StagedOrchestrationPlan(_StagedOrchestrationModel):
    schema_version: str = STAGED_ORCHESTRATION_SCHEMA_VERSION
    plan_ref: str = Field(..., min_length=1)
    run_ref: str = Field(..., min_length=1)
    turn_run_approval_chain_ref: str = Field(..., min_length=1)
    route_decision_binding_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    status: StagedOrchestrationStatus = StagedOrchestrationStatus.pending
    stages: list[StagedOrchestrationStage] = Field(..., min_length=1)
    steps: list[StagedOrchestrationStep] = Field(..., min_length=1)
    checkpoints: list[StagedOrchestrationCheckpoint] = Field(default_factory=list)
    degraded_handoffs: list[StagedOrchestrationDegradedHandoff] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(STAGED_ORCHESTRATION_BLOCKED_AUTHORITY_REFS)
    )
    no_effect: bool = True
    approved_runtime_command_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    provider_model_call_enabled: bool = False
    unrestricted_command_execution_enabled: bool = False

    @model_validator(mode="after")
    def validate_plan(self) -> "StagedOrchestrationPlan":
        for value, field_name in [
            (self.plan_ref, "plan_ref"),
            (self.run_ref, "plan_run_ref"),
            (self.turn_run_approval_chain_ref, "turn_run_approval_chain_ref"),
            (self.route_decision_binding_ref, "route_decision_binding_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "plan_safe_summary")
        _validate_refs(self.evidence_refs, "plan_evidence_ref")
        _validate_refs(self.receipt_refs, "plan_receipt_ref")
        _validate_refs(self.blocked_authority_refs, "plan_blocked_authority_ref")
        runtime_steps = [
            step
            for step in self.steps
            if step.mode == ExecutionStepMode.approved_runtime_command.value
        ]
        if runtime_steps and not self.approved_runtime_command_execution_enabled:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_PLAN_ENABLEMENT_REQUIRED")
        if self.approved_runtime_command_execution_enabled:
            if self.no_effect:
                raise ValueError("STAGED_ORCHESTRATION_RUNTIME_PLAN_NO_EFFECT_DRIFT")
            if not runtime_steps:
                raise ValueError("STAGED_ORCHESTRATION_RUNTIME_STEP_REQUIRED")
        if (
            (not self.no_effect and not self.approved_runtime_command_execution_enabled)
            or self.background_autonomy_enabled
            or self.provider_model_call_enabled
            or self.unrestricted_command_execution_enabled
        ):
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_AUTHORITY_DENIED")
        return self


class StagedOrchestrationProgressSummary(_StagedOrchestrationModel):
    total_stage_count: int = Field(..., ge=0)
    total_step_count: int = Field(..., ge=0)
    pending_count: int = Field(default=0, ge=0)
    running_count: int = Field(default=0, ge=0)
    waiting_count: int = Field(default=0, ge=0)
    degraded_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    completed_count: int = Field(default=0, ge=0)


class StagedOrchestrationValidationDecision(_StagedOrchestrationModel):
    schema_version: str = STAGED_ORCHESTRATION_SCHEMA_VERSION
    plan_ref: str = Field(..., min_length=1)
    status: StagedOrchestrationValidationStatus
    reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    no_effect: bool = True
    approved_runtime_command_execution_enabled: bool = False
    execution_performed: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> "StagedOrchestrationValidationDecision":
        _validate_ref(self.plan_ref, "validation_plan_ref")
        _validate_safe_text(self.safe_summary, "validation_safe_summary")
        _validate_refs(self.reason_codes, "validation_reason_ref")
        _validate_refs(self.blocked_authority_refs, "validation_blocked_authority_ref")
        if (
            (not self.no_effect and not self.approved_runtime_command_execution_enabled)
            or self.execution_performed
        ):
            raise ValueError("STAGED_ORCHESTRATION_VALIDATION_AUTHORITY_DENIED")
        return self


class StagedOrchestrationReplayDecision(_StagedOrchestrationModel):
    schema_version: str = STAGED_ORCHESTRATION_SCHEMA_VERSION
    checkpoint_ref: str = Field(..., min_length=1)
    status: StagedOrchestrationReplayStatus
    replay_ref: str = Field(..., min_length=1)
    fingerprint_ref: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    no_effect: bool = True
    execution_performed: bool = False

    @model_validator(mode="after")
    def validate_replay_decision(self) -> "StagedOrchestrationReplayDecision":
        _validate_ref(self.checkpoint_ref, "replay_checkpoint_ref")
        _validate_ref(self.replay_ref, "replay_ref")
        if self.fingerprint_ref:
            _validate_ref(self.fingerprint_ref, "checkpoint_fingerprint_ref")
        _validate_refs(self.reason_codes, "replay_reason_ref")
        _validate_safe_text(self.safe_summary, "replay_safe_summary")
        if not self.no_effect or self.execution_performed:
            raise ValueError("STAGED_ORCHESTRATION_REPLAY_AUTHORITY_DENIED")
        return self


class StagedOrchestrationReadModel(_StagedOrchestrationModel):
    schema_version: str = STAGED_ORCHESTRATION_SCHEMA_VERSION
    contract_ref: str = STAGED_ORCHESTRATION_CONTRACT_REF
    source: str = STAGED_ORCHESTRATION_SOURCE
    backend_owned: bool = True
    plan: StagedOrchestrationPlan
    validation: StagedOrchestrationValidationDecision
    progress: StagedOrchestrationProgressSummary
    latest_checkpoint_ref: str | None = None
    cli_ref: str = STAGED_ORCHESTRATION_CLI_REF
    api_ref: str = STAGED_ORCHESTRATION_API_REF
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(STAGED_ORCHESTRATION_REDACTIONS)
    )
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    execution_performed: bool = False
    approved_runtime_command_execution_enabled: bool = False
    runtime_execution_performed_by_read_model: bool = False
    control_center_can_mint_authority: bool = False

    @model_validator(mode="after")
    def validate_read_model(self) -> "StagedOrchestrationReadModel":
        if self.latest_checkpoint_ref:
            _validate_ref(self.latest_checkpoint_ref, "latest_checkpoint_ref")
        for redaction in self.redactions_applied:
            _validate_safe_text(redaction, "staged_orchestration_redaction")
        if (
            not self.backend_owned
            or not self.safe_refs_only
            or self.raw_payloads_persisted
            or self.execution_performed
            or self.runtime_execution_performed_by_read_model
            or self.control_center_can_mint_authority
        ):
            raise ValueError("STAGED_ORCHESTRATION_READ_MODEL_AUTHORITY_DENIED")
        return self


class StagedOrchestrationRuntimeCommandStepResult(_StagedOrchestrationModel):
    schema_version: str = STAGED_ORCHESTRATION_SCHEMA_VERSION
    step_ref: str = Field(..., min_length=1)
    status: StagedOrchestrationStatus
    runtime_invocation_ref: str = Field(..., min_length=1)
    runtime_action_envelope_ref: str = Field(..., min_length=1)
    runtime_approval_ref: str = Field(..., min_length=1)
    command_intent: str = Field(default="focused_pytest", min_length=1)
    execution_result_ref: str = Field(..., min_length=1)
    receipt_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reason_refs: list[str] = Field(default_factory=list)
    output_summary_returned: bool = False
    output_persisted: bool = False
    raw_payloads_persisted: bool = False
    replayed: bool = False
    execution_performed: bool = False
    command_execution_performed: bool = False
    unrestricted_command_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_execution_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=420)

    @model_validator(mode="after")
    def validate_result(self) -> "StagedOrchestrationRuntimeCommandStepResult":
        for value, field_name in [
            (self.step_ref, "runtime_step_ref"),
            (self.runtime_invocation_ref, "runtime_result_invocation_ref"),
            (self.runtime_action_envelope_ref, "runtime_result_action_envelope_ref"),
            (self.runtime_approval_ref, "runtime_result_approval_ref"),
            (self.execution_result_ref, "runtime_result_ref"),
            (self.receipt_ref, "runtime_result_receipt_ref"),
        ]:
            if value is not None:
                _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "runtime_result_safe_summary")
        _validate_safe_text(str(self.command_intent), "runtime_result_command_intent")
        for field_name in ("evidence_refs", "reason_refs"):
            _validate_refs(getattr(self, field_name), field_name)
        if str(self.command_intent) not in STAGED_ORCHESTRATION_APPROVED_RUNTIME_COMMAND_PROMOTED_INTENTS:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_RESULT_INTENT_NOT_PROMOTED")
        if self.output_persisted or self.raw_payloads_persisted:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_RESULT_PERSISTENCE_DENIED")
        if (
            self.unrestricted_command_execution_enabled
            or self.provider_model_call_enabled
            or self.browser_execution_enabled
            or self.connector_write_enabled
            or self.production_authority_enabled
        ):
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_RESULT_BROAD_AUTHORITY_DENIED")
        if self.command_execution_performed and not self.execution_performed:
            raise ValueError("STAGED_ORCHESTRATION_RUNTIME_RESULT_EXECUTION_FLAG_DRIFT")
        return self


def validate_staged_orchestration_plan(
    plan: StagedOrchestrationPlan,
) -> StagedOrchestrationValidationDecision:
    reason_codes = [
        *_dependency_reason_codes(plan),
        *_authority_reason_codes(plan),
    ]
    status = (
        StagedOrchestrationValidationStatus.denied
        if reason_codes
        else StagedOrchestrationValidationStatus.accepted
    )
    if reason_codes:
        summary = "Staged orchestration plan remains visible with guardrail reason codes."
    elif plan.approved_runtime_command_execution_enabled:
        summary = "Staged orchestration plan validated with exact approved runtime command guardrails."
    else:
        summary = "Staged orchestration plan validated as a no-effect read model."
    return StagedOrchestrationValidationDecision(
        plan_ref=plan.plan_ref,
        status=status,
        reason_codes=reason_codes,
        safe_summary=summary,
        blocked_authority_refs=list(STAGED_ORCHESTRATION_BLOCKED_AUTHORITY_REFS),
        no_effect=plan.no_effect,
        approved_runtime_command_execution_enabled=(
            plan.approved_runtime_command_execution_enabled
        ),
    )


def replay_staged_orchestration_checkpoint(
    plan: StagedOrchestrationPlan,
    *,
    checkpoint_ref: str,
    replay_ref: str,
    fingerprint_ref: str | None = None,
) -> StagedOrchestrationReplayDecision:
    _validate_ref(checkpoint_ref, "checkpoint_ref")
    _validate_ref(replay_ref, "replay_ref")
    checkpoint = next(
        (item for item in plan.checkpoints if item.checkpoint_ref == checkpoint_ref),
        None,
    )
    if checkpoint is None:
        return StagedOrchestrationReplayDecision(
            checkpoint_ref=checkpoint_ref,
            status=StagedOrchestrationReplayStatus.denied,
            replay_ref=replay_ref,
            reason_codes=["reason-ref:staged-orchestration:checkpoint-not-found"],
            safe_summary="Checkpoint replay was denied because the checkpoint ref was not found.",
        )
    if replay_ref == checkpoint.replay_ref and (
        fingerprint_ref is None or fingerprint_ref == checkpoint.fingerprint_ref
    ):
        return StagedOrchestrationReplayDecision(
            checkpoint_ref=checkpoint_ref,
            status=StagedOrchestrationReplayStatus.idempotent_replay,
            replay_ref=replay_ref,
            fingerprint_ref=checkpoint.fingerprint_ref,
            reason_codes=["reason-ref:staged-orchestration:checkpoint-idempotent-replay"],
            safe_summary="Checkpoint replay matched the stored safe fingerprint.",
        )
    return StagedOrchestrationReplayDecision(
        checkpoint_ref=checkpoint_ref,
        status=StagedOrchestrationReplayStatus.denied,
        replay_ref=replay_ref,
        fingerprint_ref=fingerprint_ref,
        reason_codes=["reason-ref:staged-orchestration:checkpoint-replay-conflict"],
        safe_summary="Checkpoint replay was denied because replay refs did not match.",
    )


def build_staged_orchestration_read_model(
    plan: StagedOrchestrationPlan,
) -> StagedOrchestrationReadModel:
    validation = validate_staged_orchestration_plan(plan)
    return StagedOrchestrationReadModel(
        plan=plan,
        validation=validation,
        progress=_progress_summary(plan),
        latest_checkpoint_ref=plan.checkpoints[-1].checkpoint_ref
        if plan.checkpoints
        else None,
        approved_runtime_command_execution_enabled=(
            plan.approved_runtime_command_execution_enabled
        ),
    )


def execute_approved_runtime_command_step(
    plan: StagedOrchestrationPlan,
    *,
    step_ref: str,
    gateway: Any,
    command_request: Any,
    execute_request: Any,
    idempotency_ref: str,
) -> StagedOrchestrationRuntimeCommandStepResult:
    _validate_ref(step_ref, "runtime_step_ref")
    _validate_ref(idempotency_ref, "runtime_step_idempotency_ref")
    validation = validate_staged_orchestration_plan(plan)
    if validation.status != StagedOrchestrationValidationStatus.accepted.value:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_PLAN_NOT_ACCEPTED")
    step = next((candidate for candidate in plan.steps if candidate.step_ref == step_ref), None)
    if step is None:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_STEP_NOT_FOUND")
    if step.mode != ExecutionStepMode.approved_runtime_command.value:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_STEP_MODE_REQUIRED")
    binding = step.runtime_command_binding
    if binding is None:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_BINDING_REQUIRED")
    _validate_runtime_command_binding(
        binding,
        command_request=command_request,
        execute_request=execute_request,
    )
    result = gateway.execute_approved_command(
        binding.runtime_invocation_ref,
        command_request,
        execute_request,
        idempotency_ref=idempotency_ref,
    )
    receipt = result.record.receipt
    command_performed = bool(receipt and receipt.command_execution_performed)
    execution_performed = bool(receipt and receipt.execution_performed)
    status = (
        StagedOrchestrationStatus.completed
        if command_performed and result.error_category is None
        else (
            StagedOrchestrationStatus.failed
            if command_performed
            else StagedOrchestrationStatus.blocked
        )
    )
    reason_refs = []
    if result.error_category:
        reason_refs.append(f"reason-ref:staged-orchestration:{result.error_category.lower()}")
    if not command_performed:
        reason_refs.append("reason-ref:staged-orchestration:runtime-command-not-performed")
    receipt_refs = [receipt.receipt_ref] if receipt else []
    execution_result_ref = _stable_ref(
        "runtime-step-result-ref",
        {
            "step_ref": step_ref,
            "invocation_ref": result.record.invocation_ref,
            "receipt_refs": receipt_refs,
            "status": status.value,
            "error_category": result.error_category,
            "replayed": result.replayed,
        },
    )
    return StagedOrchestrationRuntimeCommandStepResult(
        step_ref=step_ref,
        status=status,
        runtime_invocation_ref=result.record.invocation_ref,
        runtime_action_envelope_ref=binding.runtime_action_envelope_ref,
        runtime_approval_ref=binding.runtime_approval_ref,
        command_intent=str(_runtime_value(command_request.intent)),
        execution_result_ref=execution_result_ref,
        receipt_ref=receipt.receipt_ref if receipt else None,
        evidence_refs=list(receipt.evidence_refs) if receipt else [],
        reason_refs=reason_refs,
        output_summary_returned=result.output_summary_returned,
        replayed=result.replayed,
        execution_performed=execution_performed,
        command_execution_performed=command_performed,
        safe_summary=(
            "Approved staged orchestration runtime command step completed with "
            "a redacted RuntimeGateway receipt."
            if command_performed and result.error_category is None
            else "Approved staged orchestration runtime command step did not complete cleanly."
        ),
    )


def _validate_runtime_command_binding(
    binding: StagedOrchestrationApprovedRuntimeCommandBinding,
    *,
    command_request: Any,
    execute_request: Any,
) -> None:
    command_intent = str(_runtime_value(command_request.intent))
    requested_profile = str(_runtime_value(command_request.requested_profile))
    if command_intent != str(binding.command_intent):
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_COMMAND_INTENT_CHANGED")
    if binding.authority_ref != STAGED_ORCHESTRATION_APPROVED_RUNTIME_STEP_AUTHORITY_REF:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_BINDING_AUTHORITY_REF_REQUIRED")
    if command_intent not in STAGED_ORCHESTRATION_APPROVED_RUNTIME_COMMAND_PROMOTED_INTENTS:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_COMMAND_INTENT_NOT_PROMOTED")
    if requested_profile != "operator-approved":
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_OPERATOR_APPROVED_PROFILE_REQUIRED")
    if command_request.approval_ref != binding.runtime_approval_ref:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_APPROVAL_REF_CHANGED")
    if execute_request.approval_ref != binding.runtime_approval_ref:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_EXECUTE_APPROVAL_REF_CHANGED")
    if execute_request.action_envelope_ref != binding.runtime_action_envelope_ref:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_ACTION_ENVELOPE_CHANGED")
    if execute_request.expected_payload_fingerprint_ref != binding.expected_payload_fingerprint_ref:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_PAYLOAD_FINGERPRINT_CHANGED")
    if execute_request.expected_policy_decision_ref != binding.expected_policy_decision_ref:
        raise ValueError("STAGED_ORCHESTRATION_RUNTIME_POLICY_DECISION_CHANGED")


def build_sample_staged_orchestration_plan() -> StagedOrchestrationPlan:
    callback = StagedOrchestrationCallbackRef(
        callback_ref="callback-ref:staged-orchestration:deterministic-progress",
        safe_summary="Update read-model progress counters without side effects.",
        evidence_refs=["evidence-ref:staged-orchestration:callback"],
    )
    stages = [
        StagedOrchestrationStage(
            stage_ref="stage-ref:staged-orchestration:context",
            sequence=1,
            safe_summary="Collect safe refs and validate route binding.",
            status=StagedOrchestrationStatus.completed,
            step_refs=["step-ref:staged-orchestration:context-pack"],
            checkpoint_refs=["checkpoint-ref:staged-orchestration:context"],
            evidence_refs=["evidence-ref:staged-orchestration:context"],
        ),
        StagedOrchestrationStage(
            stage_ref="stage-ref:staged-orchestration:approval",
            sequence=2,
            safe_summary="Wait for exact approval posture before any future execution lane.",
            status=StagedOrchestrationStatus.waiting,
            step_refs=[
                "step-ref:staged-orchestration:approval-wait",
                "step-ref:staged-orchestration:degraded-review",
            ],
            checkpoint_refs=["checkpoint-ref:staged-orchestration:approval"],
            evidence_refs=["evidence-ref:staged-orchestration:approval"],
            degraded_handoff_refs=["handoff-ref:staged-orchestration:operator-review"],
        ),
        StagedOrchestrationStage(
            stage_ref="stage-ref:staged-orchestration:recovery",
            sequence=3,
            safe_summary="Keep downstream recovery visible without background autonomy.",
            status=StagedOrchestrationStatus.skipped,
            step_refs=["step-ref:staged-orchestration:recovery-skipped"],
            checkpoint_refs=[],
            evidence_refs=["evidence-ref:staged-orchestration:recovery"],
        ),
    ]
    steps = [
        StagedOrchestrationStep(
            step_ref="step-ref:staged-orchestration:context-pack",
            stage_ref="stage-ref:staged-orchestration:context",
            safe_summary="Validate safe context refs for staged planning.",
            status=StagedOrchestrationStatus.completed,
            mode=ExecutionStepMode.validation_only,
            callback_refs=[callback],
            policy_ref="policy-ref:staged-orchestration:sealed-default",
            approval_posture_ref="approval-posture-ref:staged-orchestration:no-effect",
            checkpoint_ref="checkpoint-ref:staged-orchestration:context",
            evidence_refs=["evidence-ref:staged-orchestration:context"],
            receipt_refs=["receipt-ref:staged-orchestration:context"],
            execution_ready=True,
        ),
        StagedOrchestrationStep(
            step_ref="step-ref:staged-orchestration:approval-wait",
            stage_ref="stage-ref:staged-orchestration:approval",
            safe_summary="Hold at approval wait with scope binding visible.",
            status=StagedOrchestrationStatus.waiting,
            mode=ExecutionStepMode.receipt_plan_only,
            depends_on_step_refs=["step-ref:staged-orchestration:context-pack"],
            policy_ref="policy-ref:staged-orchestration:exact-scope-required",
            approval_posture_ref="approval-posture-ref:staged-orchestration:operator-wait",
            checkpoint_ref="checkpoint-ref:staged-orchestration:approval",
            evidence_refs=["evidence-ref:staged-orchestration:approval"],
            receipt_refs=["receipt-ref:staged-orchestration:approval"],
            execution_ready=True,
        ),
        StagedOrchestrationStep(
            step_ref="step-ref:staged-orchestration:degraded-review",
            stage_ref="stage-ref:staged-orchestration:approval",
            safe_summary="Create degraded operator handoff when approval scope is incomplete.",
            status=StagedOrchestrationStatus.degraded,
            mode=ExecutionStepMode.validation_only,
            depends_on_step_refs=["step-ref:staged-orchestration:context-pack"],
            policy_ref="policy-ref:staged-orchestration:degraded-handoff",
            approval_posture_ref="approval-posture-ref:staged-orchestration:operator-review",
            checkpoint_ref="checkpoint-ref:staged-orchestration:approval",
            evidence_refs=["evidence-ref:staged-orchestration:degraded-review"],
            receipt_refs=["receipt-ref:staged-orchestration:degraded-review"],
            reason_refs=["reason-ref:staged-orchestration:approval-scope-incomplete"],
            execution_ready=True,
        ),
        StagedOrchestrationStep(
            step_ref="step-ref:staged-orchestration:recovery-skipped",
            stage_ref="stage-ref:staged-orchestration:recovery",
            safe_summary="Skip downstream recovery execution until approval is complete.",
            status=StagedOrchestrationStatus.skipped,
            mode=ExecutionStepMode.background_worker_blocked,
            depends_on_step_refs=["step-ref:staged-orchestration:approval-wait"],
            blocked_authority_refs=[
                "blocked-state:staged-orchestration:no-background-worker",
            ],
            reason_refs=["reason-ref:staged-orchestration:waiting-dependency"],
        ),
    ]
    checkpoints = [
        StagedOrchestrationCheckpoint(
            checkpoint_ref="checkpoint-ref:staged-orchestration:context",
            stage_ref="stage-ref:staged-orchestration:context",
            step_ref="step-ref:staged-orchestration:context-pack",
            sequence=1,
            safe_summary="Checkpoint stores safe context refs only.",
            idempotency_ref="idempotency-ref:staged-orchestration:context",
            replay_ref="replay-ref:staged-orchestration:context",
            evidence_refs=["evidence-ref:staged-orchestration:context"],
            receipt_refs=["receipt-ref:staged-orchestration:context"],
            rollback_refs=["rollback-ref:staged-orchestration:context"],
        ),
        StagedOrchestrationCheckpoint(
            checkpoint_ref="checkpoint-ref:staged-orchestration:approval",
            stage_ref="stage-ref:staged-orchestration:approval",
            step_ref="step-ref:staged-orchestration:approval-wait",
            sequence=2,
            safe_summary="Checkpoint stores approval wait posture only.",
            idempotency_ref="idempotency-ref:staged-orchestration:approval",
            replay_ref="replay-ref:staged-orchestration:approval",
            evidence_refs=["evidence-ref:staged-orchestration:approval"],
            receipt_refs=["receipt-ref:staged-orchestration:approval"],
            rollback_refs=["rollback-ref:staged-orchestration:approval"],
        ),
    ]
    handoffs = [
        StagedOrchestrationDegradedHandoff(
            handoff_ref="handoff-ref:staged-orchestration:operator-review",
            source_step_ref="step-ref:staged-orchestration:degraded-review",
            target_stage_ref="stage-ref:staged-orchestration:approval",
            safe_summary="Operator review required before any future execution lane.",
            reason_refs=["reason-ref:staged-orchestration:approval-scope-incomplete"],
            checkpoint_ref="checkpoint-ref:staged-orchestration:approval",
            evidence_refs=["evidence-ref:staged-orchestration:degraded-review"],
            receipt_refs=["receipt-ref:staged-orchestration:degraded-review"],
        )
    ]
    return StagedOrchestrationPlan(
        plan_ref="plan-ref:staged-orchestration:sample",
        run_ref="run-ref:staged-orchestration:sample",
        turn_run_approval_chain_ref="chain-ref:turn-run-approval:sample",
        route_decision_binding_ref="route-binding-ref:runtime-parity:sample",
        safe_summary="Sample staged orchestration plan with waiting and degraded posture.",
        status=StagedOrchestrationStatus.waiting,
        stages=stages,
        steps=steps,
        checkpoints=checkpoints,
        degraded_handoffs=handoffs,
        evidence_refs=["evidence-ref:staged-orchestration:sample"],
        receipt_refs=["receipt-ref:staged-orchestration:sample"],
    )


def build_sample_staged_orchestration_read_model() -> StagedOrchestrationReadModel:
    return build_staged_orchestration_read_model(build_sample_staged_orchestration_plan())


def _progress_summary(plan: StagedOrchestrationPlan) -> StagedOrchestrationProgressSummary:
    counts = {status.value: 0 for status in StagedOrchestrationStatus}
    for step in plan.steps:
        counts[str(step.status)] += 1
    return StagedOrchestrationProgressSummary(
        total_stage_count=len(plan.stages),
        total_step_count=len(plan.steps),
        pending_count=counts[StagedOrchestrationStatus.pending.value],
        running_count=counts[StagedOrchestrationStatus.running.value],
        waiting_count=counts[StagedOrchestrationStatus.waiting.value],
        degraded_count=counts[StagedOrchestrationStatus.degraded.value],
        skipped_count=counts[StagedOrchestrationStatus.skipped.value],
        blocked_count=counts[StagedOrchestrationStatus.blocked.value],
        failed_count=counts[StagedOrchestrationStatus.failed.value],
        completed_count=counts[StagedOrchestrationStatus.completed.value],
    )


def _dependency_reason_codes(plan: StagedOrchestrationPlan) -> list[str]:
    reasons: list[str] = []
    stage_by_ref = {stage.stage_ref: stage for stage in plan.stages}
    if len(stage_by_ref) != len(plan.stages):
        reasons.append("reason-ref:staged-orchestration:duplicate-stage-ref")
    step_by_ref = {step.step_ref: step for step in plan.steps}
    if len(step_by_ref) != len(plan.steps):
        reasons.append("reason-ref:staged-orchestration:duplicate-step-ref")
    stage_sequence = {stage.stage_ref: stage.sequence for stage in plan.stages}
    for stage in plan.stages:
        for step_ref in stage.step_refs:
            step = step_by_ref.get(step_ref)
            if step is None:
                reasons.append("reason-ref:staged-orchestration:stage-step-missing")
                continue
            if step.stage_ref != stage.stage_ref:
                reasons.append("reason-ref:staged-orchestration:stage-step-mismatch")
        for checkpoint_ref in stage.checkpoint_refs:
            if not any(item.checkpoint_ref == checkpoint_ref for item in plan.checkpoints):
                reasons.append("reason-ref:staged-orchestration:stage-checkpoint-missing")
    failed_or_blocked_steps = {
        step.step_ref
        for step in plan.steps
        if step.status
        in {
            StagedOrchestrationStatus.failed.value,
            StagedOrchestrationStatus.blocked.value,
        }
    }
    for step in plan.steps:
        if step.stage_ref not in stage_by_ref:
            reasons.append("reason-ref:staged-orchestration:step-stage-missing")
        if step.status == StagedOrchestrationStatus.degraded.value and not any(
            handoff.source_step_ref == step.step_ref for handoff in plan.degraded_handoffs
        ):
            reasons.append("reason-ref:staged-orchestration:degraded-handoff-missing")
        if step.execution_ready and not (step.policy_ref and step.approval_posture_ref):
            reasons.append("reason-ref:staged-orchestration:execution-ready-scope-missing")
        step_mode = ExecutionStepMode(step.mode)
        blocked_reason = (
            None
            if step_mode == ExecutionStepMode.approved_runtime_command
            else step_mode_reason(step_mode)
        )
        if blocked_reason is not None and step.execution_ready:
            reasons.append("reason-ref:staged-orchestration:effectful-step-blocked")
        for dependency_ref in step.depends_on_step_refs:
            dependency = step_by_ref.get(dependency_ref)
            if dependency is None:
                reasons.append("reason-ref:staged-orchestration:missing-dependency")
                continue
            dep_sequence = stage_sequence.get(dependency.stage_ref)
            step_sequence = stage_sequence.get(step.stage_ref)
            if dep_sequence is None or step_sequence is None:
                continue
            if dep_sequence == step_sequence:
                reasons.append("reason-ref:staged-orchestration:same-stage-dependency")
            if dep_sequence > step_sequence:
                reasons.append("reason-ref:staged-orchestration:future-stage-dependency")
            if dependency_ref in failed_or_blocked_steps and step.status not in {
                StagedOrchestrationStatus.skipped.value,
                StagedOrchestrationStatus.blocked.value,
                StagedOrchestrationStatus.degraded.value,
            }:
                reasons.append("reason-ref:staged-orchestration:downstream-not-skipped")
    reasons.extend(_cycle_reason_codes(step_by_ref))
    checkpoint_refs = {item.checkpoint_ref for item in plan.checkpoints}
    for step in plan.steps:
        if step.checkpoint_ref and step.checkpoint_ref not in checkpoint_refs:
            reasons.append("reason-ref:staged-orchestration:step-checkpoint-missing")
    for handoff in plan.degraded_handoffs:
        if handoff.source_step_ref not in step_by_ref:
            reasons.append("reason-ref:staged-orchestration:handoff-source-missing")
        if handoff.target_stage_ref not in stage_by_ref:
            reasons.append("reason-ref:staged-orchestration:handoff-stage-missing")
        if handoff.checkpoint_ref not in checkpoint_refs:
            reasons.append("reason-ref:staged-orchestration:handoff-checkpoint-missing")
    return list(dict.fromkeys(reasons))


def _authority_reason_codes(plan: StagedOrchestrationPlan) -> list[str]:
    reasons: list[str] = []
    runtime_steps = [
        step
        for step in plan.steps
        if step.mode == ExecutionStepMode.approved_runtime_command.value
    ]
    if runtime_steps and not plan.approved_runtime_command_execution_enabled:
        reasons.append("reason-ref:staged-orchestration:runtime-plan-enable-required")
    if plan.approved_runtime_command_execution_enabled:
        if plan.no_effect:
            reasons.append("reason-ref:staged-orchestration:runtime-plan-no-effect-drift")
        if not runtime_steps:
            reasons.append("reason-ref:staged-orchestration:runtime-step-required")
    if not plan.no_effect and not plan.approved_runtime_command_execution_enabled:
        reasons.append("reason-ref:staged-orchestration:runtime-authority-not-promoted")
    if plan.background_autonomy_enabled:
        reasons.append("reason-ref:staged-orchestration:background-autonomy-denied")
    if plan.provider_model_call_enabled:
        reasons.append("reason-ref:staged-orchestration:provider-model-call-denied")
    if plan.unrestricted_command_execution_enabled:
        reasons.append("reason-ref:staged-orchestration:unrestricted-command-denied")

    for step in plan.steps:
        mode = ExecutionStepMode(step.mode)
        binding = step.runtime_command_binding
        if mode == ExecutionStepMode.approved_runtime_command:
            if binding is None:
                reasons.append("reason-ref:staged-orchestration:runtime-binding-required")
            if not step.execution_ready:
                reasons.append("reason-ref:staged-orchestration:runtime-step-not-ready")
            if binding is not None:
                if (
                    binding.authority_ref
                    != STAGED_ORCHESTRATION_APPROVED_RUNTIME_STEP_AUTHORITY_REF
                ):
                    reasons.append(
                        "reason-ref:staged-orchestration:runtime-binding-authority-required"
                    )
                if (
                    str(binding.command_intent)
                    not in STAGED_ORCHESTRATION_APPROVED_RUNTIME_COMMAND_PROMOTED_INTENTS
                ):
                    reasons.append(
                        "reason-ref:staged-orchestration:runtime-command-intent-not-promoted"
                    )
            continue
        if binding is not None:
            reasons.append("reason-ref:staged-orchestration:runtime-binding-mode-required")
    return list(dict.fromkeys(reasons))


def _cycle_reason_codes(steps: dict[str, StagedOrchestrationStep]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_ref: str) -> bool:
        if step_ref in visiting:
            return True
        if step_ref in visited:
            return False
        visiting.add(step_ref)
        step = steps.get(step_ref)
        if step is None:
            visiting.remove(step_ref)
            return False
        for dependency_ref in step.depends_on_step_refs:
            if dependency_ref in steps and visit(dependency_ref):
                return True
        visiting.remove(step_ref)
        visited.add(step_ref)
        return False

    for step_ref in steps:
        if visit(step_ref):
            return ["reason-ref:staged-orchestration:dependency-cycle"]
    return []
