from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m12_foundation_gate_criteria_exist_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    m12_ids = {
        "m12_control_center_files_present",
        "m12_control_center_manifest_read_only",
        "m12_control_center_dashboard_secret_safe",
        "m12_control_center_action_preview_no_execution",
        "m12_control_center_api_read_only",
        "m12_no_frontend_dependencies",
        "m12_no_runtime_network_mobile_plugin_expansion",
    }

    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}
    assert m12_ids.issubset(criteria_by_id)

    selected = [criteria_by_id[criterion_id] for criterion_id in sorted(m12_ids)]
    report = FoundationGateEvaluator().evaluate(selected)

    assert report.overall_status == "passed"
    assert report.passed_count == len(m12_ids)
    assert report.failed_count == 0
