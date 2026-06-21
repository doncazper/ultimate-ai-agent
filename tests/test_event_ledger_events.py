from typing import Any
from datetime import UTC, datetime
from pydantic import ValidationError
import pytest

from ultimate_ai_agent.core.ledger import EventLedgerEvent, EventName
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext, FreshnessClass, StalenessPolicy
from ultimate_ai_agent.core.hygiene.policies import DataClassification, ClassificationValue

@pytest.fixture
def dummy_hygiene_contexts() -> tuple[Any, ...]:
    actor = ActorContext(
        actor_type=ActorType.orchestrator,
        actor_id="test_orchestrator",
        authority_source=AuthoritySource.explicit_user_request,
        created_at=datetime.now(UTC)
    )
    temporal = TemporalContext(
        current_time_utc=datetime.now(UTC),
        freshness_class=FreshnessClass.daily,
        staleness_policy=StalenessPolicy.allow_with_label
    )
    classification = DataClassification(
        classification=ClassificationValue.public,
        source="test"
    )
    return actor, temporal, classification

def test_valid_ledger_event_creation(dummy_hygiene_contexts: Any) -> None:
    actor, temporal, classification = dummy_hygiene_contexts
    event = EventLedgerEvent(
        event_id="evt_123",
        event_type="run",
        event_name=EventName.run_created,
        run_id="run_abc",
        trace_id="trace_abc",
        span_id="span_abc",
        correlation_id="corr_abc",
        actor_context=actor,
        temporal_context=temporal,
        data_classification=classification,
        event_source="test_source",
        subject="Agent Execution",
        action="start",
        outcome="started",
        status="success",
        severity="info"
    )
    assert event.event_id == "evt_123"
    assert event.event_name == "run.created"
    assert event.event_version == "event_ledger_event.v0"

def test_invalid_event_missing_fields() -> None:
    with pytest.raises(ValidationError):
        # Missing required fields like run_id, actor_context etc
        EventLedgerEvent(
            event_id="evt_123",
            event_type="run",
            event_name=EventName.run_created
        )
