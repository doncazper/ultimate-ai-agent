from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m184_post_m20_roadmap_projection_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "post_m20_roadmap_projection_present" in criteria_by_id

    report = FoundationGateEvaluator().evaluate([criteria_by_id["post_m20_roadmap_projection_present"]])

    assert report.failed_count == 0
    assert report.passed_count == 1
