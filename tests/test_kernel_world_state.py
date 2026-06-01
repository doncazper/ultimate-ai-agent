from tests.test_kernel_minimum_lovable_happy_path import request

from ultimate_ai_agent.core.kernel import MinimumKernelRunner


def test_kernel_world_state_tracks_artifact_events_and_rollback(tmp_path):
    result = MinimumKernelRunner().run_task(request(tmp_path))

    world_state = result.world_state
    assert world_state is not None
    assert world_state.current_phase == "completed"
    assert world_state.completed_steps[0].tool_or_component_ref == "file.write.local_dev"
    assert world_state.completed_steps[0].artifact_refs == ["notes/m5.md"]
    assert world_state.completed_steps[0].rollback_ref == result.rollback_ref
    assert world_state.completed_steps[0].event_ids == result.event_ids
