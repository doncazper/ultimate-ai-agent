from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m150_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m150_ultimate_ai_agent_alpha_contracts" in ids
    assert "m150_ultimate_ai_agent_alpha_static_safety" in ids
    assert "m150_ultimate_ai_agent_alpha_route_boundary" in ids
    assert "m150_roadmap_currentness" in ids


def test_m150_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m150_ultimate_ai_agent_alpha_contracts",
        "m150_ultimate_ai_agent_alpha_static_safety",
        "m150_ultimate_ai_agent_alpha_route_boundary",
        "m150_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m150_route_boundary_rejects_alpha_release_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/ultimate-ai-agent-alpha": {},
        "/ultimate-ai-agent-alpha/publish": {},
        "/alpha/accept": {},
        "/alpha/release": {},
        "/release/publish": {},
        "/release/tag": {},
        "/release/create-tag": {},
        "/release/artifact/build": {},
        "/release/artifact/upload": {},
        "/release/artifact/export": {},
        "/distribution/publish": {},
        "/external-distribution": {},
        "/app-store/submit": {},
        "/testflight/submit": {},
        "/beta/release": {},
        "/v1-alpha/release": {},
        "/v1.0.0-alpha/release": {},
        "/m150/release": {},
        "/release/automation": {},
        "/auth/login": {},
        "/production/authority/enable": {},
    }
    failures = gate_evaluators.m150_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/ultimate-ai-agent-alpha",
        "/ultimate-ai-agent-alpha/publish",
        "/alpha/accept",
        "/alpha/release",
        "/release/publish",
        "/release/tag",
        "/release/create-tag",
        "/release/artifact/build",
        "/release/artifact/upload",
        "/release/artifact/export",
        "/distribution/publish",
        "/external-distribution",
        "/app-store/submit",
        "/testflight/submit",
        "/beta/release",
        "/v1-alpha/release",
        "/v1.0.0-alpha/release",
        "/m150/release",
        "/release/automation",
        "/auth/login",
        "/production/authority/enable",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m150_openapi_route_failures(app.openapi().get("paths", {}))


def test_m150_static_safety_detects_alpha_release_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "release_publication_enabled=True\n"
        "release_tag_enabled=True\n"
        "tag_creation_enabled=True\n"
        "artifact_build_enabled=True\n"
        "artifact_upload_enabled=True\n"
        "artifact_export_enabled=True\n"
        "external_distribution_enabled=True\n"
        "app_store_submission_enabled=True\n"
        "testflight_submission_enabled=True\n"
        "beta_release_enabled=True\n"
        "release_automation_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "release_publication_started=True\n"
        "release_tag_created=True\n"
        "tag_creation_performed=True\n"
        "artifact_build_performed=True\n"
        "artifact_upload_started=True\n"
        "artifact_export_started=True\n"
        "external_distribution_started=True\n"
        "app_store_submission_started=True\n"
        "testflight_submission_started=True\n"
        "release_automation_started=True\n"
        "auth_runtime_started=True\n"
        "/ultimate-ai-agent-alpha\n"
        "/alpha/release\n"
        "/release/publish\n"
        "/release/tag\n"
        "/release/artifact/build\n"
        "/release/artifact/upload\n"
        "/release/artifact/export\n"
        "/distribution/publish\n"
        "/external-distribution\n"
        "/app-store/submit\n"
        "/testflight/submit\n"
        "/beta/release\n"
        "/v1.0.0-alpha/release\n"
        "/release/automation\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m150_ultimate_ai_agent_alpha_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m150_ultimate_ai_agent_alpha_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "release_publication_enabled=True",
        "release_tag_enabled=True",
        "tag_creation_enabled=True",
        "artifact_build_enabled=True",
        "artifact_upload_enabled=True",
        "artifact_export_enabled=True",
        "external_distribution_enabled=True",
        "app_store_submission_enabled=True",
        "testflight_submission_enabled=True",
        "beta_release_enabled=True",
        "release_automation_enabled=True",
        "auth_runtime_enabled=True",
        "login_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "production_authority_granted=True",
        "release_publication_started=True",
        "release_tag_created=True",
        "tag_creation_performed=True",
        "artifact_build_performed=True",
        "artifact_upload_started=True",
        "artifact_export_started=True",
        "external_distribution_started=True",
        "app_store_submission_started=True",
        "testflight_submission_started=True",
        "release_automation_started=True",
        "auth_runtime_started=True",
        "/ultimate-ai-agent-alpha",
        "/alpha/release",
        "/release/publish",
        "/release/tag",
        "/release/artifact/build",
        "/release/artifact/upload",
        "/release/artifact/export",
        "/distribution/publish",
        "/external-distribution",
        "/app-store/submit",
        "/testflight/submit",
        "/beta/release",
        "/v1.0.0-alpha/release",
        "/release/automation",
    ]:
        assert any(fragment in failure for failure in result.failures)
