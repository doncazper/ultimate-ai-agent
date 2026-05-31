from typing import Dict, Any
from ultimate_ai_agent.core.ledger.events import EventLedgerEvent
from ultimate_ai_agent.core.ledger.enums import EventName

# AsyncAPI Compatibility Specification (Placeholder Schema)
ASYNCAPI_SPEC = {
    "asyncapi": "2.6.0",
    "info": {
        "title": "Ultimate AI Agent Event Stream API",
        "version": "1.0.0",
        "description": "Compatibility spec for event-driven agent interaction."
    },
    "channels": {
        "agent/events": {
            "publish": {
                "message": {
                    "$ref": "#/components/messages/LedgerEventMessage"
                }
            }
        }
    }
}

class OTelSpanMapping(str):
    INTERNAL = "INTERNAL"
    CLIENT = "CLIENT"
    SERVER = "SERVER"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"

def map_event_to_otel(event: EventLedgerEvent) -> Dict[str, Any]:
    """Map internal Event Ledger event properties to OpenTelemetry GenAI semantic convention tags."""
    attributes = {
        "gen_ai.agent.run_id": event.run_id,
        "gen_ai.agent.event_id": event.event_id,
        "gen_ai.agent.event_name": event.event_name,
        "gen_ai.agent.actor_type": event.actor_context.actor_type,
        "gen_ai.agent.actor_id": event.actor_context.actor_id,
        "gen_ai.agent.risk_level": event.severity,
        "db.system": "postgres",
        "trace.id": event.trace_id,
        "span.id": event.span_id
    }

    if event.parent_span_id:
        attributes["span.parent_id"] = event.parent_span_id

    # Model specific OTel semantic attributes
    if event.event_name == EventName.model_route_selected.value:
        attributes["gen_ai.request.model"] = event.model_routing_ref or "default_model"
        attributes["gen_ai.system"] = "ultimate_ai_agent"
        span_kind = OTelSpanMapping.CLIENT
    # Tool specific OTel semantic attributes
    elif event.event_name in [EventName.tool_call_requested.value, EventName.tool_call_completed.value]:
        attributes["gen_ai.tool.name"] = event.tool_call_ref or "tool"
        span_kind = OTelSpanMapping.CLIENT
    else:
        span_kind = OTelSpanMapping.INTERNAL

    # Cost rollup attributes
    if event.cost_attribution:
        attributes["gen_ai.usage.cost"] = event.cost_attribution.get("cost", 0.0)
    if event.token_accounting:
        attributes["gen_ai.usage.input_tokens"] = event.token_accounting.get("input_tokens", 0)
        attributes["gen_ai.usage.output_tokens"] = event.token_accounting.get("output_tokens", 0)

    return {
        "name": event.event_name,
        "span_kind": span_kind,
        "attributes": attributes,
        "timestamp_unix_nano": int(event.occurred_at.timestamp() * 1e9)
    }

def map_event_to_cloudevent(event: EventLedgerEvent) -> Dict[str, Any]:
    """Map internal event to standard CloudEvents 1.0 specifications."""
    return {
        "specversion": "1.0",
        "type": f"com.ultimate_ai_agent.{event.event_name}",
        "source": event.event_source,
        "id": event.event_id,
        "time": event.occurred_at.isoformat(),
        "datacontenttype": "application/json",
        "subject": event.subject,
        "data": {
            "run_id": event.run_id,
            "trace_id": event.trace_id,
            "span_id": event.span_id,
            "action": event.action,
            "outcome": event.outcome,
            "status": event.status,
            "cost_summary": event.cost_attribution
        }
    }
