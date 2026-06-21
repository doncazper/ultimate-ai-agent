from typing import Any
from datetime import UTC, datetime
import pytest
import tempfile
from pathlib import Path

from ultimate_ai_agent.core.ledger import EventLedger, EventLedgerEvent, EventName
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext, FreshnessClass, StalenessPolicy
from ultimate_ai_agent.core.hygiene.policies import DataClassification, ClassificationValue

@pytest.fixture
def dummy_event_factory() -> Any:
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

    def _make(event_id: str = "evt_123", run_id: str = "run_abc", idempotency_key: Any | None = None, metadata: Any | None = None) -> Any:
        return EventLedgerEvent(
            event_id=event_id,
            event_type="run",
            event_name=EventName.run_created,
            run_id=run_id,
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
            severity="info",
            idempotency_key=idempotency_key,
            metadata=metadata or {}
        )
    return _make

def test_ledger_append_success(dummy_event_factory: Any) -> None:
    ledger = EventLedger()
    evt = dummy_event_factory(event_id="evt_1")
    ledger.append_event(evt)
    
    assert len(ledger.list_events()) == 1
    assert ledger.get_event("evt_1") is not None

def test_ledger_rejects_duplicate_event_id(dummy_event_factory: Any) -> None:
    ledger = EventLedger()
    evt1 = dummy_event_factory(event_id="evt_dup")
    evt2 = dummy_event_factory(event_id="evt_dup")
    
    ledger.append_event(evt1)
    with pytest.raises(ValueError, match="Duplicate event_id detected"):
        ledger.append_event(evt2)

def test_ledger_rejects_duplicate_idempotency_key(dummy_event_factory: Any) -> None:
    ledger = EventLedger()
    evt1 = dummy_event_factory(event_id="evt_1", idempotency_key="key_123")
    evt2 = dummy_event_factory(event_id="evt_2", idempotency_key="key_123")
    
    ledger.append_event(evt1)
    with pytest.raises(ValueError, match="Duplicate idempotency_key detected"):
        ledger.append_event(evt2)

def test_ledger_allows_same_idempotency_key_on_different_runs(dummy_event_factory: Any) -> None:
    ledger = EventLedger()
    evt1 = dummy_event_factory(event_id="evt_1", run_id="run_1", idempotency_key="key_123")
    evt2 = dummy_event_factory(event_id="evt_2", run_id="run_2", idempotency_key="key_123")

    ledger.append_event(evt1)
    ledger.append_event(evt2)

    assert [event.event_id for event in ledger.list_events("run_1")] == ["evt_1"]
    assert [event.event_id for event in ledger.list_events("run_2")] == ["evt_2"]

def test_ledger_rejects_raw_secrets(dummy_event_factory: Any) -> None:
    ledger = EventLedger()
    evt = dummy_event_factory(
        event_id="evt_secret",
        metadata={"token": "api-key='abcdef12345678901234567890'"}
    )
    with pytest.raises(ValueError, match="Event append blocked: raw secrets"):
        ledger.append_event(evt)

def test_persistent_jsonl_ledger(dummy_event_factory: Any) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "ledger.jsonl"
        ledger1 = EventLedger(filepath=str(filepath))
        
        evt = dummy_event_factory(event_id="evt_persisted", idempotency_key="persisted_key")
        ledger1.append_event(evt)
        
        # Load from the same file in a new instance
        ledger2 = EventLedger(filepath=str(filepath))
        assert len(ledger2.list_events()) == 1
        assert ledger2.get_event("evt_persisted") is not None
        with pytest.raises(ValueError, match="Duplicate idempotency_key detected"):
            ledger2.append_event(dummy_event_factory(event_id="evt_duplicate_key", idempotency_key="persisted_key"))

def test_persistent_jsonl_ledger_rejects_duplicate_event_id_on_load(dummy_event_factory: Any) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "ledger.jsonl"
        evt1 = dummy_event_factory(event_id="evt_reload_dup", idempotency_key="reload_key_1")
        evt2 = dummy_event_factory(event_id="evt_reload_dup", idempotency_key="reload_key_2")
        filepath.write_text(evt1.model_dump_json() + "\n" + evt2.model_dump_json() + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Duplicate event_id detected"):
            EventLedger(filepath=str(filepath))

def test_persistent_jsonl_ledger_rejects_duplicate_idempotency_key_on_load(dummy_event_factory: Any) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "ledger.jsonl"
        evt1 = dummy_event_factory(event_id="evt_reload_1", idempotency_key="reload_key")
        evt2 = dummy_event_factory(event_id="evt_reload_2", idempotency_key="reload_key")
        filepath.write_text(evt1.model_dump_json() + "\n" + evt2.model_dump_json() + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Duplicate idempotency_key detected"):
            EventLedger(filepath=str(filepath))

def test_trace_integrity_parent_spans(dummy_event_factory: Any) -> None:
    ledger = EventLedger()
    
    # Event 1 (root span)
    evt1 = dummy_event_factory(event_id="evt_1")
    evt1.span_id = "span_root"
    evt1.parent_span_id = None
    
    # Event 2 (child span with external parent)
    evt2 = dummy_event_factory(event_id="evt_2")
    evt2.span_id = "span_child"
    evt2.parent_span_id = "span_external"
    
    ledger.append_event(evt1)
    ledger.append_event(evt2)
    
    # By default, external parent spans are allowed
    assert ledger.validate_trace_integrity("run_abc", allow_external_parent_spans=True) is True
    
    # In internal-only mode, external parent span should cause verification to fail
    assert ledger.validate_trace_integrity("run_abc", allow_external_parent_spans=False) is False
    
    # If parent span exists within the run events, it should pass in internal-only mode too
    evt3 = dummy_event_factory(event_id="evt_3")
    evt3.span_id = "span_child_internal"
    evt3.parent_span_id = "span_root"
    ledger.append_event(evt3)
    
    # Since span_root is in the ledger, it should pass
    # But wait, evt2 still has span_external, so we create a new run context or test run_id
    run2_id = "run_internal_only"
    evt4 = dummy_event_factory(event_id="evt_4", run_id=run2_id)
    evt4.span_id = "span_root"
    evt4.parent_span_id = None
    
    evt5 = dummy_event_factory(event_id="evt_5", run_id=run2_id)
    evt5.span_id = "span_child"
    evt5.parent_span_id = "span_root"
    
    ledger.append_event(evt4)
    ledger.append_event(evt5)
    
    assert ledger.validate_trace_integrity(run2_id, allow_external_parent_spans=False) is True
