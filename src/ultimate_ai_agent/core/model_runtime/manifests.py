from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeKind, ModelRuntimeSafetyMode
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


class ModelRuntimeAdapterManifest(BaseModel):
    adapter_id: str = Field(..., min_length=1)
    runtime_kind: ModelRuntimeKind
    display_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    supported_provider_kinds: List[str] = Field(default_factory=list)
    supported_capabilities: List[str] = Field(default_factory=list)
    safety_mode: ModelRuntimeSafetyMode
    accepts_model_profile_ids: List[str] = Field(default_factory=list)
    requires_credential_ref: bool = False
    allowed_credential_refs: List[str] = Field(default_factory=list)
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_json_mode: bool = False
    supports_structured_output: bool = False
    max_context_tokens: Optional[int] = Field(None, ge=1)
    max_input_tokens: Optional[int] = Field(None, ge=0)
    max_output_tokens: Optional[int] = Field(None, ge=0)
    owner: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    enabled: bool = True
    event_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def manifest_must_be_simulated_and_secret_clean(self) -> Any:
        assert_secret_clean(self.model_dump(mode="json"), "Model runtime adapter manifest")
        if self.safety_mode == ModelRuntimeSafetyMode.disabled:
            raise ValueError("Model runtime adapter manifest cannot use disabled safety mode.")
        return self
