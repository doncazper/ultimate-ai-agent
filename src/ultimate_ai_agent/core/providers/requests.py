from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.providers.enums import ProviderCapability, ProviderDomain


class ProviderRequest(BaseModel):
    request_id: str
    provider_id: Optional[str] = None
    domain: ProviderDomain
    capability: ProviderCapability
    input_summary: str
    parameter_refs: list[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    credential_ref: Optional[str] = None
    consent_ref: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
