from ultimate_ai_agent.core.gate import FoundationGateEvaluator, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M21_OPENAPI_PATH_COUNT,
    M21_FORBIDDEN_BACKEND_ROUTES,
    m21_openapi_route_failures,
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
