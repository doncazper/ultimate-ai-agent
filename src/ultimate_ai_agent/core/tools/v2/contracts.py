from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.enums import (
    ToolApprovalRequirement,
    ToolAuthorityLevel,
    ToolExecutionMode,
    ToolInputTrustLevel,
    ToolIntentDecisionStatus,
    ToolRiskClass,
    ToolSideEffectKind,
    ToolTargetKind,
)
from ultimate_ai_agent.core.tools.v2.validation import (
    assert_model_output_not_tool_input,
    assert_no_tool_execution,
    assert_no_tool_side_effects,
    validate_safe_tool_payload,
    validate_safe_tool_text,
    validate_tool_ref,
)


class ToolTargetRef(BaseModel):
    target_ref: str = Field(..., min_length=1)
    target_kind: ToolTargetKind
    safe_label: str = ""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_target(self) -> Any:
        validate_tool_ref(self.target_ref, "target_ref")
        if self.safe_label:
            validate_safe_tool_text(self.safe_label, "safe_label")
        return self


class ToolInputBoundary(BaseModel):
    input_refs: List[str] = Field(default_factory=list)
    input_trust_level: ToolInputTrustLevel = ToolInputTrustLevel.user_provided_refs
    contains_raw_content: bool = False
    contains_secret_like_content: bool = False
    contains_model_output: bool = False
    contains_runtime_output: bool = False
    contains_openwebui_output: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_boundary(self) -> Any:
        for ref in [*self.input_refs, *self.metadata_refs]:
            validate_tool_ref(ref, "input_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        if self.contains_raw_content:
            raise ValueError("raw tool input content is denied")
        if self.contains_secret_like_content:
            raise ValueError("secret-like tool input content is denied")
        if self.contains_model_output:
            raise ValueError("model output is denied as tool input")
        if self.contains_runtime_output:
            raise ValueError("runtime output is denied as tool input")
        if self.contains_openwebui_output:
            raise ValueError("OpenWebUI output is denied as tool input")
        assert_model_output_not_tool_input(self.input_trust_level)
        return self


class ToolIntent(BaseModel):
    intent_id: str = Field(..., min_length=1)
    tool_id: str = Field(..., min_length=1)
    intent_summary: str = Field(..., min_length=1)
    target: ToolTargetRef
    input_boundary: ToolInputBoundary
    requested_execution_mode: ToolExecutionMode = ToolExecutionMode.preview_only
    declared_risk_class: ToolRiskClass = ToolRiskClass.low
    declared_side_effects: List[ToolSideEffectKind] = Field(default_factory=lambda: [ToolSideEffectKind.none])
    approval_requirement: ToolApprovalRequirement = ToolApprovalRequirement.not_required
    authority_level: ToolAuthorityLevel = ToolAuthorityLevel.validation_only
    approval_ref: Optional[str] = None
    context_pack_refs: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_intent(self) -> Any:
        validate_tool_ref(self.intent_id, "intent_id")
        validate_safe_tool_text(self.tool_id, "tool_id")
        validate_safe_tool_text(self.intent_summary, "intent_summary")
        if self.approval_ref:
            validate_safe_tool_text(self.approval_ref, "approval_ref")
        for ref in [*self.context_pack_refs, *self.metadata_refs]:
            validate_tool_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class ToolCatalogEntry(BaseModel):
    tool_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    target_kind: ToolTargetKind
    allowed_execution_modes: List[ToolExecutionMode] = Field(default_factory=lambda: [ToolExecutionMode.preview_only])
    risk_class: ToolRiskClass = ToolRiskClass.low
    side_effects: List[ToolSideEffectKind] = Field(default_factory=lambda: [ToolSideEffectKind.none])
    approval_requirement: ToolApprovalRequirement = ToolApprovalRequirement.not_required
    safe_description: str = ""
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_catalog_entry(self) -> Any:
        validate_safe_tool_text(self.tool_id, "tool_id")
        validate_safe_tool_text(self.display_name, "display_name")
        if self.safe_description:
            validate_safe_tool_text(self.safe_description, "safe_description")
        for ref in self.metadata_refs:
            validate_tool_ref(ref, "metadata_ref")
        return self


class ToolReceiptPlan(BaseModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    intent_id: str = Field(..., min_length=1)
    tool_id: str = Field(..., min_length=1)
    execution_performed: bool = False
    side_effects_performed: List[ToolSideEffectKind] = Field(default_factory=list)
    raw_output_stored: bool = False
    memory_write_performed: bool = False
    event_ledger_mutation_performed: bool = False
    safe_summary: str = "Validation-only receipt plan."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt_plan(self) -> Any:
        assert_no_tool_execution(self.execution_performed)
        if self.side_effects_performed:
            raise ValueError("M27 receipt plans must not record performed side effects")
        if self.raw_output_stored:
            raise ValueError("M27 receipt plans must not store raw output")
        if self.memory_write_performed:
            raise ValueError("M27 receipt plans must not write memory")
        if self.event_ledger_mutation_performed:
            raise ValueError("M27 receipt plans must not mutate the Event Ledger")
        validate_safe_tool_text(self.safe_summary, "safe_summary")
        for ref in [self.receipt_plan_ref, self.intent_id, *self.metadata_refs]:
            validate_tool_ref(ref, "metadata_ref")
        return self


class ToolIntentDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    intent_id: str = Field(..., min_length=1)
    tool_id: str = Field(..., min_length=1)
    status: ToolIntentDecisionStatus
    preview_allowed: bool = False
    execution_allowed: bool = False
    approval_required: bool = False
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    receipt_plan: Optional[ToolReceiptPlan] = None
    no_tool_execution_performed: bool = True
    no_side_effects_performed: bool = True
    no_memory_write_performed: bool = True
    no_event_ledger_mutation_performed: bool = True
    no_network_call_performed: bool = True
    no_model_call_performed: bool = True
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        assert_no_tool_execution(self.execution_allowed)
        assert_no_tool_side_effects(not self.no_side_effects_performed)
        if not self.no_memory_write_performed:
            raise ValueError("M27 Tool Broker v2 decisions must not write memory")
        if not self.no_event_ledger_mutation_performed:
            raise ValueError("M27 Tool Broker v2 decisions must not mutate the Event Ledger")
        if not self.no_network_call_performed:
            raise ValueError("M27 Tool Broker v2 decisions must not perform network calls")
        if not self.no_model_call_performed:
            raise ValueError("M27 Tool Broker v2 decisions must not call models")
        validate_safe_tool_text(self.safe_message, "safe_message")
        for ref in [self.decision_id, self.intent_id, *self.metadata_refs]:
            validate_tool_ref(ref, "metadata_ref")
        return self


class ToolBrokerV2Manifest(BaseModel):
    baseline_version: str = "0.31.0"
    contract_version: str = "m27-tool-broker-v2"
    tool_execution_enabled: bool = False
    backend_execution_routes_added: bool = False
    shell_execution_enabled: bool = False
    file_mutation_enabled: bool = False
    network_calls_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_enablement_enabled: bool = False
    memory_writes_enabled: bool = False
    event_ledger_mutation_enabled: bool = False
    model_provider_calls_enabled: bool = False
    context_pack_authority_enabled: bool = False
    context_injection_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> Any:
        blocked_true_fields = [
            "tool_execution_enabled",
            "backend_execution_routes_added",
            "shell_execution_enabled",
            "file_mutation_enabled",
            "network_calls_enabled",
            "browser_automation_enabled",
            "plugin_enablement_enabled",
            "memory_writes_enabled",
            "event_ledger_mutation_enabled",
            "model_provider_calls_enabled",
            "context_pack_authority_enabled",
            "context_injection_enabled",
            "production_authority_enabled",
        ]
        for field_name in blocked_true_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M27")
        return self
