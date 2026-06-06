from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m75_openapi_route_failures,
)


def test_m75_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m75_browser_action_dry_run_planner" in ids
    assert "m75_browser_action_dry_run_static_safety" in ids
    assert "m75_browser_action_dry_run_route_boundary" in ids
    assert "m75_roadmap_currentness" in ids


def test_m75_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m75_browser_action_dry_run_planner",
        "m75_browser_action_dry_run_static_safety",
        "m75_browser_action_dry_run_route_boundary",
        "m75_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m75_route_guard_denies_browser_action_runtime_routes() -> None:
    failures = m75_openapi_route_failures(
        {
            "/browser/actions/plan": {},
            "/browser/actions/run": {},
            "/browser/actions/execute": {},
            "/browser/click": {},
            "/browser/navigate": {},
            "/browser/type": {},
            "/browser/screenshot": {},
            "/browser/dom/raw": {},
            "/browser/session/start": {},
            "/tools/browser/execute": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/network/fetch": {},
            "/memory/write": {},
            "/context/inject": {},
        }
    )

    for forbidden in [
        "/browser/actions/plan",
        "/browser/actions/run",
        "/browser/actions/execute",
        "/browser/click",
        "/browser/navigate",
        "/browser/type",
        "/browser/screenshot",
        "/browser/dom/raw",
        "/browser/session/start",
        "/tools/browser/execute",
        "/tools/execute",
        "/tool-runtime/execute",
        "/network/fetch",
        "/memory/write",
        "/context/inject",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m75_openapi_route_failures(app.openapi().get("paths", {}))


def test_m75_static_gate_scans_unsafe_browser_action_fragments(tmp_path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/browser_action_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("browser_action_execution_performed=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m75_browser_action_dry_run_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("browser_action_execution_performed=True" in failure for failure in result.failures)
