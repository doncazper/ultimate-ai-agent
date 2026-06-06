from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m61_openapi_route_failures,
)


def test_m61_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m61_autonomy_mode_charter_review" in ids
    assert "m61_autonomy_mode_charter_static_safety" in ids
    assert "m61_autonomy_mode_charter_route_boundary" in ids
    assert "m61_roadmap_currentness" in ids


def test_m61_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m61_autonomy_mode_charter_review",
        "m61_autonomy_mode_charter_static_safety",
        "m61_autonomy_mode_charter_route_boundary",
        "m61_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m61_openapi_route_guard_denies_autonomy_and_execution_routes() -> None:
    failures = m61_openapi_route_failures(
        {
            "/autonomy/enable": {},
            "/autonomy/session/start": {},
            "/autonomy/run": {},
            "/autonomy/execute": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/shell/execute": {},
            "/network/fetch": {},
            "/browser/click": {},
            "/plugins/execute": {},
            "/background/start": {},
        }
    )

    for forbidden in [
        "/autonomy/enable",
        "/autonomy/session/start",
        "/autonomy/run",
        "/autonomy/execute",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/tool-runtime/execute",
        "/shell/execute",
        "/network/fetch",
        "/browser/click",
        "/plugins/execute",
        "/background/start",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m61_openapi_route_failures(app.openapi().get("paths", {}))


def test_m61_static_gate_scans_autonomy_enablement_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/autonomy_enablement.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("global_autonomy_switch_enabled=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m61_autonomy_mode_charter_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("global_autonomy_switch_enabled=True" in failure for failure in result.failures)
