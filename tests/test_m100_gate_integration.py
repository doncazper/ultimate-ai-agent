from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m100_openapi_route_failures,
)


def test_m100_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m100_mobile_permission_model_v1_contracts" in ids
    assert "m100_mobile_permission_model_v1_static_safety" in ids
    assert "m100_mobile_permission_model_v1_route_boundary" in ids
    assert "m100_roadmap_currentness" in ids


def test_m100_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m100_mobile_permission_model_v1_contracts",
        "m100_mobile_permission_model_v1_static_safety",
        "m100_mobile_permission_model_v1_route_boundary",
        "m100_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m100_route_boundary_rejects_mobile_runtime_routes() -> None:
    failures = m100_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/sensors": {},
            "/mobile/location": {},
            "/mobile/camera": {},
            "/mobile/photos": {},
            "/mobile/background/collect": {},
            "/mobile/push/execute": {},
            "/mobile/permissions/request": {},
            "/mobile/permissions/grant": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/mobile/sensors",
        "/mobile/location",
        "/mobile/camera",
        "/mobile/photos",
        "/mobile/background/collect",
        "/mobile/push/execute",
        "/mobile/permissions/request",
        "/mobile/permissions/grant",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m100_openapi_route_failures(app.openapi().get("paths", {}))


def test_m100_static_safety_detects_mobile_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "mobile_sensor_enabled=True\nbackground_collection_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m100_mobile_permission_model_v1_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m100_mobile_permission_model_v1_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("mobile_sensor_enabled=True" in failure for failure in result.failures)
    assert any("background_collection_enabled=True" in failure for failure in result.failures)
