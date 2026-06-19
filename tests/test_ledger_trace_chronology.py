"""Regression tests for EventLedger.validate_trace_integrity chronological checks.

Previously validate_trace_integrity sorted the events by ``occurred_at`` before
checking that timestamps were non-decreasing. Sorting first made the
out-of-order detection unreachable, so the method always reported ``True`` for
ordering regardless of how the events were actually recorded. These tests pin
the corrected behaviour: the stored (append-order) trace must be chronological.
"""

from datetime import UTC, datetime, timedelta

import pytest

from ultimate_ai_agent.core.ledger import EventLedger, EventLedgerEvent, EventName
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.temporal_context import (
    FreshnessClass,
    StalenessPolicy,
    TemporalContext,
)
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification


@pytest.fixture
def event_factory():
    actor = ActorContext(
        actor_type=ActorType.orchestrator,
        actor_id="test_orchestrator",
        authority_source=AuthoritySource.explicit_user_request,
        created_at=datetime.now(UTC),
    )
    temporal = TemporalContext(
        current_time_utc=datetime.now(UTC),
        freshness_class=FreshnessClass.daily,
        staleness_policy=StalenessPolicy.allow_with_label,
    )
    classification = DataClassification(
        classification=ClassificationValue.public, source="test"
    )

    def _make(event_id: str, occurred_at: datetime, run_id: str = "run_chrono"):
        return EventLedgerEvent(
            event_id=event_id,
            event_type="run",
            event_name=EventName.run_created,
            occurred_at=occurred_at,
            run_id=run_id,
            trace_id="trace_chrono",
            span_id=event_id,
            correlation_id="corr_chrono",
            actor_context=actor,
            temporal_context=temporal,
            data_classification=classification,
            event_source="test_source",
            subject="Agent Execution",
            action="start",
            outcome="started",
            status="success",
            severity="info",
            idempotency_key=event_id,
        )

    return _make


def test_trace_integrity_passes_for_chronological_append_order(event_factory):
    ledger = EventLedger()
    base = datetime.now(UTC)
    ledger.append_event(event_factory("evt_1", base))
    ledger.append_event(event_factory("evt_2", base + timedelta(seconds=1)))
    ledger.append_event(event_factory("evt_3", base + timedelta(seconds=2)))

    assert ledger.validate_trace_integrity("run_chrono") is True


def test_trace_integrity_detects_out_of_order_append(event_factory):
    ledger = EventLedger()
    base = datetime.now(UTC)
    # Second event is recorded with a timestamp earlier than the first.
    ledger.append_event(event_factory("evt_1", base))
    ledger.append_event(event_factory("evt_2", base - timedelta(seconds=5)))

    assert ledger.validate_trace_integrity("run_chrono") is False
