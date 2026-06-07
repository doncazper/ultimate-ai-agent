from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m96_openapi_route_failures,
)


def test_m96_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m96_plugin_execution_sandbox" in ids
    assert "m96_plugin_execution_sandbox_static_safety" in ids
    assert "m96_plugin_execution_sandbox_route_boundary" in ids
    assert "m96_roadmap_currentness" in ids


def test_m96_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m96_plugin_execution_sandbox",
        "m96_plugin_execution_sandbox_static_safety",
        "m96_plugin_execution_sandbox_route_boundary",
        "m96_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m96_route_boundary_rejects_plugin_execution_routes() -> None:
    failures = m96_openapi_route_failures(
        {
            "/api/manifest": {},
            "/plugins/execute": {},
            "/plugins/load": {},
            "/plugins/marketplace": {},
            "/plugin-runtime/execute": {},
            "/tools/plugins/execute": {},
            "/network/post": {},
            "/tools/execute": {},
            "/context/inject": {},
            "/memory/write": {},
        },
        expected_path_count=10,
    )

    for forbidden in [
        "/plugins/execute",
        "/plugins/load",
        "/plugins/marketplace",
        "/plugin-runtime/execute",
        "/tools/plugins/execute",
        "/network/post",
        "/tools/execute",
        "/context/inject",
        "/memory/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m96_openapi_route_failures(app.openapi().get("paths", {}))


def test_m96_static_safety_detects_external_plugin_enablement(tmp_path: Path) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/plugin_execution_sandbox"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text("external_plugin_loading_allowed=True\n", encoding="utf-8")
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m96_plugin_execution_sandbox_static_safety"
    )
    result = FoundationGateEvaluator(tmp_path).check_m96_plugin_execution_sandbox_static_safety(
        criterion
    )

    assert result.status == "failed"
    assert any("external_plugin_loading_allowed=True" in failure for failure in result.failures)
