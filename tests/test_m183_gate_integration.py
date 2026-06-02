from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m183_openwebui_ccc_strategy_criterion_exists_and_passes():
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "openwebui_ccc_strategy_docs_present" in criteria_by_id

    report = FoundationGateEvaluator().evaluate([criteria_by_id["openwebui_ccc_strategy_docs_present"]])

    assert report.failed_count == 0
    assert report.passed_count == 1
