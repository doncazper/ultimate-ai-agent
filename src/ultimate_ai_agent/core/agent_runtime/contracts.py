from __future__ import annotations

import re
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
FORBIDDEN_SAFE_TEXT_FRAGMENTS = (
    "raw" "_prompt",
    "raw" "_response",
    "raw" "_provider_payload",
    "raw" "_path",
    "raw" "_log",
    "environment" "_dump",
    "credential" "_material",
    "api_key=",
    "token=",
    "-----BEGIN",
    "/Users/",
)


class AgentRuntimeKind(str, Enum):
    deterministic_local = "deterministic_local"
    local_model = "local_model"
    openai_agents_sdk = "openai_agents_sdk"
    anthropic_style = "anthropic_style"
    gemini_style = "gemini_style"
    codex = "codex"
    claude_code = "claude_code"
    external_framework = "external_framework"
    unknown = "unknown"


class AgentRuntimeDecisionStatus(str, Enum):
    no_effect_ready = "no_effect_ready"
    denied = "denied"
    blocked = "blocked"


class _AgentRuntimeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AgentRuntimeAuthorityPosture(_AgentRuntimeModel):
    policy_engine_required: bool = True
    local_approval_authority_required: bool = True
    uaa_receipts_required: bool = True
    uaa_audit_required: bool = True
    adapter_output_is_authority: bool = False
    execution_authorized: bool = False
    provider_runtime_authorized: bool = False
    network_authorized: bool = False
    browser_automation_authorized: bool = False
    shell_execution_authorized: bool = False
    connector_write_authorized: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False

    @model_validator(mode="after")
    def validate_no_runtime_authority(self) -> "AgentRuntimeAuthorityPosture":
        denied_flags = {
            "adapter_output_is_authority": self.adapter_output_is_authority,
            "execution_authorized": self.execution_authorized,
            "provider_runtime_authorized": self.provider_runtime_authorized,
            "network_authorized": self.network_authorized,
            "browser_automation_authorized": self.browser_automation_authorized,
            "shell_execution_authorized": self.shell_execution_authorized,
            "connector_write_authorized": self.connector_write_authorized,
            "memory_write_authorized": self.memory_write_authorized,
            "context_injection_authorized": self.context_injection_authorized,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"AGENT_RUNTIME_AUTHORITY_DENIED: {', '.join(enabled)}")
        if not self.policy_engine_required or not self.local_approval_authority_required:
            raise ValueError("AGENT_RUNTIME_CORE_AUTHORITY_REQUIRED")
        if not self.uaa_receipts_required or not self.uaa_audit_required:
            raise ValueError("AGENT_RUNTIME_RECEIPT_AUDIT_REQUIRED")
        return self


class AgentRuntimeTraceRef(_AgentRuntimeModel):
    trace_ref: str
    vendor_trace_ref: str | None = None
    uaa_canonical: bool = True

    @field_validator("trace_ref", "vendor_trace_ref")
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        if value is None:
            return value
        _validate_safe_ref(value, "trace_ref")
        return value

    @model_validator(mode="after")
    def validate_canonical_trace(self) -> "AgentRuntimeTraceRef":
        if not self.uaa_canonical:
            raise ValueError("AGENT_RUNTIME_UAA_TRACE_CANONICAL_REQUIRED")
        return self


class AgentRuntimeRequest(_AgentRuntimeModel):
    request_ref: str
    adapter_ref: str
    runtime_kind: AgentRuntimeKind
    capability_ref: str
    safe_objective_summary: str = Field(..., min_length=1)
    safe_input_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    approval_ref: str | None = None
    idempotency_ref: str | None = None
    authority_posture: AgentRuntimeAuthorityPosture = Field(default_factory=AgentRuntimeAuthorityPosture)

    @field_validator("request_ref", "adapter_ref", "capability_ref", "approval_ref", "idempotency_ref")
    @classmethod
    def validate_ref_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value
        _validate_safe_ref(value, "agent_runtime_ref")
        return value

    @field_validator("safe_input_refs", "evidence_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "agent_runtime_ref")
        return values

    @field_validator("safe_objective_summary")
    @classmethod
    def validate_safe_objective_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_objective_summary")
        return value


class AgentRuntimeDecision(_AgentRuntimeModel):
    decision_ref: str
    request_ref: str
    adapter_ref: str
    runtime_kind: AgentRuntimeKind
    status: AgentRuntimeDecisionStatus = AgentRuntimeDecisionStatus.no_effect_ready
    safe_summary: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=lambda: ["AGENT_RUNTIME_CONTRACT_ONLY"])
    trace_refs: list[AgentRuntimeTraceRef] = Field(default_factory=list)
    authority_posture: AgentRuntimeAuthorityPosture = Field(default_factory=AgentRuntimeAuthorityPosture)
    output_is_authority: bool = False

    @field_validator("decision_ref", "request_ref", "adapter_ref")
    @classmethod
    def validate_ref_fields(cls, value: str) -> str:
        _validate_safe_ref(value, "agent_runtime_decision_ref")
        return value

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_summary")
        return value

    @model_validator(mode="after")
    def validate_output_authority(self) -> "AgentRuntimeDecision":
        if self.output_is_authority:
            raise ValueError("AGENT_RUNTIME_OUTPUT_AUTHORITY_DENIED")
        return self


class AgentRuntimeResult(_AgentRuntimeModel):
    result_ref: str
    request_ref: str
    decision_ref: str
    safe_output_ref: str
    safe_summary: str = Field(..., min_length=1)
    trace_refs: list[AgentRuntimeTraceRef] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    output_is_authority: bool = False
    execution_performed: bool = False
    provider_runtime_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    connector_write_performed: bool = False

    @field_validator("result_ref", "request_ref", "decision_ref", "safe_output_ref")
    @classmethod
    def validate_ref_fields(cls, value: str) -> str:
        _validate_safe_ref(value, "agent_runtime_result_ref")
        return value

    @field_validator("receipt_refs", "evidence_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "agent_runtime_result_ref")
        return values

    @field_validator("safe_summary")
    @classmethod
    def validate_safe_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_summary")
        return value

    @model_validator(mode="after")
    def validate_no_effect_result(self) -> "AgentRuntimeResult":
        denied = {
            "output_is_authority": self.output_is_authority,
            "execution_performed": self.execution_performed,
            "provider_runtime_performed": self.provider_runtime_performed,
            "memory_write_performed": self.memory_write_performed,
            "context_injection_performed": self.context_injection_performed,
            "connector_write_performed": self.connector_write_performed,
        }
        enabled = [name for name, value in denied.items() if value]
        if enabled:
            raise ValueError(f"AGENT_RUNTIME_RESULT_AUTHORITY_DENIED: {', '.join(enabled)}")
        return self


class AgentRuntimeAdapter(Protocol):
    adapter_ref: str
    runtime_kind: AgentRuntimeKind

    def decide(self, request: AgentRuntimeRequest) -> AgentRuntimeDecision:
        ...

    def invoke(self, request: AgentRuntimeRequest) -> AgentRuntimeResult:
        ...


class DeterministicNoopAgentRuntimeAdapter:
    adapter_ref = "agent-runtime-adapter:deterministic-noop"
    runtime_kind = AgentRuntimeKind.deterministic_local

    def decide(self, request: AgentRuntimeRequest) -> AgentRuntimeDecision:
        return AgentRuntimeDecision(
            decision_ref=f"agent-runtime-decision:{_ref_suffix(request.request_ref)}",
            request_ref=request.request_ref,
            adapter_ref=self.adapter_ref,
            runtime_kind=self.runtime_kind,
            safe_summary="Deterministic no-op adapter accepted the contract without execution authority.",
            trace_refs=[
                AgentRuntimeTraceRef(
                    trace_ref=f"agent-runtime-trace:{_ref_suffix(request.request_ref)}",
                )
            ],
        )

    def invoke(self, request: AgentRuntimeRequest) -> AgentRuntimeResult:
        decision = self.decide(request)
        return AgentRuntimeResult(
            result_ref=f"agent-runtime-result:{_ref_suffix(request.request_ref)}",
            request_ref=request.request_ref,
            decision_ref=decision.decision_ref,
            safe_output_ref=f"agent-runtime-output:{_ref_suffix(request.request_ref)}",
            safe_summary="Deterministic no-op adapter produced a safe output ref only.",
            trace_refs=list(decision.trace_refs),
            receipt_refs=[f"agent-runtime-receipt:{_ref_suffix(request.request_ref)}"],
            evidence_refs=[f"evidence-ref:agent-runtime:{_ref_suffix(request.request_ref)}"],
        )


def _validate_safe_ref(value: str, field_name: str) -> None:
    if not value or not SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    for fragment in FORBIDDEN_SAFE_TEXT_FRAGMENTS:
        if fragment.lower() in lowered:
            raise ValueError(f"{field_name} contains forbidden raw-content marker")


def _ref_suffix(value: str) -> str:
    return value.split(":", 1)[1].replace(":", "-").replace("/", "-")
