from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.providers.enums import (
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderStatus,
)


class ProviderCapabilitySpec(BaseModel):
    capability: ProviderCapability
    description: Optional[str] = None
    freshness_seconds: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class ProviderTermsMetadata(BaseModel):
    terms_url: Optional[str] = None
    attribution_required: bool = False
    redistribution_allowed: bool = False

    model_config = ConfigDict(extra="forbid")


class ProviderRateLimitMetadata(BaseModel):
    requests_per_minute: Optional[int] = Field(None, ge=0)
    requests_per_day: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(extra="forbid")


class ProviderAttributionMetadata(BaseModel):
    display_name: Optional[str] = None
    url: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProviderHealthMetadata(BaseModel):
    status: str = "unknown"
    last_checked_at: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProviderManifest(BaseModel):
    provider_id: str
    display_name: str
    domain: ProviderDomain
    status: ProviderStatus = ProviderStatus.enabled
    auth_requirement: ProviderAuthRequirement = ProviderAuthRequirement.none
    cost_class: ProviderCostClass = ProviderCostClass.free_no_key
    capabilities: List[ProviderCapability] = Field(default_factory=list)
    default_priority: int = 100
    credential_ref: Optional[str] = None
    base_url: Optional[str] = None
    allowed_domains: List[str] = Field(default_factory=list)
    rate_limits: Optional[ProviderRateLimitMetadata] = None
    terms_metadata: Optional[ProviderTermsMetadata] = None
    attribution_metadata: Optional[ProviderAttributionMetadata] = None
    health_metadata: Optional[ProviderHealthMetadata] = None
    normalizer_ref: Optional[str] = None
    owner: str
    source: str
    version: str
    event_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class ProviderSelectionPolicy(BaseModel):
    policy_id: str
    prefer_free: bool = True
    allow_paid: bool = False
    allow_enterprise: bool = False
    allow_self_hosted: bool = True
    max_cost_class: ProviderCostClass = ProviderCostClass.free_with_key
    require_enabled: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
