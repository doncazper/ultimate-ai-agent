from typing import Any
from datetime import datetime, timedelta

from ultimate_ai_agent.core.truth import (
    EvidenceItem,
    FreshnessPolicy,
    SourceFreshnessStatus,
    TruthSourceType,
    TruthTaskClass,
    classify_freshness,
    enforce_freshness_policy,
)


NOW = datetime(2026, 6, 1, 12, 0, 0)


def evidence(observed_at: Any | None = None) -> Any:
    return EvidenceItem(
        evidence_id="ev_weather",
        source_id="src_weather",
        source_type=TruthSourceType.provider_result,
        summary="Weather observation.",
        observed_at=observed_at,
        freshness_status=SourceFreshnessStatus.unknown,
        confidence=0.9,
    )


def policy() -> Any:
    return FreshnessPolicy(
        policy_id="fresh_live",
        freshness_window_seconds=3600,
        fetched_at_required=True,
        stale_behavior="reject",
        applies_to_source_types=[TruthSourceType.provider_result],
        applies_to_task_classes=[TruthTaskClass.weather, TruthTaskClass.live_status],
    )


def test_fresh_evidence_classified_current() -> None:
    item = evidence(observed_at=NOW - timedelta(minutes=15))

    assert classify_freshness(item, policy(), NOW) == SourceFreshnessStatus.current


def test_stale_evidence_classified_stale() -> None:
    item = evidence(observed_at=NOW - timedelta(hours=3))

    assert classify_freshness(item, policy(), NOW) == SourceFreshnessStatus.stale


def test_missing_timestamp_classified_unknown() -> None:
    assert classify_freshness(evidence(), policy(), NOW) == SourceFreshnessStatus.unknown


def test_stale_live_status_evidence_rejected() -> None:
    item = evidence(observed_at=NOW - timedelta(hours=3))

    allowed, reason = enforce_freshness_policy(item, policy(), NOW)

    assert allowed is False
    assert reason == "FRESHNESS_REJECTED"
