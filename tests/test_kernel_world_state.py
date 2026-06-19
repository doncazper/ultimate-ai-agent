from tests.test_kernel_minimum_lovable_happy_path import (
    grant_for_kernel_request,
    grant_workspace_patch_for_kernel_request,
    request,
)

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.kernel import MinimumKernelRunner


def test_kernel_world_state_tracks_artifact_events_and_rollback(tmp_path):
    authority = LocalApprovalAuthority()
    kernel_request = request(tmp_path).model_copy(update={"run_id": "run_kernel_world", "approval_ref": None})
    grant = grant_for_kernel_request(authority, kernel_request)
    workspace_grant = grant_workspace_patch_for_kernel_request(authority, kernel_request)
    result = MinimumKernelRunner(approval_authority=authority).run_task(
        kernel_request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "workspace_approval_ref": workspace_grant.approval_ref,
            }
        )
    )

    world_state = result.world_state
    assert world_state is not None
    assert world_state.current_phase == "completed"
    assert world_state.completed_steps[0].tool_or_component_ref == "file.write.local_dev"
    assert world_state.completed_steps[0].artifact_refs == ["notes/m5.md"]
    assert world_state.completed_steps[0].rollback_ref == result.rollback_ref
    assert world_state.completed_steps[0].event_ids == result.event_ids
