from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m142_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m142_alpha_privacy_review_contracts" in ids
    assert "m142_alpha_privacy_review_static_safety" in ids
    assert "m142_alpha_privacy_review_route_boundary" in ids
    assert "m142_roadmap_currentness" in ids


def test_m142_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m142_alpha_privacy_review_contracts",
        "m142_alpha_privacy_review_static_safety",
        "m142_alpha_privacy_review_route_boundary",
        "m142_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m142_route_boundary_rejects_privacy_and_alpha_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/alpha/privacy-review": {},
        "/alpha/privacy-review/start": {},
        "/alpha/privacy-review/run": {},
        "/alpha/privacy-review/signoff": {},
        "/alpha/ui": {},
        "/alpha/ui/start": {},
        "/alpha/app-readiness/run": {},
        "/privacy-review/execute": {},
        "/privacy-review/run": {},
        "/privacy/raw-content": {},
        "/privacy/export": {},
        "/production/authority/enable": {},
        "/tools/execute": {},
        "/browser/click": {},
        "/connectors/write": {},
    }
    failures = gate_evaluators.m142_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/alpha/privacy-review",
        "/alpha/privacy-review/start",
        "/alpha/privacy-review/signoff",
        "/alpha/ui/start",
        "/privacy-review/execute",
        "/privacy/raw-content",
        "/production/authority/enable",
        "/tools/execute",
        "/browser/click",
        "/connectors/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m142_openapi_route_failures(app.openapi().get("paths", {}))


def test_m142_static_safety_detects_privacy_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "privacy_review_execution_enabled=True\n"
        "alpha_privacy_signoff_enabled=True\n"
        "alpha_ui_runtime_enabled=True\n"
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
        "privacy_review_execution_performed=True\n"
        "alpha_ui_runtime_started=True\n"
        "raw_private_content_accessed=True\n"
        "/alpha/privacy-review/start\n"
        "/alpha/privacy-review/signoff\n"
        "/alpha/ui/start\n"
        "/privacy-review/execute\n"
        "/privacy/raw-content\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m142_alpha_privacy_review_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m142_alpha_privacy_review_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "privacy_review_execution_enabled=True",
        "alpha_privacy_signoff_enabled=True",
        "alpha_ui_runtime_enabled=True",
        "raw_private_content_access_enabled=True",
        "tool_execution_enabled=True",
        "browser_action_enabled=True",
        "connector_action_enabled=True",
        "backend_route_enabled=True",
        "production_authority_granted=True",
        "privacy_review_execution_performed=True",
        "alpha_ui_runtime_started=True",
        "raw_private_content_accessed=True",
        "/alpha/privacy-review/start",
        "/alpha/privacy-review/signoff",
        "/alpha/ui/start",
        "/privacy-review/execute",
        "/privacy/raw-content",
    ]:
        assert any(fragment in failure for failure in result.failures)
