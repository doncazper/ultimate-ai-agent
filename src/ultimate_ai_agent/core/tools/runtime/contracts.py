from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.runtime.enums import (
    ToolInvocationKind,
    ToolInvocationStatus,
    ToolRuntimeAdapterStatus,
    ToolRuntimeAuthorityLevel,
    ToolRuntimeCapability,
    ToolRuntimeMode,
)
from ultimate_ai_agent.core.tools.runtime.validation import (
    NOOP_TOOL_NAME,
    NOOP_TOOL_REF,
    raw_input_reason_codes,
    validate_safe_tool_runtime_payload,
    validate_safe_tool_runtime_text,
    validate_tool_runtime_ref,
)


class ToolRuntimeAdapterDescriptor(BaseModel):
    adapter_ref: str = "tool-runtime-adapter:noop.v1"
    status: ToolRuntimeAdapterStatus = ToolRuntimeAdapterStatus.noop_only
    mode: ToolRuntimeMode = ToolRuntimeMode.noop_only
    tool_ref: str = NOOP_TOOL_REF
    tool_name: str = NOOP_TOOL_NAME
    safe_description: str = "Deterministic no-op runtime adapter."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_descriptor(self):
        validate_tool_runtime_ref(self.adapter_ref, "adapter_ref")
        validate_tool_runtime_ref(self.tool_ref, "tool_ref")
        validate_safe_tool_runtime_text(self.tool_name, "tool_name")
        validate_safe_tool_runtime_text(self.safe_description, "safe_description")
        if self.tool_ref != NOOP_TOOL_REF or self.tool_name != NOOP_TOOL_NAME:
            raise ValueError("M31 runtime adapter may describe only the no-op tool")
        return self


class ToolRuntimePolicy(BaseModel):
    tool_runtime_enabled: bool = True
    noop_tool_enabled: bool = True
    replay_protection_required: bool = True
    arbitrary_tool_execution_enabled: bool = False
    side_effecting_tools_enabled: bool = False
    shell_tools_enabled: bool = False
    file_tools_enabled: bool = False
    memory_write_tools_enabled: bool = False
    network_tools_enabled: bool = False
    model_tools_enabled: bool = False
    browser_tools_enabled: bool = False
    mobile_tools_enabled: bool = False
    remote_tools_enabled: bool = False
    plugin_tools_enabled: bool = False
    dynamic_tool_registration_enabled: bool = False
    backend_execute_routes_enabled: bool = False
    control_center_execute_controls_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self):
        if not self.tool_runtime_enabled:
            raise ValueError("M31 tool runtime adapter must be enabled for no-op only")
        if not self.noop_tool_enabled:
            raise ValueError("M31 no-op tool must be enabled")
        blocked_fields = [
            "arbitrary_tool_execution_enabled",
            "side_effecting_tools_enabled",
            "shell_tools_enabled",
            "file_tools_enabled",
            "memory_write_tools_enabled",
            "network_tools_enabled",
            "model_tools_enabled",
            "browser_tools_enabled",
            "mobile_tools_enabled",
            "remote_tools_enabled",
            "plugin_tools_enabled",
            "dynamic_tool_registration_enabled",
            "backend_execute_routes_enabled",
            "control_center_execute_controls_enabled",
            "production_authority_enabled",
        ]
        for field_name in blocked_fields:
            if self.__dict__[field_name]:
                raise ValueError(f"{field_name} must be False in M31")
        return self


class ToolRuntimeManifest(BaseModel):
    baseline_version: str = "0.35.1"
    contract_version: str = "m31-tool-runtime-noop"
    adapter: ToolRuntimeAdapterDescriptor = Field(default_factory=ToolRuntimeAdapterDescriptor)
    policy: ToolRuntimePolicy = Field(default_factory=ToolRuntimePolicy)
    capabilities: List[ToolRuntimeCapability] = Field(
        default_factory=lambda: [
            ToolRuntimeCapability.noop,
            ToolRuntimeCapability.deterministic_result,
            ToolRuntimeCapability.no_effect,
            ToolRuntimeCapability.no_filesystem,
            ToolRuntimeCapability.no_memory_write,
            ToolRuntimeCapability.no_network,
            ToolRuntimeCapability.no_model_call,
            ToolRuntimeCapability.no_shell,
            ToolRuntimeCapability.no_browser,
            ToolRuntimeCapability.no_mobile,
            ToolRuntimeCapability.no_remote,
            ToolRuntimeCapability.no_plugin,
        ]
    )
    allowlisted_tool_refs: List[str] = Field(default_factory=lambda: [NOOP_TOOL_REF])

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self):
        if self.allowlisted_tool_refs != [NOOP_TOOL_REF]:
            raise ValueError("M31 manifest allowlist must contain only the no-op tool")
        return self


class ToolInvocationRequest(BaseModel):
    invocation_id: str = Field(..., min_length=1)
    tool_ref: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    invocation_kind: ToolInvocationKind = ToolInvocationKind.noop
    replay_key: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    approval_ref: Optional[str] = None
    authority_refs: List[str] = Field(default_factory=list)
    input_refs: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    contains_secret_like_content: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self):
        validate_tool_runtime_ref(self.invocation_id, "invocation_id")
        validate_tool_runtime_ref(self.tool_ref, "tool_ref")
        validate_safe_tool_runtime_text(self.tool_name, "tool_name")
        validate_tool_runtime_ref(self.replay_key, "replay_key")
        validate_safe_tool_runtime_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_tool_runtime_text(self.approval_ref, "approval_ref")
        for ref in [*self.authority_refs, *self.input_refs, *self.metadata_refs]:
            validate_tool_runtime_ref(ref, "metadata_ref")
        for reason in raw_input_reason_codes(self):
            raise ValueError(reason)
        validate_safe_tool_runtime_payload(self.metadata, "metadata")
        return self


class NoOpToolInput(BaseModel):
    input_ref: str = "noop-input:m31"
    safe_summary: str = "No-op invocation input."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_input(self):
        validate_tool_runtime_ref(self.input_ref, "input_ref")
        validate_safe_tool_runtime_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_tool_runtime_ref(ref, "metadata_ref")
        return self


class NoOpToolOutput(BaseModel):
    output_ref: str
    safe_message: str = "NOOP_TOOL_COMPLETED"
    deterministic: bool = True
    raw_input_echoed: bool = False
    raw_content_stored: bool = False
    side_effects_performed: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_output(self):
        validate_tool_runtime_ref(self.output_ref, "output_ref")
        validate_safe_tool_runtime_text(self.safe_message, "safe_message")
        if not self.deterministic or self.raw_input_echoed or self.raw_content_stored or self.side_effects_performed:
            raise ValueError("M31 no-op output must be deterministic and side-effect-free")
        return self


class ToolInvocationReceiptPlan(BaseModel):
    receipt_plan_ref: str
    invocation_id: str
    tool_ref: str = NOOP_TOOL_REF
    execution_performed: bool = True
    side_effects_performed: List[str] = Field(default_factory=list)
    raw_input_stored: bool = False
    raw_output_stored: bool = False
    memory_write_performed: bool = False
    event_ledger_mutation_performed: bool = False
    safe_summary: str = "Non-authoritative no-op tool runtime receipt plan."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self):
        for ref in [self.receipt_plan_ref, self.invocation_id, self.tool_ref, *self.metadata_refs]:
            validate_tool_runtime_ref(ref, "metadata_ref")
        if self.tool_ref != NOOP_TOOL_REF:
            raise ValueError("M31 receipt plans may reference only the no-op tool")
        if not self.execution_performed:
            raise ValueError("M31 no-op receipt records only deterministic no-op invocation")
        if self.side_effects_performed or self.raw_input_stored or self.raw_output_stored:
            raise ValueError("M31 no-op receipt must not store raw content or side effects")
        if self.memory_write_performed or self.event_ledger_mutation_performed:
            raise ValueError("M31 no-op receipt must not mutate memory or Event Ledger")
        validate_safe_tool_runtime_text(self.safe_summary, "safe_summary")
        return self


class ToolInvocationResult(BaseModel):
    result_id: str
    invocation_id: str
    tool_ref: str = NOOP_TOOL_REF
    status: ToolInvocationStatus = ToolInvocationStatus.noop_completed
    output: NoOpToolOutput
    execution_performed: bool = True
    side_effects_performed: List[str] = Field(default_factory=list)
    raw_input_echoed: bool = False
    raw_content_stored: bool = False
    memory_write_performed: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    shell_execution_performed: bool = False
    receipt_plan: ToolInvocationReceiptPlan

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_result(self):
        for ref in [self.result_id, self.invocation_id, self.tool_ref]:
            validate_tool_runtime_ref(ref, "metadata_ref")
        if self.tool_ref != NOOP_TOOL_REF or self.status != ToolInvocationStatus.noop_completed:
            raise ValueError("M31 results are only for completed no-op invocations")
        if not self.execution_performed:
            raise ValueError("M31 no-op runtime result must record deterministic no-op invocation")
        unsafe_flags = [
            self.side_effects_performed,
            self.raw_input_echoed,
            self.raw_content_stored,
            self.memory_write_performed,
            self.network_call_performed,
            self.model_call_performed,
            self.shell_execution_performed,
        ]
        if any(unsafe_flags):
            raise ValueError("M31 no-op runtime result must not report side effects")
        return self


class ToolInvocationDecision(BaseModel):
    decision_id: str
    invocation_id: str
    tool_ref: str
    status: ToolInvocationStatus
    invocation_allowed: bool = False
    execution_performed: bool = False
    authority_level: ToolRuntimeAuthorityLevel = ToolRuntimeAuthorityLevel.non_authoritative
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    result: Optional[ToolInvocationResult] = None
    receipt_plan: Optional[ToolInvocationReceiptPlan] = None
    side_effects_performed: List[str] = Field(default_factory=list)
    raw_input_echoed: bool = False
    raw_content_stored: bool = False
    memory_write_performed: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    shell_execution_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self):
        for ref in [self.decision_id, self.invocation_id, self.tool_ref]:
            validate_tool_runtime_ref(ref, "metadata_ref")
        validate_safe_tool_runtime_text(self.safe_message, "safe_message")
        if self.tool_ref != NOOP_TOOL_REF:
            raise ValueError("M31 decisions may reference only the no-op tool")
        if self.execution_performed and self.status != ToolInvocationStatus.noop_completed:
            raise ValueError("M31 execution_performed is true only for completed no-op invocation")
        unsafe_flags = [
            self.side_effects_performed,
            self.raw_input_echoed,
            self.raw_content_stored,
            self.memory_write_performed,
            self.network_call_performed,
            self.model_call_performed,
            self.shell_execution_performed,
        ]
        if any(unsafe_flags):
            raise ValueError("M31 tool runtime decisions must not report side effects")
        return self
