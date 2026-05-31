from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.providers.enums import ProviderCapability, ProviderDomain


class ProviderNormalizationReport(BaseModel):
    report_id: str
    provider_id: str
    domain: ProviderDomain
    capability: ProviderCapability
    normalizer_ref: Optional[str] = None
    normalized: bool
    warnings: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
