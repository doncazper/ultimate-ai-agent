from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m92_openapi_route_failures,
)


def test_m92_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m92_low_risk_tool_autonomy_single_session" in ids
    assert "m92_low_risk_tool_autonomy_static_safety" in ids
    assert "m92_low_risk_tool_autonomy_route_boundary" in ids
    assert "m92_roadmap_currentness" in ids


def test_m92_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m92_low_risk_tool_autonomy_single_session",
        "m92_low_risk_tool_autonomy_static_safety",
        "m92_low_risk_tool_autonomy_route_boundary",
        "m92_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m92_route_boundary_rejects_single_session_execution_routes() -> None:
    failures = m92_openapi_route_failures(
        {
            "/api/manifest": {},
            "/tools/execute": {},
            "/autonomy/tools/execute": {},
            "/autonomy/session/start": {},
            "/autonomy/session/run": {},
            "/autonomy/session/execute": {},
            "/autonomy/sessions": {},
            "/tools/autonomous/execute": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/tools/execute",
        "/autonomy/tools/execute",
        "/autonomy/session/start",
        "/autonomy/session/run",
        "/autonomy/session/execute",
        "/autonomy/sessions",
        "/tools/autonomous/execute",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m92_openapi_route_failures(app.openapi().get("paths", {}))


def test_m92_static_safety_detects_tool_autonomy_authority(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("low_risk_tool_autonomy_enabled=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m92_low_risk_tool_autonomy_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m92_low_risk_tool_autonomy_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("low_risk_tool_autonomy_enabled=True" in failure for failure in result.failures)
