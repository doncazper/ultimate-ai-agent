from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m143_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m143_alpha_ui_app_readiness_contracts" in ids
    assert "m143_alpha_ui_app_readiness_static_safety" in ids
    assert "m143_alpha_ui_app_readiness_route_boundary" in ids
    assert "m143_roadmap_currentness" in ids


def test_m143_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m143_alpha_ui_app_readiness_contracts",
        "m143_alpha_ui_app_readiness_static_safety",
        "m143_alpha_ui_app_readiness_route_boundary",
        "m143_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m143_route_boundary_rejects_ui_app_and_release_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/alpha/ui": {},
        "/alpha/ui/start": {},
        "/alpha/ui/run": {},
        "/alpha/app-readiness": {},
        "/alpha/app-readiness/run": {},
        "/alpha/app-readiness/signoff": {},
        "/app/readiness/execute": {},
        "/app/build": {},
        "/app/sign": {},
        "/app-store/connect": {},
        "/testflight/upload": {},
        "/alpha/release": {},
        "/beta/release": {},
        "/production/authority/enable": {},
        "/tools/execute": {},
        "/browser/click": {},
        "/connectors/write": {},
    }
    failures = gate_evaluators.m143_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/alpha/ui",
        "/alpha/ui/start",
        "/alpha/app-readiness",
        "/alpha/app-readiness/run",
        "/app/build",
        "/app/sign",
        "/app-store/connect",
        "/testflight/upload",
        "/alpha/release",
        "/beta/release",
        "/production/authority/enable",
        "/tools/execute",
        "/browser/click",
        "/connectors/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m143_openapi_route_failures(app.openapi().get("paths", {}))


def test_m143_static_safety_detects_ui_app_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "alpha_ui_runtime_enabled=True\n"
        "app_readiness_execution_enabled=True\n"
        "app_build_enabled=True\n"
        "app_signing_enabled=True\n"
        "app_store_connect_enabled=True\n"
        "testflight_upload_enabled=True\n"
        "alpha_release_enabled=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "raw_private_content_access_enabled=True\n"
        "execution_enabled=True\n"
        "tool_execution_enabled=True\n"
        "shell_execution_enabled=True\n"
        "browser_action_enabled=True\n"
        "connector_action_enabled=True\n"
        "network_access_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "model_call_enabled=True\n"
        "memory_write_enabled=True\n"
        "context_injection_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "alpha_ui_runtime_started=True\n"
        "app_readiness_execution_performed=True\n"
        "app_build_performed=True\n"
        "app_store_connect_performed=True\n"
        "testflight_upload_performed=True\n"
        "/alpha/ui/start\n"
        "/alpha/app-readiness/run\n"
        "/app/build\n"
        "/app-store/connect\n"
        "/testflight/upload\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m143_alpha_ui_app_readiness_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m143_alpha_ui_app_readiness_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "alpha_ui_runtime_enabled=True",
        "app_readiness_execution_enabled=True",
        "app_build_enabled=True",
        "app_store_connect_enabled=True",
        "testflight_upload_enabled=True",
        "alpha_release_enabled=True",
        "production_authority_granted=True",
        "raw_private_content_access_enabled=True",
        "tool_execution_enabled=True",
        "browser_action_enabled=True",
        "connector_action_enabled=True",
        "backend_route_enabled=True",
        "alpha_ui_runtime_started=True",
        "app_readiness_execution_performed=True",
        "app_build_performed=True",
        "app_store_connect_performed=True",
        "testflight_upload_performed=True",
        "/alpha/ui/start",
        "/alpha/app-readiness/run",
        "/app/build",
        "/app-store/connect",
        "/testflight/upload",
    ]:
        assert any(fragment in failure for failure in result.failures)
