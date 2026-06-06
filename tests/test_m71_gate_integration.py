from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m71_openapi_route_failures,
)


def test_m71_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m71_network_tool_contract_review" in ids
    assert "m71_network_tool_contract_static_safety" in ids
    assert "m71_network_tool_contract_route_boundary" in ids
    assert "m71_roadmap_currentness" in ids


def test_m71_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m71_network_tool_contract_review",
        "m71_network_tool_contract_static_safety",
        "m71_network_tool_contract_route_boundary",
        "m71_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m71_route_guard_denies_network_runtime_routes() -> None:
    failures = m71_openapi_route_failures(
        {
            "/network/fetch": {},
            "/network/request": {},
            "/http/fetch": {},
            "/http/request": {},
            "/tools/network/execute": {},
            "/tools/execute": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/memory/write": {},
            "/context/inject": {},
        }
    )

    for forbidden in [
        "/network/fetch",
        "/network/request",
        "/http/fetch",
        "/http/request",
        "/tools/network/execute",
        "/tools/execute",
        "/browser/click",
        "/plugins/execute",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m71_openapi_route_failures(app.openapi().get("paths", {}))


def test_m71_static_gate_scans_network_authority_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/network_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("network_call_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m71_network_tool_contract_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("network_call_enabled=True" in failure for failure in result.failures)
