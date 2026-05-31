from pydantic import BaseModel, ConfigDict
from ultimate_ai_agent.core.ledger.enums import RunState

class InvalidStateTransitionError(ValueError):
    pass

# Stable schema version
RUN_STATE_SCHEMA_VERSION = "run_state.v0"

# Strict State Machine Transition Map
ALLOWED_TRANSITIONS = {
    RunState.created: {RunState.contract_created, RunState.failed, RunState.cancelled},
    RunState.contract_created: {RunState.context_loaded, RunState.failed, RunState.cancelled},
    RunState.context_loaded: {RunState.planned, RunState.failed, RunState.cancelled},
    RunState.planned: {RunState.in_progress, RunState.failed, RunState.cancelled},
    RunState.in_progress: {RunState.waiting_for_approval, RunState.verifying, RunState.failed, RunState.cancelled},
    RunState.waiting_for_approval: {RunState.in_progress, RunState.blocked, RunState.failed, RunState.cancelled},
    RunState.blocked: {RunState.in_progress, RunState.failed, RunState.cancelled},
    RunState.verifying: {RunState.completed, RunState.failed, RunState.cancelled},
    RunState.completed: set(),
    RunState.failed: set(),
    RunState.cancelled: set(),
}

class DeterministicRunState(BaseModel):
    run_id: str
    current_state: RunState = RunState.created
    schema_version: str = RUN_STATE_SCHEMA_VERSION

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    def transition_to(self, next_state: RunState) -> "DeterministicRunState":
        current = self.current_state
        # Allow transition to self (no-op)
        if current == next_state:
            return self

        # Validate transition map
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if next_state not in allowed:
            raise InvalidStateTransitionError(
                f"Invalid transition from state '{current}' to state '{next_state}' for run_id '{self.run_id}'"
            )

        self.current_state = next_state
        return self
