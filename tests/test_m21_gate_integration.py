from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M21_OPENAPI_PATH_COUNT,
    M21_FORBIDDEN_BACKEND_ROUTES,
    m21_forbidden_openwebui_config_path_matches,
    m21_forbidden_openwebui_runtime_fragment_failures,
    m21_openapi_route_failures,
)
from scripts.verify_all import (
    find_openwebui_forbidden_config_path_matches,
    find_openwebui_forbidden_runtime_fragment_failures,
)


def test_m21_openwebui_bridge_contract_criterion_exists_and_passes():
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m21_openwebui_bridge_contract_safe" in criteria_by_id
    criterion = criteria_by_id["m21_openwebui_bridge_contract_safe"]
    assert "contract-only" in criterion.pass_condition
    assert "OpenWebUI is the preferred conversational web shell" in criterion.pass_condition
    assert "not the agent brain" in criterion.pass_condition
    assert "Agent Core remains authority" in criterion.pass_condition
    assert "no direct tool execution" in criterion.pass_condition
    assert "no direct memory write" in criterion.pass_condition
    assert "no runtime execution" in criterion.pass_condition
    assert "OpenAPI path count at 74" in criterion.pass_condition
    assert "M22 planned" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m21_openapi_route_guard_rejects_openwebui_runtime_expansion():
    failures = m21_openapi_route_failures(
        {
            "/health",
            "/openwebui",
            "/openwebui/bridge",
            "/openwebui/chat",
            "/openwebui/execute",
            "/chat/run",
            "/runtime/execute",
            "/model-runtime/execute",
        },
        expected_path_count=EXPECTED_M21_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M21_OPENAPI_PATH_COUNT == 74
    assert "/openwebui" in M21_FORBIDDEN_BACKEND_ROUTES
    assert "/openwebui/bridge" in M21_FORBIDDEN_BACKEND_ROUTES
    assert "/openwebui/execute" in M21_FORBIDDEN_BACKEND_ROUTES
    assert "/chat/run" in M21_FORBIDDEN_BACKEND_ROUTES
    assert "/model-runtime/execute" in M21_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/openwebui" in failure for failure in failures)
    assert any("/openwebui/execute" in failure for failure in failures)
    assert any("/chat/run" in failure for failure in failures)


def test_m21_gate_scans_openwebui_bridge_package_for_forbidden_runtime_fragments(tmp_path):
    bridge_file = tmp_path / "src" / "ultimate_ai_agent" / "core" / "openwebui_bridge" / "runtime.py"
    bridge_file.parent.mkdir(parents=True)
    bridge_file.write_text("OPENWEBUI_API_KEY = 'blocked'\n", encoding="utf-8")

    failures = m21_forbidden_openwebui_runtime_fragment_failures(tmp_path)

    assert any("src/ultimate_ai_agent/core/openwebui_bridge/runtime.py" in failure for failure in failures)
    assert any("openwebui_api_key" in failure for failure in failures)


def test_m21_gate_recursively_rejects_forbidden_openwebui_config_paths_outside_docs(tmp_path):
    forbidden_config = tmp_path / "sandbox" / "nested" / "openwebui.config.yml"
    allowed_doc = tmp_path / "docs" / "openwebui" / "openwebui.config.yml"
    forbidden_config.parent.mkdir(parents=True)
    allowed_doc.parent.mkdir(parents=True)
    forbidden_config.write_text("disabled: true\n", encoding="utf-8")
    allowed_doc.write_text("documentation-only example\n", encoding="utf-8")

    matches = m21_forbidden_openwebui_config_path_matches(tmp_path)

    assert "sandbox/nested/openwebui.config.yml" in matches
    assert "docs/openwebui/openwebui.config.yml" not in matches


def test_verify_all_openwebui_helpers_match_gate_hardening(tmp_path):
    config_path = tmp_path / "tools" / "openwebui_plugins" / "README.md"
    bridge_file = tmp_path / "src" / "ultimate_ai_agent" / "core" / "openwebui_bridge" / "client.py"
    config_path.parent.mkdir(parents=True)
    bridge_file.parent.mkdir(parents=True)
    config_path.write_text("blocked path\n", encoding="utf-8")
    bridge_file.write_text("openwebui_cookie = 'blocked'\n", encoding="utf-8")

    path_matches = find_openwebui_forbidden_config_path_matches(tmp_path)
    fragment_failures = find_openwebui_forbidden_runtime_fragment_failures(tmp_path)

    assert "tools/openwebui_plugins/README.md" in path_matches
    assert any("src/ultimate_ai_agent/core/openwebui_bridge/client.py" in failure for failure in fragment_failures)
    assert any("openwebui_cookie" in failure for failure in fragment_failures)
