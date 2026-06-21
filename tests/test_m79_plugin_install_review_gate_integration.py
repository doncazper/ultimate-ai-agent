from pathlib import Path
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    FoundationGateEvaluator,
    m79_openapi_route_failures,
)


def test_m79_foundation_gate_criteria_are_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m79_plugin_install_review" in ids
    assert "m79_plugin_install_static_safety" in ids
    assert "m79_plugin_install_route_boundary" in ids
    assert "m79_roadmap_currentness" in ids


def test_m79_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = FoundationGateEvaluator()
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    for criterion_id in [
        "m79_plugin_install_review",
        "m79_plugin_install_static_safety",
        "m79_plugin_install_route_boundary",
        "m79_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m79_route_guard_denies_plugin_install_enable_execute_routes() -> None:
    failures = m79_openapi_route_failures(
        {
            "/plugins/install": {},
            "/plugins/enable": {},
            "/plugins/execute": {},
            "/plugins/review/install/submit": {},
            "/plugin-runtime/import": {},
            "/plugin-runtime/execute": {},
            "/tools/execute": {},
            "/tool-runtime/execute": {},
            "/memory/write": {},
            "/context/inject": {},
            "/shell/execute": {},
        }
    )

    for forbidden in [
        "/plugins/install",
        "/plugins/enable",
        "/plugins/execute",
        "/plugins/review/install/submit",
        "/plugin-runtime/import",
        "/plugin-runtime/execute",
        "/tools/execute",
        "/tool-runtime/execute",
        "/memory/write",
        "/context/inject",
        "/shell/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not m79_openapi_route_failures(app.openapi().get("paths", {}))


def test_m79_static_gate_scans_unsafe_plugin_install_fragments(tmp_path: Path) -> None:
    src_file = tmp_path / "src/ultimate_ai_agent/plugin_install_escape.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("plugin_install_performed=True\n", encoding="utf-8")

    evaluator = FoundationGateEvaluator(root=tmp_path)
    criteria = {criterion.criterion_id: criterion for criterion in default_foundation_gate_criteria()}

    report = evaluator.evaluate([criteria["m79_plugin_install_static_safety"]])
    result = report.results[0]

    assert result.status == "failed"
    assert any("plugin_install_performed=True" in failure for failure in result.failures)
