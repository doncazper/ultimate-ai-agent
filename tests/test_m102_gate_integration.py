from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m102_openapi_route_failures,
)


def test_m102_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m102_location_sensor_off_by_default_contracts" in ids
    assert "m102_location_sensor_off_by_default_static_safety" in ids
    assert "m102_location_sensor_off_by_default_route_boundary" in ids
    assert "m102_roadmap_currentness" in ids


def test_m102_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m102_location_sensor_off_by_default_contracts",
        "m102_location_sensor_off_by_default_static_safety",
        "m102_location_sensor_off_by_default_route_boundary",
        "m102_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m102_route_boundary_rejects_location_runtime_routes() -> None:
    failures = m102_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/location": {},
            "/mobile/location/current": {},
            "/mobile/location/history": {},
            "/mobile/location/geofence": {},
            "/mobile/location/export": {},
            "/mobile/sensors/location": {},
            "/mobile/permissions/prompt": {},
            "/mobile/background/location": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/mobile/location",
        "/mobile/location/current",
        "/mobile/location/history",
        "/mobile/location/geofence",
        "/mobile/location/export",
        "/mobile/sensors/location",
        "/mobile/permissions/prompt",
        "/mobile/background/location",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m102_openapi_route_failures(app.openapi().get("paths", {}))


def test_m102_static_safety_detects_location_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "runtime_location_access_enabled=True\nraw_coordinates_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m102_location_sensor_off_by_default_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m102_location_sensor_off_by_default_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("runtime_location_access_enabled=True" in failure for failure in result.failures)
    assert any("raw_coordinates_enabled=True" in failure for failure in result.failures)
