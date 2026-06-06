from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m80_openapi_route_failures,
)


def test_m80_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m80_network_browser_openwebui_hardening_freeze_review" in ids
    assert "m80_network_browser_openwebui_hardening_freeze_static_safety" in ids
    assert "m80_network_browser_openwebui_hardening_freeze_route_boundary" in ids
    assert "m80_roadmap_currentness" in ids


def test_m80_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m80_network_browser_openwebui_hardening_freeze_review",
        "m80_network_browser_openwebui_hardening_freeze_static_safety",
        "m80_network_browser_openwebui_hardening_freeze_route_boundary",
        "m80_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m80_openapi_route_guard_denies_runtime_expansion_routes() -> None:
    failures = m80_openapi_route_failures(
        {
            "/network/fetch/unrestricted": {},
            "/browser/click": {},
            "/browser/screenshot": {},
            "/browser/navigate": {},
            "/openwebui/tools/execute": {},
            "/openwebui/context/inject": {},
            "/openwebui/memory/write": {},
            "/plugins/install": {},
            "/plugins/enable": {},
            "/plugins/execute": {},
            "/plugin-runtime/import": {},
            "/plugin-runtime/execute": {},
            "/tools/execute": {},
            "/shell/execute": {},
        }
    )

    for forbidden in [
        "/network/fetch/unrestricted",
        "/browser/click",
        "/browser/screenshot",
        "/browser/navigate",
        "/openwebui/tools/execute",
        "/openwebui/context/inject",
        "/openwebui/memory/write",
        "/plugins/install",
        "/plugins/enable",
        "/plugins/execute",
        "/plugin-runtime/import",
        "/plugin-runtime/execute",
        "/tools/execute",
        "/shell/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m80_openapi_route_failures(app.openapi().get("paths", {}))


def test_m80_static_gate_scans_runtime_authority_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/m80_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("browser_action_execution_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate(
        [criteria["m80_network_browser_openwebui_hardening_freeze_static_safety"]]
    )
    result = report.results[0]

    assert result.status == "failed"
    assert any("browser_action_execution_enabled=True" in failure for failure in result.failures)
