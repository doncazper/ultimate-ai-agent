from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m15_approval_receipt_event_ui_criterion_exists_and_passes():
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m15_approval_receipt_event_ui_safe" in criteria_by_id

    report = FoundationGateEvaluator().evaluate([criteria_by_id["m15_approval_receipt_event_ui_safe"]])

    assert report.failed_count == 0
    assert report.passed_count == 1
