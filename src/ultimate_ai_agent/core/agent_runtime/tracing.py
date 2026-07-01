from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.agent_runtime.contracts import _validate_safe_ref, _validate_safe_text


class AgentRuntimeTraceStatus(str, Enum):
    planned = "planned"
    no_effect_completed = "no_effect_completed"
    denied = "denied"
    failed_safely = "failed_safely"


class _TraceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AgentRuntimeTraceEvent(_TraceModel):
    event_ref: str
    trace_ref: str
    safe_summary: str = Field(..., min_length=1)
    status: AgentRuntimeTraceStatus = AgentRuntimeTraceStatus.planned
    policy_status_ref: str
    approval_status_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    @field_validator("event_ref", "trace_ref", "policy_status_ref", "approval_status_ref")
    @classmethod
    def validate_ref_fields(cls, value: str) -> str:
        _validate_safe_ref(value, "trace_event_ref")
        return value

    @field_validator("evidence_refs", "receipt_refs", "blocked_authority_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "trace_event_ref")
        return values

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_summary")
        return value


class AgentRuntimeTraceSpan(_TraceModel):
    trace_ref: str
    span_ref: str
    parent_trace_ref: str | None = None
    capability_ref: str
    safe_summary: str = Field(..., min_length=1)
    timing_class: str = "unknown"
    result_status: AgentRuntimeTraceStatus = AgentRuntimeTraceStatus.planned
    policy_status_ref: str
    approval_status_ref: str
    events: list[AgentRuntimeTraceEvent] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    uaa_canonical: bool = True

    @field_validator("trace_ref", "span_ref", "parent_trace_ref", "capability_ref", "policy_status_ref", "approval_status_ref")
    @classmethod
    def validate_ref_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value
        _validate_safe_ref(value, "trace_span_ref")
        return value

    @field_validator("evidence_refs", "receipt_refs", "blocked_authority_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "trace_span_ref")
        return values

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_summary")
        return value

    @model_validator(mode="after")
    def validate_canonical_trace(self) -> "AgentRuntimeTraceSpan":
        if not self.uaa_canonical:
            raise ValueError("AGENT_RUNTIME_UAA_TRACE_CANONICAL_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("AGENT_RUNTIME_BLOCKED_AUTHORITY_REFS_REQUIRED")
        return self


class AgentRuntimeImportedVendorTrace(_TraceModel):
    import_ref: str
    uaa_trace_ref: str
    vendor_trace_ref: str
    safe_summary: str = Field(..., min_length=1)
    imported_as_evidence_only: bool = True
    authority_granted: bool = False
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("import_ref", "uaa_trace_ref", "vendor_trace_ref")
    @classmethod
    def validate_ref_fields(cls, value: str) -> str:
        _validate_safe_ref(value, "imported_vendor_trace_ref")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "imported_vendor_trace_ref")
        return values

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_summary")
        return value

    @model_validator(mode="after")
    def validate_evidence_only(self) -> "AgentRuntimeImportedVendorTrace":
        if not self.imported_as_evidence_only or self.authority_granted:
            raise ValueError("VENDOR_TRACE_AUTHORITY_DENIED")
        return self


class AgentRuntimeReceiptPlan(_TraceModel):
    receipt_plan_ref: str
    trace_ref: str
    safe_summary: str = Field(..., min_length=1)
    uaa_receipt_required: bool = True
    vendor_trace_receipt_is_canonical: bool = False
    execution_performed: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    @field_validator("receipt_plan_ref", "trace_ref")
    @classmethod
    def validate_ref_fields(cls, value: str) -> str:
        _validate_safe_ref(value, "agent_runtime_receipt_plan_ref")
        return value

    @field_validator("evidence_refs", "blocked_authority_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "agent_runtime_receipt_plan_ref")
        return values

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_summary")
        return value

    @model_validator(mode="after")
    def validate_receipt_plan(self) -> "AgentRuntimeReceiptPlan":
        if not self.uaa_receipt_required:
            raise ValueError("UAA_RECEIPT_REQUIRED")
        if self.vendor_trace_receipt_is_canonical or self.execution_performed:
            raise ValueError("AGENT_RUNTIME_RECEIPT_AUTHORITY_DENIED")
        return self
