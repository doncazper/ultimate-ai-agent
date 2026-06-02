from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m16_event_timeline_trace_viewer_criterion_exists_and_passes():
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m16_event_timeline_trace_viewer_safe" in criteria_by_id
    assert "redacted timeline" in criteria_by_id["m16_event_timeline_trace_viewer_safe"].pass_condition
    assert "raw payloads" in criteria_by_id["m16_event_timeline_trace_viewer_safe"].pass_condition

    report = FoundationGateEvaluator().evaluate([criteria_by_id["m16_event_timeline_trace_viewer_safe"]])

    assert report.failed_count == 0
    assert report.passed_count == 1
