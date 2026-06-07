from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m91_openapi_route_failures,
)


def test_m91_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m91_autonomous_tool_execution_contract" in ids
    assert "m91_autonomous_tool_execution_static_safety" in ids
    assert "m91_autonomous_tool_execution_route_boundary" in ids
    assert "m91_roadmap_currentness" in ids


def test_m91_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m91_autonomous_tool_execution_contract",
        "m91_autonomous_tool_execution_static_safety",
        "m91_autonomous_tool_execution_route_boundary",
        "m91_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m91_route_boundary_rejects_tool_autonomy_execution_routes() -> None:
    failures = m91_openapi_route_failures(
        {
            "/api/manifest": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/autonomy/tools/execute": {},
            "/autonomy/session/start": {},
            "/commands/execute": {},
            "/shell/execute": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=9,
    )

    for forbidden in [
        "/tools/execute",
        "/tool-runtime/execute",
        "/autonomy/tools/execute",
        "/autonomy/session/start",
        "/commands/execute",
        "/shell/execute",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m91_openapi_route_failures(app.openapi().get("paths", {}))


def test_m91_static_safety_detects_tool_autonomy_authority(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/tools"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("autonomous_tool_execution_enabled=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m91_autonomous_tool_execution_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m91_autonomous_tool_execution_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("autonomous_tool_execution_enabled=True" in failure for failure in result.failures)
