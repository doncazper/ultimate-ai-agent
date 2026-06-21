from pathlib import Path
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m73_openapi_route_failures,
)


def test_m73_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m73_browser_automation_contract_review" in ids
    assert "m73_browser_automation_contract_static_safety" in ids
    assert "m73_browser_automation_contract_route_boundary" in ids
    assert "m73_roadmap_currentness" in ids


def test_m73_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m73_browser_automation_contract_review",
        "m73_browser_automation_contract_static_safety",
        "m73_browser_automation_contract_route_boundary",
        "m73_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m73_route_guard_denies_browser_runtime_routes() -> None:
    failures = m73_openapi_route_failures(
        {
            "/browser/observe": {},
            "/browser/click": {},
            "/browser/navigate": {},
            "/browser/type": {},
            "/browser/screenshot": {},
            "/browser/execute": {},
            "/browser/run": {},
            "/browser/session/start": {},
            "/browser/profile/authenticated": {},
            "/tools/browser/execute": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/network/fetch": {},
            "/memory/write": {},
            "/context/inject": {},
        }
    )

    for forbidden in [
        "/browser/observe",
        "/browser/click",
        "/browser/navigate",
        "/browser/type",
        "/browser/screenshot",
        "/browser/execute",
        "/browser/run",
        "/browser/session/start",
        "/browser/profile/authenticated",
        "/tools/browser/execute",
        "/tools/execute",
        "/tool-runtime/execute",
        "/network/fetch",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m73_openapi_route_failures(app.openapi().get("paths", {}))


def test_m73_static_gate_scans_unsafe_browser_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/browser_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("browser_click_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m73_browser_automation_contract_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("browser_click_enabled=True" in failure for failure in result.failures)
