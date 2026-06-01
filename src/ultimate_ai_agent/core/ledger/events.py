from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from ultimate_ai_agent.core.contracts.versioning import EVENT_LEDGER_EVENT_SCHEMA_VERSION
from ultimate_ai_agent.core.ledger.enums import EventName
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext
from ultimate_ai_agent.core.hygiene.policies import DataClassification
from ultimate_ai_agent.core.hygiene.envelopes import ErrorEnvelope

class EventLedgerEvent(BaseModel):
    event_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)  # Category e.g., 'contract', 'tool', etc.
    event_version: str = EVENT_LEDGER_EVENT_SCHEMA_VERSION
    event_name: EventName
    occurred_at: datetime = Field(default_factory=utc_now)
    recorded_at: datetime = Field(default_factory=utc_now)
    run_id: str = Field(..., min_length=1)
    step_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    trace_id: str = Field(..., min_length=1)
    span_id: str = Field(..., min_length=1)
    parent_span_id: Optional[str] = None
    traceparent: Optional[str] = None
    correlation_id: str = Field(..., min_length=1)
    causation_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    actor_context: ActorContext
    temporal_context: TemporalContext
    data_classification: DataClassification
    redaction_summary: Dict[str, Any] = Field(default_factory=dict)
    event_source: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    outcome: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    cost_attribution: Optional[Dict[str, Any]] = None
    token_accounting: Optional[Dict[str, Any]] = None
    model_routing_ref: Optional[str] = None
    tool_call_ref: Optional[str] = None
    approval_ref: Optional[str] = None
    consent_ref: Optional[str] = None
    rollback_ref: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    world_state_snapshot_ref: Optional[str] = None
    error: Optional[ErrorEnvelope] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )
