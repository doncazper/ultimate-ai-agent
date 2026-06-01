from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_router.enums import ModelPrivacyClass, ModelProviderKind, ModelTaskCapability


class ModelCapabilityProfile(BaseModel):
    model_profile_id: str = Field(..., min_length=1)
    provider_kind: ModelProviderKind
    runtime_id: Optional[str] = None
    provider_id: Optional[str] = None
    model_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    capabilities: List[ModelTaskCapability] = Field(default_factory=list)
    privacy_class: ModelPrivacyClass
    max_context_tokens: Optional[int] = Field(None, ge=1)
    supports_json_mode: bool = False
    supports_tools: bool = False
    supports_streaming: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    supports_structured_output: bool = False
    cost_per_1k_input_tokens: Optional[float] = Field(None, ge=0)
    cost_per_1k_output_tokens: Optional[float] = Field(None, ge=0)
    estimated_tokens_per_second: Optional[float] = Field(None, ge=0)
    time_to_first_token_ms: Optional[float] = Field(None, ge=0)
    resource_profile_ref: Optional[str] = None
    credential_ref: Optional[str] = None
    enabled: bool = True
    owner: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @property
    def is_cloud(self) -> bool:
        return self.provider_kind in {
            ModelProviderKind.cloud_provider,
            ModelProviderKind.openai_compatible,
            ModelProviderKind.sdk_adapter_placeholder,
        }

    @property
    def is_paid(self) -> bool:
        return self.cost_per_1k_input_tokens is not None or self.cost_per_1k_output_tokens is not None
