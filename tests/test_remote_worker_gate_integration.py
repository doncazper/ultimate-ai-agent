from ultimate_ai_agent.core.gate import FoundationGateStatus


def test_m105_gate_criteria_pass_on_current_repo(foundation_gate_results):
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
        "m143_private_mesh_taxonomy_open_source_first",
        "m143_planned_mesh_transports_disabled",
        "m143_no_live_mesh_integrations",
        "documentation_integrity_current",
        "codex_plugin_governance_docs_present",
    ]
    for criterion_id in expected:
        assert criterion_id in foundation_gate_results
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed
