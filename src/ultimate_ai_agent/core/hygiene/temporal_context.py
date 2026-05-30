from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class FreshnessClass(str, Enum):
    static = "static"
    slow_changing = "slow_changing"
    daily = "daily"
    hourly = "hourly"
    near_real_time = "near_real_time"
    breaking = "breaking"
    expired = "expired"
    unknown = "unknown"

class StalenessPolicy(str, Enum):
    allow_with_label = "allow_with_label"
    refresh_required = "refresh_required"
    reject_if_stale = "reject_if_stale"
    manual_review = "manual_review"
    unknown = "unknown"

class TemporalContext(BaseModel):
    current_time_utc: datetime = Field(default_factory=datetime.utcnow)
    user_timezone: Optional[str] = None
    source_observed_at: Optional[datetime] = None
    source_published_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    freshness_window_seconds: Optional[int] = Field(None, ge=0)
    freshness_class: FreshnessClass
    staleness_policy: StalenessPolicy = StalenessPolicy.unknown

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
