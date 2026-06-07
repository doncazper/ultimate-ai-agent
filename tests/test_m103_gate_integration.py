from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m103_openapi_route_failures,
)


def test_m103_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m103_camera_photos_metadata_only_contracts" in ids
    assert "m103_camera_photos_metadata_only_static_safety" in ids
    assert "m103_camera_photos_metadata_only_route_boundary" in ids
    assert "m103_roadmap_currentness" in ids


def test_m103_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m103_camera_photos_metadata_only_contracts",
        "m103_camera_photos_metadata_only_static_safety",
        "m103_camera_photos_metadata_only_route_boundary",
        "m103_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m103_route_boundary_rejects_camera_photos_runtime_routes() -> None:
    failures = m103_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/camera": {},
            "/mobile/camera/capture": {},
            "/mobile/photos": {},
            "/mobile/photos/read": {},
            "/mobile/photos/export": {},
            "/mobile/media/raw": {},
            "/mobile/media/export": {},
            "/mobile/permissions/prompt": {},
            "/mobile/background/media": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=12,
    )

    for forbidden in [
        "/mobile/camera",
        "/mobile/camera/capture",
        "/mobile/photos",
        "/mobile/photos/read",
        "/mobile/photos/export",
        "/mobile/media/raw",
        "/mobile/media/export",
        "/mobile/permissions/prompt",
        "/mobile/background/media",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m103_openapi_route_failures(app.openapi().get("paths", {}))


def test_m103_static_safety_detects_camera_photos_runtime_fragments(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "camera_runtime_access_enabled=True\nraw_media_content_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m103_camera_photos_metadata_only_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m103_camera_photos_metadata_only_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("camera_runtime_access_enabled=True" in failure for failure in result.failures)
    assert any("raw_media_content_enabled=True" in failure for failure in result.failures)
