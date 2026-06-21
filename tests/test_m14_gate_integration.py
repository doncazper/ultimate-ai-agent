from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m14_foundation_gate_criteria_exist_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    m14_ids = {
        "m14_local_backend_api_base_policy",
        "m14_connection_states_visible_and_safe",
        "m14_backend_api_contract_unchanged",
    }
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert m14_ids.issubset(criteria_by_id)

    selected = [criteria_by_id[criterion_id] for criterion_id in sorted(m14_ids)]
    report = FoundationGateEvaluator().evaluate(selected)

    assert report.failed_count == 0
    assert report.passed_count == len(m14_ids)
