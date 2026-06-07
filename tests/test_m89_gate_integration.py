from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m89_openapi_route_failures,
)


def test_m89_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m89_emergency_stop_process_kill_safety_contract" in ids
    assert "m89_emergency_stop_process_kill_static_safety" in ids
    assert "m89_emergency_stop_process_kill_route_boundary" in ids
    assert "m89_roadmap_currentness" in ids


def test_m89_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m89_emergency_stop_process_kill_safety_contract",
        "m89_emergency_stop_process_kill_static_safety",
        "m89_emergency_stop_process_kill_route_boundary",
        "m89_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m89_route_boundary_rejects_kill_and_execution_routes() -> None:
    failures = m89_openapi_route_failures(
        {
            "/api/manifest": {},
            "/emergency/stop": {},
            "/emergency/kill": {},
            "/process/kill": {},
            "/process/signal": {},
            "/commands/execute": {},
            "/shell/execute": {},
            "/process/spawn": {},
            "/filesystem/write": {},
            "/memory/write": {},
            "/context/inject": {},
            "/tools/execute": {},
        },
        expected_path_count=12,
    )

    for forbidden in [
        "/emergency/stop",
        "/emergency/kill",
        "/process/kill",
        "/process/signal",
        "/commands/execute",
        "/shell/execute",
        "/process/spawn",
        "/filesystem/write",
        "/memory/write",
        "/context/inject",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m89_openapi_route_failures(app.openapi().get("paths", {}))


def test_m89_static_safety_detects_process_kill_authority(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/sandbox"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("process_kill_authorized=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m89_emergency_stop_process_kill_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m89_emergency_stop_process_kill_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("process_kill_authorized=True" in failure for failure in result.failures)
