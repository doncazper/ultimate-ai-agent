from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m106_openapi_route_failures,
)


def test_m106_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m106_mobile_background_read_only_status_sync_contracts" in ids
    assert "m106_mobile_background_read_only_status_sync_static_safety" in ids
    assert "m106_mobile_background_read_only_status_sync_route_boundary" in ids
    assert "m106_roadmap_currentness" in ids


def test_m106_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m106_mobile_background_read_only_status_sync_contracts",
        "m106_mobile_background_read_only_status_sync_static_safety",
        "m106_mobile_background_read_only_status_sync_route_boundary",
        "m106_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m106_route_boundary_rejects_status_sync_runtime_routes() -> None:
    failures = m106_openapi_route_failures(
        {
            "/api/manifest": {},
            "/mobile/background/status-sync": {},
            "/mobile/background/status-sync/start": {},
            "/mobile/background/status-sync/schedule": {},
            "/mobile/background/status-sync/push": {},
            "/mobile/background/workers": {},
            "/mobile/background/daemon": {},
            "/mobile/background/fetch": {},
            "/mobile/notifications/push": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=11,
    )

    for forbidden in [
        "/mobile/background/status-sync",
        "/mobile/background/status-sync/start",
        "/mobile/background/status-sync/schedule",
        "/mobile/background/status-sync/push",
        "/mobile/background/workers",
        "/mobile/background/daemon",
        "/mobile/background/fetch",
        "/mobile/notifications/push",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m106_openapi_route_failures(app.openapi().get("paths", {}))


def test_m106_static_safety_detects_background_status_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/mobile_companion"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "background_worker_enabled=True\nnetwork_sync_enabled=True\nraw_status_payload_enabled=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m106_mobile_background_read_only_status_sync_static_safety"
    )
    result = (
        FoundationGateEvaluator(tmp_path)
        .check_m106_mobile_background_read_only_status_sync_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("background_worker_enabled=True" in failure for failure in result.failures)
    assert any("network_sync_enabled=True" in failure for failure in result.failures)
    assert any("raw_status_payload_enabled=True" in failure for failure in result.failures)
