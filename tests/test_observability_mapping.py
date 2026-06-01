from datetime import UTC, datetime
import pytest

from ultimate_ai_agent.core.ledger import (
    EventLedgerEvent,
    EventName,
    validate_traceparent,
    map_event_to_otel,
    map_event_to_cloudevent
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext, FreshnessClass, StalenessPolicy
from ultimate_ai_agent.core.hygiene.policies import DataClassification, ClassificationValue

@pytest.fixture
def sample_event():
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

    return EventLedgerEvent(
        event_id="evt_123",
        event_type="model",
        event_name=EventName.model_route_selected,
        run_id="run_abc",
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
        correlation_id="corr_abc",
        actor_context=actor,
        temporal_context=temporal,
        data_classification=classification,
        event_source="com.ultimate_ai_agent",
        subject="Model Router",
        action="select_route",
        outcome="selected",
        status="success",
        severity="info",
        model_routing_ref="gpt-4o",
        cost_attribution={"cost": 0.0005},
        token_accounting={"input_tokens": 100, "output_tokens": 50}
    )

def test_traceparent_validation():
    # Valid W3C traceparent
    assert validate_traceparent("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01") is True
    
    # Invalid traceparents
    assert validate_traceparent("00-invalid-00f067aa0ba902b7-01") is False
    assert validate_traceparent("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7") is False
    assert validate_traceparent("") is False

def test_otel_mapping(sample_event):
    otel = map_event_to_otel(sample_event)
    
    assert otel["name"] == "model.route.selected"
    assert otel["span_kind"] == "CLIENT"
    assert otel["attributes"]["gen_ai.request.model"] == "gpt-4o"
    assert otel["attributes"]["gen_ai.usage.cost"] == 0.0005

def test_cloudevent_mapping(sample_event):
    ce = map_event_to_cloudevent(sample_event)
    
    assert ce["specversion"] == "1.0"
    assert ce["type"] == "com.ultimate_ai_agent.model.route.selected"
    assert ce["id"] == "evt_123"
    assert ce["subject"] == "Model Router"
