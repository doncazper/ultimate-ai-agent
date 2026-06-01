from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from ultimate_ai_agent.core.ledger.events import EventLedgerEvent
from ultimate_ai_agent.core.ledger.enums import EventName, RunState

RECEIPT_SCHEMA_VERSION = "receipt.v0"

class RunReceipt(BaseModel):
    run_id: str = Field(..., min_length=1)
    receipt_id: str = Field(..., min_length=1)
    schema_version: str = RECEIPT_SCHEMA_VERSION
    generated_at: datetime = Field(default_factory=utc_now)
    status: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    event_count: int = Field(..., ge=0)
    started_at: datetime
    completed_at: Optional[datetime] = None
    actions_taken: List[str] = Field(default_factory=list)
    approvals: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    tools_called: List[str] = Field(default_factory=list)
    model_routes: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    rollback_refs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    cost_summary: Optional[Dict[str, Any]] = None
    trace_id: str = Field(..., min_length=1)

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

def generate_receipt_from_events(run_id: str, events: List[EventLedgerEvent]) -> RunReceipt:
    # Filter and sort events
    run_events = [e for e in events if e.run_id == run_id]
    if not run_events:
        raise ValueError(f"No ledger events found for run_id: {run_id}")
    
    # Sort events by occurred_at
    run_events.sort(key=lambda x: x.occurred_at)

    receipt_id = f"rcpt_{run_id}"
    started_at = run_events[0].occurred_at
    completed_at = None
    
    status = RunState.created.value
    summary = "Execution run initialized"
    
    actions_taken = []
    approvals = []
    files_changed = []
    tools_called = []
    model_routes = []
    evidence_refs = []
    rollback_refs = []
    errors = []
    warnings = []
    redactions_applied = []
    
    total_cost = 0.0
    total_tokens = 0
    
    trace_id = run_events[0].trace_id

    for event in run_events:
        name = event.event_name
        
        # Determine status and completion time
        if name == EventName.run_completed.value:
            status = RunState.completed.value
            completed_at = event.occurred_at
        elif name == EventName.run_failed.value:
            status = RunState.failed.value
            completed_at = event.occurred_at
        elif name == EventName.run_blocked.value:
            status = RunState.blocked.value
        elif name == EventName.run_created.value:
            summary = event.subject
        
        # Accumulate actions taken summary (reference based, safe)
        action_desc = f"{event.subject}: {event.action} -> {event.outcome}"
        if action_desc not in actions_taken:
            actions_taken.append(action_desc)

        # Approvals tracking
        if name in [EventName.approval_requested.value, EventName.approval_granted.value, EventName.approval_denied.value]:
            app_desc = f"{event.subject} ({event.action} - {event.status})"
            if app_desc not in approvals:
                approvals.append(app_desc)

        # Files changed tracking (refs only)
        if name in [EventName.file_change_proposed.value, EventName.file_change_applied.value]:
            if event.tool_call_ref and event.tool_call_ref not in files_changed:
                files_changed.append(event.tool_call_ref)

        # Tools called tracking
        if name in [EventName.tool_call_requested.value, EventName.tool_call_completed.value, EventName.tool_call_failed.value]:
            t_ref = event.tool_call_ref or event.action
            if t_ref not in tools_called:
                tools_called.append(t_ref)

        # Model routing tracking
        if name == EventName.model_route_selected.value:
            m_ref = event.model_routing_ref or event.action
            if m_ref not in model_routes:
                model_routes.append(m_ref)

        # Evidence references
        for ref in event.evidence_refs:
            if ref not in evidence_refs:
                evidence_refs.append(ref)

        # Rollback references
        if event.rollback_ref and event.rollback_ref not in rollback_refs:
            rollback_refs.append(event.rollback_ref)

        # Error tracking
        if event.error:
            err_msg = f"{event.error.code}: {event.error.safe_message}"
            if err_msg not in errors:
                errors.append(err_msg)

        # Warnings tracking
        if event.severity in ["warning", "high", "critical"] and name not in [EventName.run_failed.value]:
            warn_msg = f"{event.event_name}: {event.outcome} (severity: {event.severity})"
            if warn_msg not in warnings:
                warnings.append(warn_msg)

        # Redactions applied metadata
        if event.redaction_summary:
            for field in event.redaction_summary.get("fields", []):
                if field not in redactions_applied:
                    redactions_applied.append(field)

        # Cost rollup
        if event.cost_attribution:
            total_cost += event.cost_attribution.get("cost", 0.0)
        if event.token_accounting:
            total_tokens += event.token_accounting.get("total_tokens", 0)

    # Compile safe cost summary
    cost_summary = {
        "total_actual_cost": round(total_cost, 6),
        "total_tokens_consumed": total_tokens
    }

    return RunReceipt(
        run_id=run_id,
        receipt_id=receipt_id,
        status=status,
        summary=summary,
        event_count=len(run_events),
        started_at=started_at,
        completed_at=completed_at,
        actions_taken=actions_taken,
        approvals=approvals,
        files_changed=files_changed,
        tools_called=tools_called,
        model_routes=model_routes,
        evidence_refs=evidence_refs,
        rollback_refs=rollback_refs,
        errors=errors,
        warnings=warnings,
        redactions_applied=redactions_applied,
        cost_summary=cost_summary,
        trace_id=trace_id
    )
