from typing import Any
from datetime import UTC, datetime
import pytest

from ultimate_ai_agent.core.ledger import (
    EventLedgerEvent,
    EventName,
    generate_receipt_from_events,
    RunState
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext, FreshnessClass, StalenessPolicy
from ultimate_ai_agent.core.hygiene.policies import DataClassification, ClassificationValue

@pytest.fixture
def make_event() -> Any:
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

    def _make(event_id: str, event_name: str, subject: Any, action: Any, outcome: Any, cost: Any | None = None, tokens: Any | None = None, error: Any | None = None, redaction_fields: Any | None = None) -> Any:
        cost_attr = {"cost": cost} if cost is not None else None
        token_acct = {"total_tokens": tokens} if tokens is not None else None
        redact_summary = {"fields": redaction_fields} if redaction_fields else {}
        
        return EventLedgerEvent(
            event_id=event_id,
            event_type="run",
            event_name=event_name,
            run_id="run_receipt_1",
            trace_id="trace_receipt",
            span_id=f"span_{event_id}",
            correlation_id="corr_receipt",
            actor_context=actor,
            temporal_context=temporal,
            data_classification=classification,
            event_source="test_source",
            subject=subject,
            action=action,
            outcome=outcome,
            status="success",
            severity="info",
            cost_attribution=cost_attr,
            token_accounting=token_acct,
            error=error,
            redaction_summary=redact_summary
        )
    return _make

def test_generate_deterministic_receipt(make_event: Any) -> None:
    events = [
        make_event("evt_1", EventName.run_created, "Run init", "initialize", "started"),
        make_event("evt_2", EventName.tool_call_completed, "Tool", "call_tool", "finished", cost=0.001, tokens=150),
        make_event("evt_3", EventName.run_completed, "Run finish", "complete", "completed", cost=0.002, tokens=200, redaction_fields=["user_email"])
    ]
    
    receipt = generate_receipt_from_events("run_receipt_1", events)
    
    assert receipt.run_id == "run_receipt_1"
    assert receipt.status == RunState.completed.value
    assert receipt.event_count == 3
    assert receipt.cost_summary["total_actual_cost"] == 0.003
    assert receipt.cost_summary["total_tokens_consumed"] == 350
    assert "user_email" in receipt.redactions_applied
