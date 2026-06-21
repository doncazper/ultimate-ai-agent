import pytest
from ultimate_ai_agent.core.ledger import DeterministicRunState, RunState, InvalidStateTransitionError

def test_deterministic_valid_transitions() -> None:
    state = DeterministicRunState(run_id="run_1")
    assert state.current_state == RunState.created
    
    # created -> contract_created
    state.transition_to(RunState.contract_created)
    assert state.current_state == RunState.contract_created

    # contract_created -> context_loaded
    state.transition_to(RunState.context_loaded)
    assert state.current_state == RunState.context_loaded

    # context_loaded -> planned
    state.transition_to(RunState.planned)
    assert state.current_state == RunState.planned

    # planned -> in_progress
    state.transition_to(RunState.in_progress)
    assert state.current_state == RunState.in_progress

    # in_progress -> waiting_for_approval
    state.transition_to(RunState.waiting_for_approval)
    assert state.current_state == RunState.waiting_for_approval

    # waiting_for_approval -> in_progress
    state.transition_to(RunState.in_progress)
    assert state.current_state == RunState.in_progress

    # in_progress -> verifying
    state.transition_to(RunState.verifying)
    assert state.current_state == RunState.verifying

    # verifying -> completed
    state.transition_to(RunState.completed)
    assert state.current_state == RunState.completed

def test_invalid_transition_raises() -> None:
    state = DeterministicRunState(run_id="run_1")
    with pytest.raises(InvalidStateTransitionError):
        # cannot transition from created straight to planned
        state.transition_to(RunState.planned)

def test_terminal_state_frozen() -> None:
    state = DeterministicRunState(run_id="run_1", current_state=RunState.completed)
    with pytest.raises(InvalidStateTransitionError):
        state.transition_to(RunState.in_progress)
