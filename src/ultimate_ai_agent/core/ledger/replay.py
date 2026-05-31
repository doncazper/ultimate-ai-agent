from typing import List
from ultimate_ai_agent.core.ledger.events import EventLedgerEvent
from ultimate_ai_agent.core.ledger.enums import EventName, RunState
from ultimate_ai_agent.core.ledger.run_state import DeterministicRunState

EVENT_TO_STATE_TRANSITION = {
    EventName.run_created.value: RunState.created,
    EventName.execution_contract_created.value: RunState.contract_created,
    EventName.context_pack_created.value: RunState.context_loaded,
    EventName.model_route_selected.value: RunState.planned,
    EventName.tool_call_requested.value: RunState.in_progress,
    EventName.tool_call_completed.value: RunState.in_progress,
    EventName.tool_call_failed.value: RunState.in_progress,
    EventName.file_change_proposed.value: RunState.in_progress,
    EventName.file_change_applied.value: RunState.in_progress,
    EventName.memory_read.value: RunState.in_progress,
    EventName.memory_write_proposed.value: RunState.in_progress,
    EventName.approval_requested.value: RunState.waiting_for_approval,
    EventName.approval_granted.value: RunState.in_progress,
    EventName.approval_denied.value: RunState.in_progress,
    EventName.run_blocked.value: RunState.blocked,
    EventName.event_receipt_generated.value: RunState.verifying,
    EventName.run_completed.value: RunState.completed,
    EventName.run_failed.value: RunState.failed,
}

def replay_run_events(run_id: str, events: List[EventLedgerEvent]) -> DeterministicRunState:
    """Reconstruct run state from ordered events."""
    run_events = [e for e in events if e.run_id == run_id]
    
    # Sort events by occurred_at
    run_events.sort(key=lambda x: x.occurred_at)

    run_state = DeterministicRunState(run_id=run_id, current_state=RunState.created)

    for event in run_events:
        target_state = EVENT_TO_STATE_TRANSITION.get(event.event_name)
        if target_state:
            run_state.transition_to(target_state)

    return run_state
