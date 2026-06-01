from tests.test_kernel_minimum_lovable_happy_path import request

from ultimate_ai_agent.core.kernel import MinimumKernelRunner
from ultimate_ai_agent.core.ledger.enums import EventName


def test_kernel_event_trace_contains_expected_ordered_events(tmp_path):
    runner = MinimumKernelRunner()

    result = runner.run_task(request(tmp_path))

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
