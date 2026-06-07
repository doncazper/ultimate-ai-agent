from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m101_openapi_route_failures,
)


def test_m101_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m101_mobile_sensor_contract_review_contracts" in ids
    assert "m101_mobile_sensor_contract_review_static_safety" in ids
    assert "m101_mobile_sensor_contract_review_route_boundary" in ids
    assert "m101_roadmap_currentness" in ids


def test_m101_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m101_mobile_sensor_contract_review_contracts",
        "m101_mobile_sensor_contract_review_static_safety",
        "m101_mobile_sensor_contract_review_route_boundary",
        "m101_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m101_route_boundary_rejects_sensor_runtime_routes() -> None:
    failures = m101_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/sensors": {},
            "/mobile/sensors/location": {},
            "/mobile/sensors/camera": {},
            "/mobile/sensors/photos": {},
            "/mobile/sensors/microphone": {},
            "/mobile/background/collect": {},
            "/mobile/permissions/prompt": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/mobile/sensors",
        "/mobile/sensors/location",
        "/mobile/sensors/camera",
        "/mobile/sensors/photos",
        "/mobile/sensors/microphone",
        "/mobile/background/collect",
        "/mobile/permissions/prompt",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m101_openapi_route_failures(app.openapi().get("paths", {}))


def test_m101_static_safety_detects_mobile_sensor_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "runtime_sensor_access_enabled=True\nnative_permission_prompt_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m101_mobile_sensor_contract_review_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m101_mobile_sensor_contract_review_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("runtime_sensor_access_enabled=True" in failure for failure in result.failures)
    assert any("native_permission_prompt_enabled=True" in failure for failure in result.failures)
