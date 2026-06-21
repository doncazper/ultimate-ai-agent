from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_governed_web_evidence_gate_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "governed_web_evidence_intake_no_live_fetch" in criteria_by_id

    report = FoundationGateEvaluator().evaluate(
        [criteria_by_id["governed_web_evidence_intake_no_live_fetch"]]
    )

    assert report.failed_count == 0
    assert report.passed_count == 1
