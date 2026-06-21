from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m182_open_design_governance_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "open_design_governance_docs_present" in criteria_by_id

    report = FoundationGateEvaluator().evaluate([criteria_by_id["open_design_governance_docs_present"]])

    assert report.failed_count == 0
    assert report.passed_count == 1
