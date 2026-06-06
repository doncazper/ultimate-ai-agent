from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m74_openapi_route_failures,
)


def test_m74_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m74_browser_observe_only_adapter" in ids
    assert "m74_browser_observe_only_static_safety" in ids
    assert "m74_browser_observe_only_route_boundary" in ids
    assert "m74_roadmap_currentness" in ids


def test_m74_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m74_browser_observe_only_adapter",
        "m74_browser_observe_only_static_safety",
        "m74_browser_observe_only_route_boundary",
        "m74_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m74_route_guard_denies_browser_control_routes() -> None:
    failures = m74_openapi_route_failures(
        {
            "/browser/observe": {},
            "/browser/click": {},
            "/browser/navigate": {},
            "/browser/type": {},
            "/browser/screenshot": {},
            "/browser/dom/raw": {},
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
        "/browser/dom/raw",
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
    assert not m74_openapi_route_failures(app.openapi().get("paths", {}))


def test_m74_static_gate_scans_unsafe_browser_control_fragments(tmp_path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/browser_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("browser_click_performed=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m74_browser_observe_only_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("browser_click_performed=True" in failure for failure in result.failures)
