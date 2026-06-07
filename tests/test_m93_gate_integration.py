from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m93_openapi_route_failures,
)


def test_m93_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m93_multi_tool_dry_run_promotion" in ids
    assert "m93_multi_tool_dry_run_promotion_static_safety" in ids
    assert "m93_multi_tool_dry_run_promotion_route_boundary" in ids
    assert "m93_roadmap_currentness" in ids


def test_m93_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m93_multi_tool_dry_run_promotion",
        "m93_multi_tool_dry_run_promotion_static_safety",
        "m93_multi_tool_dry_run_promotion_route_boundary",
        "m93_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m93_route_boundary_rejects_promotion_and_real_run_routes() -> None:
    failures = m93_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/dry-run/promote": {},
            "/autonomy/promotion/execute": {},
            "/autonomy/real-run/execute": {},
            "/tools/multi/execute": {},
            "/tools/execute": {},
            "/autonomy/session/start": {},
            "/context/inject": {},
            "/memory/write": {},
            "/browser/click": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/autonomy/dry-run/promote",
        "/autonomy/promotion/execute",
        "/autonomy/real-run/execute",
        "/tools/multi/execute",
        "/tools/execute",
        "/autonomy/session/start",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m93_openapi_route_failures(app.openapi().get("paths", {}))


def test_m93_static_safety_detects_promotion_execution_authority(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("real_run_execution_enabled=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m93_multi_tool_dry_run_promotion_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m93_multi_tool_dry_run_promotion_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("real_run_execution_enabled=True" in failure for failure in result.failures)
