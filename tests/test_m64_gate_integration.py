from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m64_openapi_route_failures,
)


def test_m64_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m64_autonomous_plan_simulator_contract_review" in ids
    assert "m64_autonomous_plan_simulator_static_safety" in ids
    assert "m64_autonomous_plan_simulator_route_boundary" in ids
    assert "m64_roadmap_currentness" in ids


def test_m64_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m64_autonomous_plan_simulator_contract_review",
        "m64_autonomous_plan_simulator_static_safety",
        "m64_autonomous_plan_simulator_route_boundary",
        "m64_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m64_openapi_route_guard_denies_simulation_execution_routes() -> None:
    failures = m64_openapi_route_failures(
        {
            "/autonomy/simulate": {},
            "/autonomy/simulator/run": {},
            "/autonomy/execute": {},
            "/autonomy/session/start": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/shell/execute": {},
            "/network/fetch": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/background/start": {},
        }
    )

    for forbidden in [
        "/autonomy/simulate",
        "/autonomy/simulator/run",
        "/autonomy/execute",
        "/autonomy/session/start",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/shell/execute",
        "/network/fetch",
        "/browser/click",
        "/plugins/execute",
        "/background/start",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m64_openapi_route_failures(app.openapi().get("paths", {}))


def test_m64_static_gate_scans_execution_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/autonomous_simulator_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("execution_requested=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m64_autonomous_plan_simulator_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("execution_requested=True" in failure for failure in result.failures)
