from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


def test_m11_foundation_gate_criteria_exist_and_pass() -> None:
    criteria = default_foundation_gate_criteria()
    m11_ids = {
        "m11_runtime_readiness_files_present",
        "m11_runtime_capability_matrix_safe",
        "m11_manual_smoke_report_validation_safe",
        "m11_no_production_readiness_claim",
        "m11_runtime_api_status_validation_only",
        "m11_no_smoke_script_execution_in_gate",
        "m11_no_runtime_expansion_imports",
        "m11_no_remote_mesh_mobile_or_plugin_enablement",
    }

    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}
    assert m11_ids.issubset(criteria_by_id)

    selected = [criteria_by_id[criterion_id] for criterion_id in sorted(m11_ids)]
    report = FoundationGateEvaluator().evaluate(selected)

    assert report.overall_status == "passed"
    assert report.passed_count == len(m11_ids)
    assert report.failed_count == 0
