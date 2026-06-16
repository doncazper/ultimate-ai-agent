from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m147_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m147_public_docs_wiki_readiness_contracts" in ids
    assert "m147_public_docs_wiki_readiness_static_safety" in ids
    assert "m147_public_docs_wiki_readiness_route_boundary" in ids
    assert "m147_roadmap_currentness" in ids


def test_m147_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m147_public_docs_wiki_readiness_contracts",
        "m147_public_docs_wiki_readiness_static_safety",
        "m147_public_docs_wiki_readiness_route_boundary",
        "m147_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m147_route_boundary_rejects_public_docs_wiki_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/public-docs/publish": {},
        "/public-docs/deploy": {},
        "/docs/publish": {},
        "/docs/deploy": {},
        "/docs/site/deploy": {},
        "/wiki/publish": {},
        "/wiki/sync": {},
        "/wiki/automation": {},
        "/github/wiki": {},
        "/github/wiki/publish": {},
        "/artifacts/upload": {},
        "/release/publish": {},
        "/distribution/publish": {},
        "/external-distribution": {},
        "/auth/login": {},
        "/production/authority/enable": {},
    }
    failures = gate_evaluators.m147_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/public-docs/publish",
        "/public-docs/deploy",
        "/docs/publish",
        "/docs/deploy",
        "/docs/site/deploy",
        "/wiki/publish",
        "/wiki/sync",
        "/wiki/automation",
        "/github/wiki",
        "/github/wiki/publish",
        "/artifacts/upload",
        "/release/publish",
        "/distribution/publish",
        "/external-distribution",
        "/auth/login",
        "/production/authority/enable",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m147_openapi_route_failures(app.openapi().get("paths", {}))


def test_m147_static_safety_detects_public_publish_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "public_publish_enabled=True\n"
        "wiki_publish_enabled=True\n"
        "wiki_automation_enabled=True\n"
        "github_wiki_runtime_enabled=True\n"
        "docs_site_deploy_enabled=True\n"
        "external_distribution_enabled=True\n"
        "artifact_upload_enabled=True\n"
        "release_publish_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "public_publish_started=True\n"
        "wiki_automation_started=True\n"
        "github_wiki_runtime_performed=True\n"
        "docs_site_deploy_started=True\n"
        "external_distribution_performed=True\n"
        "artifact_upload_started=True\n"
        "release_publish_started=True\n"
        "docs_runtime_performed=True\n"
        "auth_runtime_started=True\n"
        "/public-docs/publish\n"
        "/public-docs/deploy\n"
        "/docs/publish\n"
        "/docs/deploy\n"
        "/wiki/publish\n"
        "/wiki/sync\n"
        "/wiki/automation\n"
        "/github/wiki\n"
        "/artifacts/upload\n"
        "/release/publish\n"
        "/distribution/publish\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m147_public_docs_wiki_readiness_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m147_public_docs_wiki_readiness_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "public_publish_enabled=True",
        "wiki_publish_enabled=True",
        "wiki_automation_enabled=True",
        "github_wiki_runtime_enabled=True",
        "docs_site_deploy_enabled=True",
        "external_distribution_enabled=True",
        "artifact_upload_enabled=True",
        "release_publish_enabled=True",
        "auth_runtime_enabled=True",
        "login_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "beta_release_enabled=True",
        "production_authority_granted=True",
        "public_publish_started=True",
        "wiki_automation_started=True",
        "github_wiki_runtime_performed=True",
        "docs_site_deploy_started=True",
        "external_distribution_performed=True",
        "artifact_upload_started=True",
        "release_publish_started=True",
        "docs_runtime_performed=True",
        "auth_runtime_started=True",
        "/public-docs/publish",
        "/public-docs/deploy",
        "/docs/publish",
        "/docs/deploy",
        "/wiki/publish",
        "/wiki/sync",
        "/wiki/automation",
        "/github/wiki",
        "/artifacts/upload",
        "/release/publish",
        "/distribution/publish",
    ]:
        assert any(fragment in failure for failure in result.failures)
