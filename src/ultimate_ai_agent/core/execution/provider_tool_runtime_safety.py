from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.execution.validation import (
    dedupe_reasons,
    validate_execution_ref,
    validate_safe_execution_text,
)


PROVIDER_TOOL_RUNTIME_INVOCATION_SCHEMA_VERSION = "provider_tool_runtime_invocation_contract.v1"
PROVIDER_TOOL_RUNTIME_RESULT_SCHEMA_VERSION = "provider_tool_runtime_result_contract.v1"
PROVIDER_TOOL_RUNTIME_STREAM_EVENT_SCHEMA_VERSION = "provider_tool_runtime_stream_event_contract.v1"
PROVIDER_TOOL_RUNTIME_VALIDATION_SCHEMA_VERSION = "provider_tool_runtime_validation_decision.v1"
PROVIDER_TOOL_RUNTIME_REPLAY_SCHEMA_VERSION = "provider_tool_runtime_replay_sanitized.v1"

ProviderToolRuntimeTargetKind = Literal["provider", "tool"]
ProviderToolRuntimeResultStatus = Literal[
    "blocked",
    "validation_failed",
    "approval_required",
    "cost_blocked",
    "redacted_result_ready",
    "failed",
    "canceled",
]
ProviderToolRuntimeStreamEventType = Literal[
    "stream_started",
    "stream_delta_redacted",
    "stream_heartbeat",
    "stream_completed",
    "stream_failed",
    "stream_canceled",
    "stream_redaction_applied",
]
ProviderToolRuntimeValidationStatus = Literal[
    "valid_contract_only",
    "blocked",
    "validation_failed",
    "approval_required",
    "cost_blocked",
]
ProviderToolRuntimeTerminalStreamEventType = Literal["stream_completed", "stream_failed", "stream_canceled"]


class _ProviderToolRuntimeContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True, validate_assignment=True)

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return type(self).model_validate(copied.model_dump(mode="python"))

_RAW_PAYLOAD_FIELD_RE = re.compile(
    r"(?i)(^|[_-])("
    r"raw|prompt|response|provider[_-]?payload|tool[_-]?payload|payload|"
    r"local[_-]?path|env[_-]?dump|credential|cookie|token|secret|api[_-]?key|"
    r"password|username|hostname|file[_-]?content|raw[_-]?chunk|raw[_-]?text"
    r")($|[_-])"
)
_RAW_PAYLOAD_VALUE_RE = re.compile(
    r"(?i)(raw\s+(prompt|response|chunk|text|payload|local\s+path|file\s+content)|"
    r"provider[\s_-]?payload|tool[\s_-]?payload|env[\s_-]?dump|"
    r"credential|secret|api[_-]?key|bearer\s+|cookie|token|/Users/|/home/|"
    r"-----BEGIN)"
)


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_optional_ref(value: str | None, field_name: str) -> None:
    if value is not None:
        _validate_ref(value, field_name)


def _validate_ref_list(values: Sequence[str], field_name: str) -> None:
    for value in values:
        _validate_ref(value, field_name)


def _scan_raw_payload_like_fields(value: Any, path: str = "payload") -> list[str]:
    reasons: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _RAW_PAYLOAD_FIELD_RE.search(key_text):
                reasons.append("RAW_PAYLOAD_LIKE_FIELD_BLOCKED")
            reasons.extend(_scan_raw_payload_like_fields(item, f"{path}.{key_text}"))
        return dedupe_reasons(reasons)
    if isinstance(value, list):
        for index, item in enumerate(value):
            reasons.extend(_scan_raw_payload_like_fields(item, f"{path}[{index}]"))
        return dedupe_reasons(reasons)
    if isinstance(value, str) and _RAW_PAYLOAD_VALUE_RE.search(value):
        reasons.append("RAW_PAYLOAD_LIKE_VALUE_BLOCKED")
    return dedupe_reasons(reasons)


def _validate_safe_contract_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    raw_reasons = _scan_raw_payload_like_fields(value, field_name)
    if raw_reasons:
        raise ValueError(f"{field_name.upper()}_RAW_PAYLOAD_LIKE_VALUE_BLOCKED")


def _missing_required_reasons(payload: Mapping[str, Any]) -> list[str]:
    checks = {
        "run_ref": "MISSING_RUN_REF_BLOCKED",
        "exact_approval_scope_ref": "MISSING_EXACT_APPROVAL_BLOCKED",
        "approval_ref": "MISSING_EXACT_APPROVAL_BLOCKED",
        "idempotency_ref": "MISSING_IDEMPOTENCY_REF_BLOCKED",
        "cost_estimate_ref": "MISSING_COST_ESTIMATE_REF_BLOCKED",
        "redaction_posture_ref": "MISSING_REDACTION_POSTURE_REF_BLOCKED",
    }
    return dedupe_reasons([reason for key, reason in checks.items() if not payload.get(key)])


class ProviderToolRuntimeInvocationEnvelope(_ProviderToolRuntimeContractModel):
    schema_version: str = PROVIDER_TOOL_RUNTIME_INVOCATION_SCHEMA_VERSION
    run_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    target_kind: ProviderToolRuntimeTargetKind
    provider_ref: str | None = None
    tool_ref: str | None = None
    exact_approval_scope_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    redacted_input_ref: str = Field(..., min_length=1)
    expected_result_schema_ref: str = Field(..., min_length=1)
    cost_estimate_ref: str = Field(..., min_length=1)
    max_approved_usd_ref: str = Field(..., min_length=1)
    privacy_posture_ref: str = Field(..., min_length=1)
    replay_posture_ref: str = Field(..., min_length=1)
    rollback_posture_ref: str = Field(..., min_length=1)
    safe_disable_posture_ref: str = Field(..., min_length=1)
    redaction_posture_ref: str = Field(..., min_length=1)
    authority_boundary_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(
        default="Contract-only provider/tool runtime invocation envelope; no execution authority is granted.",
        min_length=1,
    )
    runtime_activation_enabled: bool = False
    provider_model_calls_enabled: bool = False
    provider_sdk_calls_enabled: bool = False
    tool_execution_expansion_enabled: bool = False
    connector_writes_enabled: bool = False
    background_worker_enabled: bool = False
    billing_authority_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_invocation_envelope(self) -> Any:
        refs = [
            (self.run_ref, "run_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.exact_approval_scope_ref, "exact_approval_scope_ref"),
            (self.approval_ref, "approval_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.redacted_input_ref, "redacted_input_ref"),
            (self.expected_result_schema_ref, "expected_result_schema_ref"),
            (self.cost_estimate_ref, "cost_estimate_ref"),
            (self.max_approved_usd_ref, "max_approved_usd_ref"),
            (self.privacy_posture_ref, "privacy_posture_ref"),
            (self.replay_posture_ref, "replay_posture_ref"),
            (self.rollback_posture_ref, "rollback_posture_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
            (self.redaction_posture_ref, "redaction_posture_ref"),
        ]
        for value, field_name in refs:
            _validate_ref(value, field_name)
        _validate_optional_ref(self.provider_ref, "provider_ref")
        _validate_optional_ref(self.tool_ref, "tool_ref")
        _validate_ref_list(self.authority_boundary_refs, "authority_boundary_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_safe_contract_text(self.safe_summary, "safe_summary")
        if self.target_kind == "provider" and not self.provider_ref:
            raise ValueError("PROVIDER_REF_REQUIRED")
        if self.target_kind == "tool" and not self.tool_ref:
            raise ValueError("TOOL_REF_REQUIRED")
        if self.target_kind == "provider" and self.tool_ref:
            raise ValueError("PROVIDER_ENVELOPE_MUST_NOT_SET_TOOL_REF")
        if self.target_kind == "tool" and self.provider_ref:
            raise ValueError("TOOL_ENVELOPE_MUST_NOT_SET_PROVIDER_REF")
        if not self.authority_boundary_refs:
            raise ValueError("AUTHORITY_BOUNDARY_REF_REQUIRED")
        denied_flags = [
            self.runtime_activation_enabled,
            self.provider_model_calls_enabled,
            self.provider_sdk_calls_enabled,
            self.tool_execution_expansion_enabled,
            self.connector_writes_enabled,
            self.background_worker_enabled,
            self.billing_authority_enabled,
            self.production_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_TOOL_RUNTIME_AUTHORITY_DENIED")
        return self


class ProviderToolRuntimeResultContract(_ProviderToolRuntimeContractModel):
    schema_version: str = PROVIDER_TOOL_RUNTIME_RESULT_SCHEMA_VERSION
    run_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    status: ProviderToolRuntimeResultStatus
    redacted_output_ref: str | None = None
    usage_receipt_refs: list[str] = Field(default_factory=list)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    error_safe_summary_ref: str | None = None
    safe_summary: str = Field(..., min_length=1)
    execution_performed: bool = False
    provider_model_called: bool = False
    provider_sdk_used: bool = False
    tool_executed: bool = False
    connector_write_performed: bool = False

    @model_validator(mode="after")
    def validate_result_contract(self) -> Any:
        _validate_ref(self.run_ref, "run_ref")
        _validate_ref(self.invocation_ref, "invocation_ref")
        _validate_optional_ref(self.redacted_output_ref, "redacted_output_ref")
        _validate_optional_ref(self.error_safe_summary_ref, "error_safe_summary_ref")
        _validate_ref_list(self.usage_receipt_refs, "usage_receipt_refs")
        _validate_ref_list(self.cost_receipt_refs, "cost_receipt_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_safe_contract_text(self.safe_summary, "safe_summary")
        if self.status == "redacted_result_ready" and not self.redacted_output_ref:
            raise ValueError("REDACTED_OUTPUT_REF_REQUIRED")
        denied_flags = [
            self.execution_performed,
            self.provider_model_called,
            self.provider_sdk_used,
            self.tool_executed,
            self.connector_write_performed,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_TOOL_RESULT_EXECUTION_AUTHORITY_DENIED")
        return self


class ProviderToolRuntimeStreamEventContract(_ProviderToolRuntimeContractModel):
    schema_version: str = PROVIDER_TOOL_RUNTIME_STREAM_EVENT_SCHEMA_VERSION
    run_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    sequence: int = Field(..., ge=1)
    event_type: ProviderToolRuntimeStreamEventType
    durable_run_event_ref: str = Field(..., min_length=1)
    redacted_delta_ref: str | None = None
    heartbeat_ref: str | None = None
    redaction_posture_ref: str | None = None
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    ordered_under_durable_run_event_log: bool = True
    live_streaming_runtime_enabled: bool = False
    provider_stream_called: bool = False
    tool_stream_called: bool = False

    @model_validator(mode="after")
    def validate_stream_event(self) -> Any:
        _validate_ref(self.run_ref, "run_ref")
        _validate_ref(self.invocation_ref, "invocation_ref")
        _validate_ref(self.durable_run_event_ref, "durable_run_event_ref")
        _validate_optional_ref(self.redacted_delta_ref, "redacted_delta_ref")
        _validate_optional_ref(self.heartbeat_ref, "heartbeat_ref")
        _validate_optional_ref(self.redaction_posture_ref, "redaction_posture_ref")
        _validate_ref_list(self.receipt_refs, "receipt_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_safe_contract_text(self.safe_summary, "safe_summary")
        if self.event_type == "stream_delta_redacted" and not self.redacted_delta_ref:
            raise ValueError("REDACTED_DELTA_REF_REQUIRED")
        if self.event_type == "stream_heartbeat" and not self.heartbeat_ref:
            raise ValueError("HEARTBEAT_REF_REQUIRED")
        if self.event_type == "stream_redaction_applied" and not self.redaction_posture_ref:
            raise ValueError("REDACTION_POSTURE_REF_REQUIRED")
        if not self.ordered_under_durable_run_event_log:
            raise ValueError("STREAM_EVENT_MUST_BE_DURABLE_RUN_ORDERED")
        if self.live_streaming_runtime_enabled or self.provider_stream_called or self.tool_stream_called:
            raise ValueError("STREAM_RUNTIME_AUTHORITY_DENIED")
        return self


class ProviderToolRuntimeValidationContext(_ProviderToolRuntimeContractModel):
    known_provider_refs: list[str] = Field(default_factory=list)
    known_tool_refs: list[str] = Field(default_factory=list)
    local_approval_authority_decision_ref: str | None = None
    approval_grant_ref: str | None = None
    approved_scope_ref: str | None = None
    cost_governor_decision_ref: str | None = None
    budget_decision_ref: str | None = None
    cost_estimate_ref: str | None = None
    max_approved_usd_ref: str | None = None
    paid_cost_posture_ref: str | None = None
    actual_cost_receipt_ref: str | None = None
    paid_cost_known: bool = True
    actual_cost_complete: bool = True

    @model_validator(mode="after")
    def validate_context_refs(self) -> Any:
        _validate_ref_list(self.known_provider_refs, "known_provider_refs")
        _validate_ref_list(self.known_tool_refs, "known_tool_refs")
        _validate_optional_ref(self.local_approval_authority_decision_ref, "local_approval_authority_decision_ref")
        _validate_optional_ref(self.approval_grant_ref, "approval_grant_ref")
        _validate_optional_ref(self.approved_scope_ref, "approved_scope_ref")
        _validate_optional_ref(self.cost_governor_decision_ref, "cost_governor_decision_ref")
        _validate_optional_ref(self.budget_decision_ref, "budget_decision_ref")
        _validate_optional_ref(self.cost_estimate_ref, "cost_estimate_ref")
        _validate_optional_ref(self.max_approved_usd_ref, "max_approved_usd_ref")
        _validate_optional_ref(self.paid_cost_posture_ref, "paid_cost_posture_ref")
        _validate_optional_ref(self.actual_cost_receipt_ref, "actual_cost_receipt_ref")
        return self


class ProviderToolRuntimeValidationDecision(_ProviderToolRuntimeContractModel):
    schema_version: str = PROVIDER_TOOL_RUNTIME_VALIDATION_SCHEMA_VERSION
    validation_status: ProviderToolRuntimeValidationStatus
    contract_valid: bool = False
    blocked: bool = True
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    invocation_ref: str | None = None
    execution_permitted: bool = False
    execution_performed: bool = False
    runtime_activation_enabled: bool = False

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        _validate_optional_ref(self.invocation_ref, "invocation_ref")
        _validate_safe_contract_text(self.safe_message, "safe_message")
        if self.execution_permitted or self.execution_performed or self.runtime_activation_enabled:
            raise ValueError("VALIDATION_DECISION_MUST_NOT_GRANT_RUNTIME_AUTHORITY")
        if self.validation_status == "valid_contract_only" and (self.blocked or not self.contract_valid):
            raise ValueError("VALID_CONTRACT_DECISION_SHAPE_DENIED")
        if self.validation_status != "valid_contract_only" and not self.blocked:
            raise ValueError("BLOCKED_DECISION_SHAPE_DENIED")
        return self


class ProviderToolRuntimeSanitizedReplay(_ProviderToolRuntimeContractModel):
    schema_version: str = PROVIDER_TOOL_RUNTIME_REPLAY_SCHEMA_VERSION
    run_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    target_kind: ProviderToolRuntimeTargetKind
    target_ref: str = Field(..., min_length=1)
    result_status: ProviderToolRuntimeResultStatus | None = None
    stream_event_count: int = Field(default=0, ge=0)
    stream_sequence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    redacted_refs: list[str] = Field(default_factory=list)
    safe_summary: str = "Sanitized provider/tool runtime replay contains safe refs only."
    safe_refs_only: bool = True
    raw_content_omitted: bool = True
    execution_performed: bool = False

    @model_validator(mode="after")
    def validate_replay(self) -> Any:
        _validate_ref(self.run_ref, "run_ref")
        _validate_ref(self.invocation_ref, "invocation_ref")
        _validate_ref(self.target_ref, "target_ref")
        _validate_ref_list(self.stream_sequence_refs, "stream_sequence_refs")
        _validate_ref_list(self.receipt_refs, "receipt_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.redacted_refs, "redacted_refs")
        _validate_safe_contract_text(self.safe_summary, "safe_summary")
        if not self.safe_refs_only or not self.raw_content_omitted or self.execution_performed:
            raise ValueError("SANITIZED_REPLAY_AUTHORITY_DENIED")
        return self


def _decision(
    status: ProviderToolRuntimeValidationStatus,
    reason_codes: Sequence[str],
    safe_message: str,
    invocation_ref: str | None = None,
    contract_valid: bool = False,
) -> ProviderToolRuntimeValidationDecision:
    return ProviderToolRuntimeValidationDecision(
        validation_status=status,
        contract_valid=contract_valid,
        blocked=status != "valid_contract_only",
        reason_codes=dedupe_reasons(list(reason_codes)),
        safe_message=safe_message,
        invocation_ref=invocation_ref,
    )


def validate_provider_tool_runtime_invocation(
    payload: ProviderToolRuntimeInvocationEnvelope | Mapping[str, Any],
    context: ProviderToolRuntimeValidationContext | Mapping[str, Any] | None = None,
) -> ProviderToolRuntimeValidationDecision:
    raw_mapping = payload.model_dump(mode="json") if isinstance(payload, ProviderToolRuntimeInvocationEnvelope) else payload
    if isinstance(raw_mapping, Mapping):
        raw_reasons = _scan_raw_payload_like_fields(raw_mapping)
        if raw_reasons:
            return _decision(
                "blocked",
                raw_reasons,
                "Provider/tool runtime invocation contract contains raw-payload-like fields and is blocked.",
            )
        missing_reasons = _missing_required_reasons(raw_mapping)
        if missing_reasons:
            status: ProviderToolRuntimeValidationStatus = (
                "approval_required" if "MISSING_EXACT_APPROVAL_BLOCKED" in missing_reasons else "blocked"
            )
            if "MISSING_COST_ESTIMATE_REF_BLOCKED" in missing_reasons:
                status = "cost_blocked"
            return _decision(status, missing_reasons, "Provider/tool runtime invocation contract is missing required refs.")
    try:
        envelope = (
            payload
            if isinstance(payload, ProviderToolRuntimeInvocationEnvelope)
            else ProviderToolRuntimeInvocationEnvelope.model_validate(payload)
        )
        validation_context = (
            ProviderToolRuntimeValidationContext()
            if context is None
            else (
                context
                if isinstance(context, ProviderToolRuntimeValidationContext)
                else ProviderToolRuntimeValidationContext.model_validate(context)
            )
        )
    except (TypeError, ValueError, ValidationError) as exc:
        return _decision(
            "validation_failed",
            ["PROVIDER_TOOL_RUNTIME_CONTRACT_VALIDATION_FAILED"],
            f"Provider/tool runtime invocation contract failed validation: {exc.__class__.__name__}.",
        )

    reasons: list[str] = []
    target_ref = envelope.provider_ref if envelope.target_kind == "provider" else envelope.tool_ref
    known_refs = validation_context.known_provider_refs if envelope.target_kind == "provider" else validation_context.known_tool_refs
    unknown_reason = "UNKNOWN_PROVIDER_BLOCKED" if envelope.target_kind == "provider" else "UNKNOWN_TOOL_BLOCKED"
    if target_ref not in set(known_refs):
        reasons.append(unknown_reason)
    if (
        not validation_context.local_approval_authority_decision_ref
        or not validation_context.approval_grant_ref
        or not validation_context.approved_scope_ref
    ):
        reasons.append("EXACT_APPROVAL_SCOPE_NOT_VALIDATED_BLOCKED")
    if (
        validation_context.approval_grant_ref
        and validation_context.approval_grant_ref != envelope.approval_ref
    ) or (
        validation_context.approved_scope_ref
        and validation_context.approved_scope_ref != envelope.exact_approval_scope_ref
    ):
        reasons.append("APPROVAL_SCOPE_MISMATCH_BLOCKED")
    if (
        not validation_context.cost_governor_decision_ref
        or not validation_context.budget_decision_ref
        or not validation_context.cost_estimate_ref
        or validation_context.cost_estimate_ref != envelope.cost_estimate_ref
        or not validation_context.max_approved_usd_ref
        or validation_context.max_approved_usd_ref != envelope.max_approved_usd_ref
    ):
        reasons.append("COST_GOVERNOR_DECISION_REF_REQUIRED_BLOCKED")
    if not validation_context.paid_cost_known or not validation_context.paid_cost_posture_ref:
        reasons.append("UNKNOWN_PAID_COST_BLOCKED")
    if not validation_context.actual_cost_complete or not validation_context.actual_cost_receipt_ref:
        reasons.append("INCOMPLETE_ACTUAL_COST_BLOCKED")

    if reasons:
        if any(
            reason in reasons
            for reason in [
                "COST_GOVERNOR_DECISION_REF_REQUIRED_BLOCKED",
                "UNKNOWN_PAID_COST_BLOCKED",
                "INCOMPLETE_ACTUAL_COST_BLOCKED",
            ]
        ):
            status = "cost_blocked"
        elif any(reason in reasons for reason in ["EXACT_APPROVAL_SCOPE_NOT_VALIDATED_BLOCKED"]):
            status = "approval_required"
        else:
            status = "blocked"
        return _decision(
            status,
            reasons,
            "Provider/tool runtime invocation contract is blocked before execution authority.",
            envelope.invocation_ref,
        )

    return _decision(
        "valid_contract_only",
        ["CONTRACT_VALID_NO_EXECUTION"],
        "Provider/tool runtime invocation contract is valid as metadata only; execution remains disabled.",
        envelope.invocation_ref,
        contract_valid=True,
    )


def validate_provider_tool_stream_events(
    events: Sequence[ProviderToolRuntimeStreamEventContract | Mapping[str, Any]],
) -> ProviderToolRuntimeValidationDecision:
    parsed_events: list[ProviderToolRuntimeStreamEventContract] = []
    try:
        for event in events:
            parsed_events.append(
                event
                if isinstance(event, ProviderToolRuntimeStreamEventContract)
                else ProviderToolRuntimeStreamEventContract.model_validate(event)
            )
    except (TypeError, ValueError, ValidationError) as exc:
        return _decision(
            "validation_failed",
            ["PROVIDER_TOOL_STREAM_EVENT_VALIDATION_FAILED"],
            f"Provider/tool stream event contract failed validation: {exc.__class__.__name__}.",
        )
    if not parsed_events:
        return _decision("blocked", ["STREAM_EVENTS_REQUIRED"], "At least one stream event ref is required.")

    reasons: list[str] = []
    sequence_values = [event.sequence for event in parsed_events]
    expected_sequence_values = list(range(1, len(parsed_events) + 1))
    if sequence_values != expected_sequence_values:
        reasons.append("STREAM_EVENT_SEQUENCE_NOT_MONOTONIC")
    durable_run_event_refs = [event.durable_run_event_ref for event in parsed_events]
    if len(durable_run_event_refs) != len(set(durable_run_event_refs)):
        reasons.append("STREAM_EVENT_DURABLE_RUN_EVENT_REF_DUPLICATE")
    if parsed_events[0].event_type != "stream_started":
        reasons.append("STREAM_STARTED_EVENT_REQUIRED")
    terminal_event_types: set[ProviderToolRuntimeTerminalStreamEventType] = {
        "stream_completed",
        "stream_failed",
        "stream_canceled",
    }
    terminal_indexes = [
        index for index, event in enumerate(parsed_events) if event.event_type in terminal_event_types
    ]
    if len(terminal_indexes) > 1:
        reasons.append("STREAM_TERMINAL_EVENT_DUPLICATE")
    if terminal_indexes and terminal_indexes[0] != len(parsed_events) - 1:
        reasons.append("STREAM_TERMINAL_EVENT_MUST_BE_LAST")
    run_refs = {event.run_ref for event in parsed_events}
    invocation_refs = {event.invocation_ref for event in parsed_events}
    if len(run_refs) != 1:
        reasons.append("STREAM_EVENT_RUN_REF_MISMATCH")
    if len(invocation_refs) != 1:
        reasons.append("STREAM_EVENT_INVOCATION_REF_MISMATCH")
    if reasons:
        return _decision(
            "blocked",
            reasons,
            "Provider/tool stream event contracts are blocked until ordering and refs are consistent.",
            parsed_events[0].invocation_ref,
        )
    return _decision(
        "valid_contract_only",
        ["STREAM_EVENTS_ORDERED_UNDER_DURABLE_RUN_LOG"],
        "Provider/tool stream event contracts are ordered metadata only; live streaming remains disabled.",
        parsed_events[0].invocation_ref,
        contract_valid=True,
    )


def sanitize_provider_tool_runtime_replay(
    envelope: ProviderToolRuntimeInvocationEnvelope,
    result: ProviderToolRuntimeResultContract | None = None,
    stream_events: Sequence[ProviderToolRuntimeStreamEventContract] = (),
) -> ProviderToolRuntimeSanitizedReplay:
    target_ref = envelope.provider_ref if envelope.target_kind == "provider" else envelope.tool_ref
    assert target_ref is not None
    receipt_refs: list[str] = []
    evidence_refs: list[str] = list(envelope.evidence_refs)
    redacted_refs = [envelope.redacted_input_ref]
    if result is not None:
        if result.run_ref != envelope.run_ref or result.invocation_ref != envelope.invocation_ref:
            raise ValueError("PROVIDER_TOOL_REPLAY_RESULT_REF_MISMATCH")
        receipt_refs.extend(result.usage_receipt_refs)
        receipt_refs.extend(result.cost_receipt_refs)
        evidence_refs.extend(result.evidence_refs)
        if result.redacted_output_ref:
            redacted_refs.append(result.redacted_output_ref)
    if stream_events:
        stream_decision = validate_provider_tool_stream_events(stream_events)
        if stream_decision.blocked or stream_decision.validation_status != "valid_contract_only":
            raise ValueError("PROVIDER_TOOL_REPLAY_STREAM_EVENTS_INVALID")
    for event in stream_events:
        if event.run_ref != envelope.run_ref or event.invocation_ref != envelope.invocation_ref:
            raise ValueError("PROVIDER_TOOL_REPLAY_STREAM_REF_MISMATCH")
        receipt_refs.extend(event.receipt_refs)
        evidence_refs.extend(event.evidence_refs)
        if event.redacted_delta_ref:
            redacted_refs.append(event.redacted_delta_ref)
    return ProviderToolRuntimeSanitizedReplay(
        run_ref=envelope.run_ref,
        invocation_ref=envelope.invocation_ref,
        target_kind=envelope.target_kind,
        target_ref=target_ref,
        result_status=None if result is None else result.status,
        stream_event_count=len(stream_events),
        stream_sequence_refs=[
            f"stream-sequence-ref:{event.run_ref.split(':')[-1]}:{event.invocation_ref.split(':')[-1]}:{event.sequence}"
            for event in stream_events
        ],
        receipt_refs=dedupe_reasons(receipt_refs),
        evidence_refs=dedupe_reasons(evidence_refs),
        redacted_refs=dedupe_reasons(redacted_refs),
    )
