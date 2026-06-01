from ultimate_ai_agent.core.time import utc_now
from typing import List, Optional
from ultimate_ai_agent.core.world_state.models import StructuredWorldState, WorldStateStep

def compile_world_state_snapshot(
    world_state_id: str,
    run_id: str,
    current_phase: str,
    current_step: str,
    last_event_id: str,
    completed_steps: Optional[List[WorldStateStep]] = None,
    open_decisions: Optional[List[str]] = None,
    active_constraints: Optional[List[str]] = None,
    active_assumptions: Optional[List[str]] = None,
    artifact_refs: Optional[List[str]] = None,
    evidence_refs: Optional[List[str]] = None,
    rollback_refs: Optional[List[str]] = None,
) -> StructuredWorldState:
    """Compile structured world state snapshot from parameters.

    Ensures compact representation suitable for transcript trimming injection,
    while maintaining exact references (event_ids) to the Event Ledger.
    """
    now = utc_now()
    return StructuredWorldState(
        world_state_id=world_state_id,
        run_id=run_id,
        current_phase=current_phase,
        current_step=current_step,
        completed_steps=completed_steps or [],
        open_decisions=open_decisions or [],
        active_constraints=active_constraints or [],
        active_assumptions=active_assumptions or [],
        artifact_refs=artifact_refs or [],
        evidence_refs=evidence_refs or [],
        rollback_refs=rollback_refs or [],
        last_event_id=last_event_id,
        created_at=now,
        updated_at=now
    )
