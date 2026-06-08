from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m110_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m110_mobile_sensor_hardening_freeze_contracts" in ids
    assert "m110_mobile_sensor_hardening_freeze_static_safety" in ids
    assert "m110_mobile_sensor_hardening_freeze_route_boundary" in ids
    assert "m110_roadmap_currentness" in ids


def test_m110_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m110_mobile_sensor_hardening_freeze_contracts",
        "m110_mobile_sensor_hardening_freeze_static_safety",
        "m110_mobile_sensor_hardening_freeze_route_boundary",
        "m110_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m110_route_boundary_rejects_sensor_hardening_runtime_routes() -> None:
    failures = gate_evaluators.m110_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/sensor-hardening": {},
            "/mobile/sensor-hardening/run": {},
            "/mobile/sensor-hardening/freeze": {},
            "/mobile/sensors": {},
            "/mobile/sensors/location": {},
            "/mobile/sensors/camera": {},
            "/mobile/sensors/photos": {},
            "/mobile/sensors/microphone": {},
            "/mobile/background/collect": {},
            "/mobile/background/workers": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=13,
    )

    for forbidden in [
        "/mobile/sensor-hardening",
        "/mobile/sensor-hardening/run",
        "/mobile/sensor-hardening/freeze",
        "/mobile/sensors",
        "/mobile/sensors/location",
        "/mobile/sensors/camera",
        "/mobile/sensors/photos",
        "/mobile/sensors/microphone",
        "/mobile/background/collect",
        "/mobile/background/workers",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m110_openapi_route_failures(app.openapi().get("paths", {}))


def test_m110_static_safety_detects_sensor_hardening_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "hardening_runtime_enabled=True\n"
        "sensor_access_enabled=True\n"
        "raw_sensor_payload_enabled=True\n"
        "background_collection_enabled=True\n"
        "native_mobile_ui_enabled=True\n"
        "dependency_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m110_mobile_sensor_hardening_freeze_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m110_mobile_sensor_hardening_freeze_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("hardening_runtime_enabled=True" in failure for failure in result.failures)
    assert any("sensor_access_enabled=True" in failure for failure in result.failures)
    assert any("raw_sensor_payload_enabled=True" in failure for failure in result.failures)
    assert any("background_collection_enabled=True" in failure for failure in result.failures)
    assert any("native_mobile_ui_enabled=True" in failure for failure in result.failures)
    assert any("dependency_added=True" in failure for failure in result.failures)
