from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m99_openapi_route_failures,
)


def test_m99_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m99_autonomy_v1_safety_freeze_review" in ids
    assert "m99_autonomy_v1_safety_freeze_static_safety" in ids
    assert "m99_autonomy_v1_safety_freeze_route_boundary" in ids
    assert "m99_roadmap_currentness" in ids


def test_m99_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m99_autonomy_v1_safety_freeze_review",
        "m99_autonomy_v1_safety_freeze_static_safety",
        "m99_autonomy_v1_safety_freeze_route_boundary",
        "m99_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m99_route_boundary_rejects_autonomy_escape_routes() -> None:
    failures = m99_openapi_route_failures(
        {
            "/api/manifest": {},
            "/autonomy/global/enable": {},
            "/autonomy/run": {},
            "/autonomy/tools/execute": {},
            "/shell/execute": {},
            "/browser/click": {},
            "/network/post": {},
            "/plugins/execute": {},
            "/automation/recurring/worker": {},
            "/scheduler/start": {},
            "/memory/write": {},
            "/context/inject": {},
            "/mobile/sensors": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/autonomy/global/enable",
        "/autonomy/run",
        "/autonomy/tools/execute",
        "/shell/execute",
        "/browser/click",
        "/network/post",
        "/plugins/execute",
        "/automation/recurring/worker",
        "/scheduler/start",
        "/memory/write",
        "/context/inject",
        "/mobile/sensors",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m99_openapi_route_failures(app.openapi().get("paths", {}))


def test_m99_static_safety_detects_broad_autonomy_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/autonomy"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("production_authority_enabled=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m99_autonomy_v1_safety_freeze_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m99_autonomy_v1_safety_freeze_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("production_authority_enabled=True" in failure for failure in result.failures)
