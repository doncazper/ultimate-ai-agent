from datetime import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.truth.enums import SourceFreshnessStatus, TruthSourceType, TruthTaskClass


class FreshnessPolicy(BaseModel):
    policy_id: str
    freshness_window_seconds: Optional[int] = Field(None, ge=0)
    expires_at_required: bool = False
    published_at_required: bool = False
    fetched_at_required: bool = False
    stale_behavior: str = "allow_with_warning"
    applies_to_source_types: List[TruthSourceType] = Field(default_factory=list)
    applies_to_task_classes: List[TruthTaskClass] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


def classify_freshness(evidence_item, policy: FreshnessPolicy, now: datetime) -> SourceFreshnessStatus:
    if evidence_item.expires_at and evidence_item.expires_at <= now:
        return SourceFreshnessStatus.expired
    timestamp = evidence_item.observed_at or evidence_item.published_at or evidence_item.effective_at
    if policy.published_at_required and not evidence_item.published_at:
        return SourceFreshnessStatus.unknown
    if policy.expires_at_required and not evidence_item.expires_at:
        return SourceFreshnessStatus.unknown
    if policy.fetched_at_required and not evidence_item.observed_at:
        return SourceFreshnessStatus.unknown
    if timestamp is None:
        return SourceFreshnessStatus.unknown
    if policy.freshness_window_seconds is None:
        return SourceFreshnessStatus.current
    age_seconds = (now - timestamp).total_seconds()
    if age_seconds <= policy.freshness_window_seconds:
        return SourceFreshnessStatus.current
    return SourceFreshnessStatus.stale


def is_source_stale(evidence_item, policy: FreshnessPolicy, now: datetime) -> bool:
    return classify_freshness(evidence_item, policy, now) in [SourceFreshnessStatus.stale, SourceFreshnessStatus.expired]


def enforce_freshness_policy(evidence_item, policy: FreshnessPolicy, now: datetime) -> Tuple[bool, str]:
    status = classify_freshness(evidence_item, policy, now)
    evidence_item.freshness_status = status
    if status == SourceFreshnessStatus.current:
        return True, "FRESHNESS_CURRENT"
    if status == SourceFreshnessStatus.unknown and policy.stale_behavior in ["require_refresh", "reject"]:
        return False, "FRESHNESS_UNKNOWN"
    if status in [SourceFreshnessStatus.stale, SourceFreshnessStatus.expired]:
        if policy.stale_behavior == "reject":
            return False, "FRESHNESS_REJECTED"
        if policy.stale_behavior == "require_refresh":
            return False, "FRESHNESS_REFRESH_REQUIRED"
        if policy.stale_behavior == "human_review":
            return False, "FRESHNESS_HUMAN_REVIEW_REQUIRED"
    return True, "FRESHNESS_ALLOWED_WITH_WARNING"
