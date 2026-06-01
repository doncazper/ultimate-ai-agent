from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_router.enums import ModelPrivacyClass, ModelProviderKind, ModelTaskCapability


class ModelRoutingPolicy(BaseModel):
    policy_id: str = Field(..., min_length=1)
    required_capabilities: List[ModelTaskCapability] = Field(default_factory=list)
    preferred_capabilities: List[ModelTaskCapability] = Field(default_factory=list)
    forbidden_provider_kinds: List[ModelProviderKind] = Field(default_factory=list)
    allowed_provider_kinds: List[ModelProviderKind] = Field(default_factory=list)
    privacy_mode: ModelPrivacyClass = ModelPrivacyClass.project_allowed
    prefer_local: bool = True
    allow_cloud: bool = False
    allow_paid: bool = False
    max_estimated_cost_usd: Optional[float] = Field(None, ge=0)
    max_latency_ms: Optional[float] = Field(None, ge=0)
    min_context_tokens: Optional[int] = Field(None, ge=1)
    require_structured_output: Optional[bool] = None
    require_tool_support: Optional[bool] = None
    require_human_approval_for_cloud: Optional[bool] = None
    fallback_allowed: bool = False
    reason_codes_required: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
