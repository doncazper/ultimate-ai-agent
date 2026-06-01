from ultimate_ai_agent.core.control_center import build_control_center_dashboard


def test_control_center_dashboard_snapshot_is_safe_summary_only():
    snapshot = build_control_center_dashboard(
        baseline_version="0.16.0",
        api_route_count=74,
        foundation_gate_status="passed",
    )

    assert snapshot.system_status.status == "available_read_only"
    assert snapshot.foundation_gate_summary.status == "passed"
    assert snapshot.runtime_readiness_summary.production_ready is False
    assert snapshot.api_summary.route_count == 74
    assert snapshot.approval_summary.pending_count == 0
    assert snapshot.remote_worker_summary.execution_enabled is False
    assert snapshot.private_mesh_summary.status == "planned_disabled"
    assert snapshot.mobile_planning_summary.sensor_access_enabled is False
    assert snapshot.plugin_governance_summary.plugin_enablement_allowed is False
    assert snapshot.next_recommended_action == "review_status_and_previews_only"


def test_control_center_dashboard_contains_no_raw_or_secret_content():
    snapshot = build_control_center_dashboard(baseline_version="0.16.0")
    dump = snapshot.model_dump_json().lower()

    forbidden_fragments = [
        "api_key='abcdefghijklmnop'",
        "raw_prompt",
        "file_contents",
        "memory_contents",
        "credential_value",
        "private_key",
        "remote execution enabled",
        "mobile sensor enabled",
        "plugin enabled",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in dump
