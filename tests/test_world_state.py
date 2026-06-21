from ultimate_ai_agent.core.world_state import (
    WorldStateStep,
    compile_world_state_snapshot,
    validate_world_state_secrets,
)

def test_world_state_serialization() -> None:
    step = WorldStateStep(
        step_id="step_1",
        step_type="code_generation",
        outcome="success",
        event_ids=["evt_123"]
    )
    state = compile_world_state_snapshot(
        world_state_id="ws_123",
        run_id="run_123",
        current_phase="implementation",
        current_step="step_1",
        last_event_id="evt_123",
        completed_steps=[step]
    )
    assert state.world_state_id == "ws_123"
    assert len(state.completed_steps) == 1
    assert state.completed_steps[0].step_type == "code_generation"
    assert validate_world_state_secrets(state) is True

def test_world_state_secrets_blocking() -> None:
    # Attempt to inject secret into step outcome
    step = WorldStateStep(
        step_id="step_secret",
        step_type="fetch_credentials",
        outcome="api_key = 'super-secret-123456789'",
        event_ids=["evt_456"]
    )
    state = compile_world_state_snapshot(
        world_state_id="ws_secret",
        run_id="run_secret",
        current_phase="auth",
        current_step="step_secret",
        last_event_id="evt_456",
        completed_steps=[step]
    )
    # The validation function must detect the secret
    assert validate_world_state_secrets(state) is False
