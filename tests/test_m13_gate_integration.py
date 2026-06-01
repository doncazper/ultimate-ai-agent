from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria


ROOT = Path(__file__).resolve().parents[1]


def test_m13_foundation_gate_criteria_exist_and_pass():
    criteria = default_foundation_gate_criteria()
    m13_ids = {
        "m13_web_control_center_files_present",
        "m13_web_shell_read_only_preview_only",
        "m13_action_preview_ui_posts_only_to_preview",
        "m13_mock_data_safe_non_authoritative",
        "m13_no_tracked_generated_or_native_artifacts",
        "m13_backend_api_contract_unchanged",
        "m13_frontend_no_sensitive_browser_apis",
        "m13_control_center_frontend_safety_verifier_passes",
        "m13_frontend_ci_covers_local_checks",
        "m13_browser_smoke_readiness_manual_local_only",
        "m13_browser_smoke_readiness_verifier_passes",
    }

    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}
    assert m13_ids.issubset(criteria_by_id)

    selected = [criteria_by_id[criterion_id] for criterion_id in sorted(m13_ids)]
    report = FoundationGateEvaluator().evaluate(selected)

    assert report.overall_status == "passed"
    assert report.passed_count == len(m13_ids)
    assert report.failed_count == 0


def test_frontend_source_declares_only_preview_post_route():
    endpoints = (ROOT / "apps/control-center/src/api/endpoints.ts").read_text(encoding="utf-8")
    client = (ROOT / "apps/control-center/src/api/client.ts").read_text(encoding="utf-8")

    assert 'actionPreview: "/control-center/actions/preview"' in endpoints
    assert "/control-center/actions/execute" not in endpoints
    assert "/control-center/plugins/enable" not in endpoints
    assert "/control-center/remote-workers/dispatch" not in endpoints
    assert client.count('method: "POST"') == 1
    assert "API_ENDPOINTS.actionPreview" in client


def test_frontend_package_has_only_local_shell_dependencies():
    package = (ROOT / "apps/control-center/package.json").read_text(encoding="utf-8").lower()
    forbidden = [
        '"next"',
        '"tailwindcss"',
        '"stripe"',
        '"@supabase/supabase-js"',
        '"openai"',
        '"anthropic"',
        '"expo"',
        '"react-native"',
        '"electron"',
        '"playwright"',
        '"puppeteer"',
    ]
    for fragment in forbidden:
        assert fragment not in package


def test_frontend_mocks_remain_non_authoritative():
    mock = (ROOT / "apps/control-center/src/mocks/controlCenterData.ts").read_text(encoding="utf-8").lower()
    required = [
        "mock: true",
        "production_control_center: false",
        "production_ready: false",
        "real_model_runtime_ready: false",
        "remote_execution_ready: false",
        "mobile_sensor_ready: false",
        "plugin_or_native_build_ready: false",
        "model_output_authoritative: false",
    ]
    for fragment in required:
        assert fragment in mock
