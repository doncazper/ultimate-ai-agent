from tests.test_kernel_minimum_lovable_happy_path import (
    grant_for_kernel_request,
    grant_workspace_patch_for_kernel_request,
    request,
)

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.kernel import MinimumKernelRunner
from ultimate_ai_agent.core.ledger.enums import EventName


def test_kernel_event_trace_contains_expected_ordered_events(tmp_path):
    authority = LocalApprovalAuthority()
    kernel_request = request(tmp_path).model_copy(update={"run_id": "run_kernel_trace", "approval_ref": None})
    grant = grant_for_kernel_request(authority, kernel_request)
    workspace_grant = grant_workspace_patch_for_kernel_request(authority, kernel_request)
    runner = MinimumKernelRunner(approval_authority=authority)

    result = runner.run_task(
        kernel_request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "workspace_approval_ref": workspace_grant.approval_ref,
            }
        )
    )

    event_names = [event.event_name for event in runner.event_ledger.list_events(result.run_id)]
    assert event_names == [
        EventName.run_created.value,
        EventName.execution_contract_created.value,
        EventName.context_pack_created.value,
        EventName.tool_call_requested.value,
        EventName.file_change_proposed.value,
        EventName.file_change_applied.value,
        EventName.memory_write_proposed.value,
        EventName.event_receipt_generated.value,
        EventName.run_completed.value,
    ]
    assert result.event_ids == [event.event_id for event in runner.event_ledger.list_events(result.run_id)]
    assert runner.event_ledger.validate_trace_integrity(result.run_id)
    assert "abcdefghijklmnop" not in "".join(event.model_dump_json() for event in runner.event_ledger.list_events(result.run_id))
