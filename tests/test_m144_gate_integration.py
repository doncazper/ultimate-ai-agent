from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m144_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m144_plugin_marketplace_policy_draft_contracts" in ids
    assert "m144_plugin_marketplace_policy_draft_static_safety" in ids
    assert "m144_plugin_marketplace_policy_draft_route_boundary" in ids
    assert "m144_roadmap_currentness" in ids


def test_m144_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m144_plugin_marketplace_policy_draft_contracts",
        "m144_plugin_marketplace_policy_draft_static_safety",
        "m144_plugin_marketplace_policy_draft_route_boundary",
        "m144_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m144_route_boundary_rejects_marketplace_and_plugin_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/plugin-marketplace": {},
        "/plugin-marketplace/policy": {},
        "/plugin-marketplace/publish": {},
        "/plugin-marketplace/install": {},
        "/plugin-marketplace/enable": {},
        "/plugin-marketplace/execute": {},
        "/plugins/marketplace": {},
        "/plugins/install": {},
        "/plugins/execute": {},
        "/plugins/load": {},
        "/plugin-runtime/import": {},
        "/plugin-runtime/execute": {},
        "/plugin-package/download": {},
        "/plugin-package/upload": {},
        "/marketplace/listings/write": {},
        "/tools/plugins/execute": {},
        "/network/fetch": {},
        "/production/authority/enable": {},
    }
    failures = gate_evaluators.m144_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/plugin-marketplace",
        "/plugin-marketplace/publish",
        "/plugin-marketplace/install",
        "/plugins/marketplace",
        "/plugins/install",
        "/plugins/execute",
        "/plugin-runtime/import",
        "/plugin-package/download",
        "/marketplace/listings/write",
        "/tools/plugins/execute",
        "/network/fetch",
        "/production/authority/enable",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m144_openapi_route_failures(app.openapi().get("paths", {}))


def test_m144_static_safety_detects_marketplace_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "plugin_marketplace_runtime_enabled=True\n"
        "marketplace_publish_enabled=True\n"
        "plugin_install_enabled=True\n"
        "plugin_enablement_enabled=True\n"
        "plugin_execution_enabled=True\n"
        "external_plugin_authority_enabled=True\n"
        "external_plugin_loading_enabled=True\n"
        "marketplace_listing_mutation_enabled=True\n"
        "package_import_enabled=True\n"
        "runtime_import_enabled=True\n"
        "network_plugin_fetch_enabled=True\n"
        "package_download_enabled=True\n"
        "artifact_upload_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "production_authority_granted=True\n"
        "plugin_marketplace_runtime_started=True\n"
        "marketplace_publish_performed=True\n"
        "plugin_install_performed=True\n"
        "plugin_execution_performed=True\n"
        "package_import_performed=True\n"
        "network_plugin_fetch_performed=True\n"
        "/plugin-marketplace/publish\n"
        "/plugin-marketplace/install\n"
        "/plugins/execute\n"
        "/plugin-runtime/import\n"
        "/plugin-package/download\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m144_plugin_marketplace_policy_draft_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m144_plugin_marketplace_policy_draft_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "plugin_marketplace_runtime_enabled=True",
        "marketplace_publish_enabled=True",
        "plugin_install_enabled=True",
        "plugin_enablement_enabled=True",
        "plugin_execution_enabled=True",
        "external_plugin_authority_enabled=True",
        "external_plugin_loading_enabled=True",
        "marketplace_listing_mutation_enabled=True",
        "package_import_enabled=True",
        "runtime_import_enabled=True",
        "network_plugin_fetch_enabled=True",
        "package_download_enabled=True",
        "artifact_upload_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "production_authority_granted=True",
        "plugin_marketplace_runtime_started=True",
        "marketplace_publish_performed=True",
        "plugin_install_performed=True",
        "plugin_execution_performed=True",
        "package_import_performed=True",
        "network_plugin_fetch_performed=True",
        "/plugin-marketplace/publish",
        "/plugin-marketplace/install",
        "/plugins/execute",
        "/plugin-runtime/import",
        "/plugin-package/download",
    ]:
        assert any(fragment in failure for failure in result.failures)
