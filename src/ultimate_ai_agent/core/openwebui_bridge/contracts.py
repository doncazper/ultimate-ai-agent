from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ultimate_ai_agent.core.openwebui_bridge.enums import (
    OpenWebUIAuthorityBoundary,
    OpenWebUIBridgeAdapterStatus,
    OpenWebUIBridgeDecisionStatus,
    OpenWebUIBridgeStatus,
    OpenWebUIContentMode,
    OpenWebUIMessageDirection,
    OpenWebUIRuntimeBridgeStatus,
    OpenWebUISafeHandoffStatus,
    OpenWebUISafeConversationSurfaceStatus,
    OpenWebUISurfaceRole,
)


class _OpenWebUIBridgeContractModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class OpenWebUIBridgeManifest(_OpenWebUIBridgeContractModel):
    manifest_id: str = "openwebui_bridge_manifest_m21"
    baseline_version: str = "0.25.1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: OpenWebUIBridgeStatus = OpenWebUIBridgeStatus.contract_only
    supported_surfaces: list[OpenWebUISurfaceRole] = Field(default_factory=list)
    blocked_surfaces: list[OpenWebUISurfaceRole] = Field(default_factory=list)
    allowed_content_modes: list[OpenWebUIContentMode] = Field(default_factory=list)
    blocked_content_modes: list[OpenWebUIContentMode] = Field(default_factory=list)
    authority_boundaries: list[OpenWebUIAuthorityBoundary] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    safe_summary: str = "M21 OpenWebUI bridge contract-only manifest."
    agent_core_remains_authority: bool = True
    openwebui_is_preferred_conversational_shell: bool = True
    openwebui_is_agent_brain: bool = False
    openwebui_integration_implemented: bool = False
    deployment_config_added: bool = False
    backend_routes_added: bool = False
    openwebui_package_imported: bool = False
    dependencies_added: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    runtime_execution_enabled: bool = False
    provider_call_enabled: bool = False
    approval_grant_enabled: bool = False
    credential_access_enabled: bool = False
    raw_content_allowed: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "supported_surfaces",
        "blocked_surfaces",
        "allowed_content_modes",
        "blocked_content_modes",
        "authority_boundaries",
        "docs_refs",
        "warnings",
    )
    @classmethod
    def _copy_collections(cls, value: list[Any]) -> list[Any]:
        return list(value)


class OpenWebUIChatSessionRef(_OpenWebUIBridgeContractModel):
    session_ref: str = Field(..., min_length=1)
    shell_ref: str = Field(..., min_length=1)
    user_ref: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    safe_label: str = Field(..., min_length=1)
    authority_granted: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUITranscriptRef(_OpenWebUIBridgeContractModel):
    transcript_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    redaction_status: str = "redacted_summary_only"
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_summary: str = Field(..., min_length=1)
    raw_content_stored: bool = False
    event_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIMessageRef(_OpenWebUIBridgeContractModel):
    message_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    direction: OpenWebUIMessageDirection
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_summary: str = Field(..., min_length=1)
    event_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIChatIngressEnvelope(_OpenWebUIBridgeContractModel):
    envelope_id: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    message_ref: str = Field(..., min_length=1)
    direction: OpenWebUIMessageDirection
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    user_visible_summary: str = Field(..., min_length=1)
    raw_content_present: bool = False
    raw_content_allowed: bool = False
    contains_user_content: bool = True
    contains_secret_like_content: bool = False
    requires_redaction: bool = True
    requires_agent_core_processing: bool = True
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    runtime_execution_requested: bool = False
    provider_call_requested: bool = False
    approval_ref: str | None = None
    validation_status: OpenWebUIBridgeDecisionStatus = (
        OpenWebUIBridgeDecisionStatus.requires_future_bridge
    )
    event_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIChatEgressEnvelope(_OpenWebUIBridgeContractModel):
    envelope_id: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    message_ref: str = Field(..., min_length=1)
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_response_summary: str = Field(..., min_length=1)
    model_output_non_authoritative: bool = True
    action_executed: bool = False
    tool_executed: bool = False
    memory_written: bool = False
    provider_called: bool = False
    runtime_called: bool = False
    approval_granted: bool = False
    event_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIBridgeValidationDecision(_OpenWebUIBridgeContractModel):
    decision_id: str = Field(..., min_length=1)
    subject_ref: str = Field(..., min_length=1)
    allowed: bool = False
    status: OpenWebUIBridgeDecisionStatus = OpenWebUIBridgeDecisionStatus.not_implemented
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    required_next_action: str = "future_reviewed_bridge_milestone_required"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIBridgePlan(_OpenWebUIBridgeContractModel):
    plan_id: str = "openwebui_bridge_plan_m21"
    status: OpenWebUIBridgeStatus = OpenWebUIBridgeStatus.planned_disabled
    stage: str = "m21_contract_only"
    purpose: str = "Define future OpenWebUI chat shell bridge contracts."
    allowed_scope: list[str] = Field(default_factory=list)
    blocked_scope: list[str] = Field(default_factory=list)
    required_future_milestones: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIBridgeReceiptPlan(_OpenWebUIBridgeContractModel):
    receipt_plan_id: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    redaction_required: bool = True
    raw_transcript_storage_allowed: bool = False
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIBridgeAdapterPolicy(_OpenWebUIBridgeContractModel):
    adapter_policy_ref: str = "openwebui-bridge-adapter-policy:m51"
    baseline_version: str = "0.55.0"
    status: OpenWebUIBridgeStatus = OpenWebUIBridgeStatus.adapter_pilot
    safe_summary_only: bool = True
    agent_core_remains_authority: bool = True
    openwebui_is_agent_brain: bool = False
    adapter_runtime_enabled: bool = False
    live_openwebui_connection_enabled: bool = False
    openwebui_network_call_enabled: bool = False
    provider_call_enabled: bool = False
    model_authority_enabled: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    approval_ref_authority_enabled: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    raw_content_allowed: bool = False
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIBridgeAdapterRequest(_OpenWebUIBridgeContractModel):
    adapter_request_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    message_ref: str = Field(..., min_length=1)
    safe_user_summary: str = Field(..., min_length=1)
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    approval_ref: str | None = None
    raw_prompt_present: bool = False
    raw_provider_payload_present: bool = False
    raw_content_present: bool = False
    secret_like_content_present: bool = False
    provider_call_requested: bool = False
    model_authority_requested: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    openwebui_runtime_call_requested: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIBridgeAdapterResult(_OpenWebUIBridgeContractModel):
    adapter_result_ref: str
    adapter_request_ref: str
    session_ref: str
    message_ref: str
    status: OpenWebUIBridgeAdapterStatus = OpenWebUIBridgeAdapterStatus.safe_summary_ready
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_shell_summary: str
    reason_codes: list[str] = Field(default_factory=list)
    raw_prompt_returned: bool = False
    raw_provider_payload_returned: bool = False
    raw_content_returned: bool = False
    model_output_authoritative: bool = False
    openwebui_called: bool = False
    provider_called: bool = False
    tool_executed: bool = False
    memory_written: bool = False
    context_injected: bool = False
    approval_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeConversationSurfacePolicy(_OpenWebUIBridgeContractModel):
    surface_policy_ref: str = "openwebui-safe-conversation-policy:m52"
    baseline_version: str = "0.56.0"
    status: OpenWebUIBridgeStatus = OpenWebUIBridgeStatus.safe_conversation_surface
    safe_summary_only: bool = True
    agent_core_remains_authority: bool = True
    openwebui_is_agent_brain: bool = False
    live_openwebui_connection_enabled: bool = False
    openwebui_runtime_call_enabled: bool = False
    openwebui_network_call_enabled: bool = False
    provider_call_enabled: bool = False
    model_call_enabled: bool = False
    model_authority_enabled: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    approval_ref_authority_enabled: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    raw_content_allowed: bool = False
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeConversationTurn(_OpenWebUIBridgeContractModel):
    turn_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    message_ref: str = Field(..., min_length=1)
    direction: OpenWebUIMessageDirection
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_summary: str = Field(..., min_length=1)
    approval_ref: str | None = None
    raw_prompt_present: bool = False
    raw_provider_payload_present: bool = False
    raw_content_present: bool = False
    secret_like_content_present: bool = False
    provider_call_requested: bool = False
    model_call_requested: bool = False
    model_authority_requested: bool = False
    model_output_authoritative: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    openwebui_runtime_call_requested: bool = False
    event_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeConversationSurface(_OpenWebUIBridgeContractModel):
    conversation_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    status: OpenWebUISafeConversationSurfaceStatus = (
        OpenWebUISafeConversationSurfaceStatus.safe_review_ready
    )
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_title: str = Field(..., min_length=1)
    turns: list[OpenWebUISafeConversationTurn] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    openwebui_called: bool = False
    provider_called: bool = False
    model_called: bool = False
    model_output_authoritative: bool = False
    tool_executed: bool = False
    memory_written: bool = False
    context_injected: bool = False
    approval_granted: bool = False
    raw_prompt_returned: bool = False
    raw_provider_payload_returned: bool = False
    raw_content_returned: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIRuntimeBridgePolicy(_OpenWebUIBridgeContractModel):
    runtime_bridge_policy_ref: str = "openwebui-runtime-bridge-policy:m76"
    baseline_version: str = "0.80.0"
    status: OpenWebUIBridgeStatus = OpenWebUIBridgeStatus.contract_only
    safe_summary_only: bool = True
    review_only: bool = True
    agent_core_remains_authority: bool = True
    openwebui_is_agent_brain: bool = False
    live_openwebui_connection_enabled: bool = False
    openwebui_runtime_call_enabled: bool = False
    openwebui_network_call_enabled: bool = False
    provider_call_enabled: bool = False
    model_call_enabled: bool = False
    model_authority_enabled: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    approval_ref_authority_enabled: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    raw_content_allowed: bool = False
    credential_cookie_access_enabled: bool = False
    production_authority_enabled: bool = False
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIRuntimeBridgeRequest(_OpenWebUIBridgeContractModel):
    bridge_request_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_conversation_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    safe_intent_summary: str = Field(..., min_length=1)
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    approval_ref: str | None = None
    raw_prompt_present: bool = False
    raw_provider_payload_present: bool = False
    raw_content_present: bool = False
    secret_like_content_present: bool = False
    provider_call_requested: bool = False
    model_call_requested: bool = False
    model_authority_requested: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    openwebui_runtime_call_requested: bool = False
    openwebui_handoff_requested: bool = False
    network_call_requested: bool = False
    credential_cookie_access_requested: bool = False
    production_authority_requested: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIRuntimeBridgeReceiptPlan(_OpenWebUIBridgeContractModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    bridge_request_ref: str = Field(..., min_length=1)
    bridge_envelope_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_conversation_ref: str = Field(..., min_length=1)
    redaction_required: bool = True
    raw_prompt_stored: bool = False
    raw_provider_payload_stored: bool = False
    raw_content_stored: bool = False
    openwebui_runtime_call_performed: bool = False
    provider_call_performed: bool = False
    model_call_performed: bool = False
    tool_execution_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    network_call_performed: bool = False
    credential_cookie_access_performed: bool = False
    production_authority_granted: bool = False
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUIRuntimeBridgeEnvelope(_OpenWebUIBridgeContractModel):
    bridge_envelope_ref: str = Field(..., min_length=1)
    bridge_request_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_conversation_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    status: OpenWebUIRuntimeBridgeStatus = OpenWebUIRuntimeBridgeStatus.review_envelope_ready
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_bridge_summary: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    receipt_plan: OpenWebUIRuntimeBridgeReceiptPlan
    raw_prompt_returned: bool = False
    raw_provider_payload_returned: bool = False
    raw_content_returned: bool = False
    model_output_authoritative: bool = False
    openwebui_called: bool = False
    provider_called: bool = False
    model_called: bool = False
    tool_executed: bool = False
    memory_written: bool = False
    context_injected: bool = False
    network_called: bool = False
    credential_cookie_accessed: bool = False
    approval_granted: bool = False
    handoff_executed: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeHandoffPolicy(_OpenWebUIBridgeContractModel):
    safe_handoff_policy_ref: str = "openwebui-safe-handoff-policy:m77"
    baseline_version: str = "0.81.0"
    status: OpenWebUIBridgeStatus = OpenWebUIBridgeStatus.contract_only
    safe_summary_only: bool = True
    safe_handoff_execution_enabled: bool = True
    exact_approval_binding_required: bool = True
    agent_core_remains_authority: bool = True
    openwebui_is_agent_brain: bool = False
    live_openwebui_connection_enabled: bool = False
    openwebui_runtime_call_enabled: bool = False
    openwebui_network_call_enabled: bool = False
    provider_call_enabled: bool = False
    model_call_enabled: bool = False
    model_authority_enabled: bool = False
    tool_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    approval_ref_authority_enabled: bool = False
    raw_prompt_exposure_enabled: bool = False
    raw_provider_payload_exposure_enabled: bool = False
    raw_content_allowed: bool = False
    credential_cookie_access_enabled: bool = False
    production_authority_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeHandoffRequest(_OpenWebUIBridgeContractModel):
    handoff_request_ref: str = Field(..., min_length=1)
    bridge_envelope_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_conversation_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    approval_ref: str | None = Field(..., min_length=1)
    approved_bridge_envelope_ref: str = Field(..., min_length=1)
    approved_session_ref: str = Field(..., min_length=1)
    approved_safe_conversation_ref: str = Field(..., min_length=1)
    approved_actor_ref: str = Field(..., min_length=1)
    safe_handoff_summary: str = Field(..., min_length=1)
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    approval_expired: bool = False
    approval_revoked: bool = False
    approval_replayed: bool = False
    raw_prompt_present: bool = False
    raw_provider_payload_present: bool = False
    raw_content_present: bool = False
    secret_like_content_present: bool = False
    openwebui_runtime_call_requested: bool = False
    provider_call_requested: bool = False
    model_call_requested: bool = False
    model_authority_requested: bool = False
    tool_execution_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    network_call_requested: bool = False
    credential_cookie_access_requested: bool = False
    production_authority_requested: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeHandoffReceiptPlan(_OpenWebUIBridgeContractModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    handoff_request_ref: str = Field(..., min_length=1)
    safe_handoff_result_ref: str = Field(..., min_length=1)
    bridge_envelope_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_conversation_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    safe_handoff_recorded: bool = True
    redaction_required: bool = True
    raw_prompt_stored: bool = False
    raw_provider_payload_stored: bool = False
    raw_content_stored: bool = False
    openwebui_runtime_call_performed: bool = False
    provider_call_performed: bool = False
    model_call_performed: bool = False
    tool_execution_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    network_call_performed: bool = False
    credential_cookie_access_performed: bool = False
    production_authority_granted: bool = False
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenWebUISafeHandoffResult(_OpenWebUIBridgeContractModel):
    safe_handoff_result_ref: str = Field(..., min_length=1)
    handoff_request_ref: str = Field(..., min_length=1)
    bridge_envelope_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    session_ref: str = Field(..., min_length=1)
    safe_conversation_ref: str = Field(..., min_length=1)
    actor_ref: str = Field(..., min_length=1)
    status: OpenWebUISafeHandoffStatus = OpenWebUISafeHandoffStatus.safe_handoff_executed
    content_mode: OpenWebUIContentMode = OpenWebUIContentMode.summary_only
    safe_handoff_summary: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    receipt_plan: OpenWebUISafeHandoffReceiptPlan
    safe_handoff_executed: bool = True
    raw_prompt_returned: bool = False
    raw_provider_payload_returned: bool = False
    raw_content_returned: bool = False
    model_output_authoritative: bool = False
    openwebui_called: bool = False
    provider_called: bool = False
    model_called: bool = False
    tool_executed: bool = False
    memory_written: bool = False
    context_injected: bool = False
    network_called: bool = False
    credential_cookie_accessed: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
