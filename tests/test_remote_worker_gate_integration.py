from ultimate_ai_agent.core.gate import FoundationGateEvaluator, FoundationGateStatus


def test_m105_gate_criteria_pass_on_current_repo():
    report = FoundationGateEvaluator().evaluate()
    results = {result.criterion_id: result for result in report.results}

    expected = [
        "m105_remote_worker_files_present",
        "m105_remote_capabilities_default_safe",
        "m105_unknown_node_and_transport_denied",
        "m105_planned_transports_disabled",
        "m105_dry_run_dispatches_nothing",
        "m105_no_remote_network_or_background_execution",
        "m105_no_remote_subagents_tools_or_approvals",
        "m105_remote_output_untrusted",
        "m105_api_routes_are_dry_run_only",
        "m105_docs_foundation_only",
        "m105_remote_tailnet_enable_flag_rejected",
        "m105_remote_personal_data_enable_flag_rejected",
        "m105_remote_worker_api_extra_fields_forbidden",
    ]
    for criterion_id in expected:
        assert criterion_id in results
        assert results[criterion_id].status == FoundationGateStatus.passed
