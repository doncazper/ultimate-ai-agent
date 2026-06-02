from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_runtime.enums import (
    LocalModelRuntimeActivationStatus,
    LocalModelRuntimeKind,
    LocalModelRuntimeRiskLevel,
    LocalModelRuntimeStatus,
    LocalModelRuntimeTrustLevel,
)


class _LocalRuntimeActivationModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class LocalModelRuntimeActivationPolicy(_LocalRuntimeActivationModel):
    policy_ref: str = "local_model_runtime_activation_policy_m22"
    status: LocalModelRuntimeStatus = LocalModelRuntimeStatus.contract_only
    trust_level: LocalModelRuntimeTrustLevel = LocalModelRuntimeTrustLevel.local_metadata_only
    risk_level: LocalModelRuntimeRiskLevel = LocalModelRuntimeRiskLevel.safe_metadata
    activation_allowed_now: bool = False
    real_model_call_allowed: bool = False
    runtime_execution_allowed: bool = False
    endpoint_probe_allowed: bool = False
    provider_call_allowed: bool = False
    user_content_allowed: bool = False
    tool_call_allowed: bool = False
    memory_write_allowed: bool = False
    remote_host_allowed: bool = False
    secret_material_allowed: bool = False
    approval_ref_can_authorize_activation: bool = False
    requires_m23_for_real_call: bool = True
    safe_summary: str = "M22 local runtime activation policy is contract-only."
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalModelRuntimeActivationRequest(_LocalRuntimeActivationModel):
    request_ref: str = Field(..., min_length=1)
    runtime_kind: LocalModelRuntimeKind
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: LocalModelRuntimeActivationStatus = LocalModelRuntimeActivationStatus.requires_m23
    safe_summary: str = Field(..., min_length=1)
    approval_ref: str | None = None
    runtime_execution_requested: bool = False
    provider_call_requested: bool = False
    endpoint_probe_requested: bool = False
    prompt_present: bool = False
    user_content_present: bool = False
    secret_present: bool = False
    tool_call_requested: bool = False
    memory_write_requested: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalModelRuntimeActivationDecision(_LocalRuntimeActivationModel):
    decision_ref: str = Field(..., min_length=1)
    runtime_kind: LocalModelRuntimeKind
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    allowed: bool = False
    status: LocalModelRuntimeActivationStatus = LocalModelRuntimeActivationStatus.denied
    safe_message: str = Field(..., min_length=1)
    required_next_milestone: str = "M23"
    approval_ref_authorized: bool = False
    no_model_called: bool = True
    no_runtime_activated: bool = True
    no_endpoint_contacted: bool = True
    no_user_content_processed: bool = True
    no_tool_call_performed: bool = True
    no_memory_write_performed: bool = True
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
