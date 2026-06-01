from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.providers.enums import ProviderCapability, ProviderCostClass, ProviderDomain
from ultimate_ai_agent.core.providers.manifests import (
    ProviderAttributionMetadata,
    ProviderTermsMetadata,
)


class ProviderError(BaseModel):
    code: str
    safe_message: str
    retryable: bool = False

    model_config = ConfigDict(extra="forbid")


class SourceMetadata(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    observed_at: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProviderCostMetadata(BaseModel):
    cost_class: ProviderCostClass
    estimated_cost: float = 0.0
    currency: str = "USD"

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class ProviderFreshnessMetadata(BaseModel):
    fetched_at: datetime = Field(default_factory=utc_now)
    freshness_seconds: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(extra="forbid")


class WeatherNormalized(BaseModel):
    location_name: str
    temperature_c: Optional[float] = None
    condition: Optional[str] = None
    forecast_summary: Optional[str] = None
    observed_at: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class NewsNormalized(BaseModel):
    headline: str
    summary: Optional[str] = None
    source: SourceMetadata
    published_at: Optional[str] = None
    article_url: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProviderResultEnvelope(BaseModel):
    result_id: str
    provider_id: str
    domain: ProviderDomain
    capability: ProviderCapability
    fetched_at: datetime = Field(default_factory=utc_now)
    input_summary: str
    normalized: Any
    raw_ref: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    freshness_seconds: Optional[int] = Field(None, ge=0)
    cost: Optional[ProviderCostMetadata] = None
    terms: Optional[ProviderTermsMetadata] = None
    attribution: Optional[ProviderAttributionMetadata] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[ProviderError] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
