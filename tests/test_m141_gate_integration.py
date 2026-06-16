from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m141_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m141_multi_user_product_boundary_contracts" in ids
    assert "m141_multi_user_product_boundary_static_safety" in ids
    assert "m141_multi_user_product_boundary_route_boundary" in ids
    assert "m141_roadmap_currentness" in ids


def test_m141_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m141_multi_user_product_boundary_contracts",
        "m141_multi_user_product_boundary_static_safety",
        "m141_multi_user_product_boundary_route_boundary",
        "m141_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m141_route_boundary_rejects_multi_user_and_auth_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/multi-user": {},
        "/multi-user/enable": {},
        "/multi-user/start": {},
        "/multi-user/run": {},
        "/tenants": {},
        "/tenants/create": {},
        "/tenants/invite": {},
        "/workspaces/share": {},
        "/workspaces/members": {},
        "/identity/federation/enable": {},
        "/auth/login": {},
        "/auth/session": {},
        "/organizations/create": {},
        "/roles/assign": {},
        "/alpha/privacy-review/start": {},
        "/alpha/privacy-review/run": {},
        "/production/authority/enable": {},
        "/tools/execute": {},
        "/browser/click": {},
        "/connectors/write": {},
    }
    failures = gate_evaluators.m141_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/multi-user",
        "/multi-user/enable",
        "/tenants/create",
        "/workspaces/share",
        "/identity/federation/enable",
        "/auth/login",
        "/auth/session",
        "/alpha/privacy-review/start",
        "/production/authority/enable",
        "/tools/execute",
        "/browser/click",
        "/connectors/write",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m141_openapi_route_failures(app.openapi().get("paths", {}))


def test_m141_static_safety_detects_multi_user_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "multi_user_runtime_enabled=True\n"
        "account_tenancy_enabled=True\n"
        "tenant_runtime_enabled=True\n"
        "workspace_sharing_enabled=True\n"
        "identity_federation_enabled=True\n"
        "org_admin_runtime_enabled=True\n"
        "cross_workspace_access_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "session_cookie_enabled=True\n"
        "credential_handling_enabled=True\n"
        "persistent_identity_store_enabled=True\n"
        "account_connector_enabled=True\n"
        "production_runtime_enabled=True\n"
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
        "alpha_privacy_review_enabled=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "multi_user_runtime_started=True\n"
        "tenant_runtime_started=True\n"
        "auth_runtime_started=True\n"
        "tool_execution_performed=True\n"
        "browser_action_performed=True\n"
        "connector_action_performed=True\n"
        "/multi-user/enable\n"
        "/tenants/create\n"
        "/workspaces/share\n"
        "/identity/federation/enable\n"
        "/auth/login\n"
        "/alpha/privacy-review/start\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m141_multi_user_product_boundary_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m141_multi_user_product_boundary_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "multi_user_runtime_enabled=True",
        "account_tenancy_enabled=True",
        "tenant_runtime_enabled=True",
        "workspace_sharing_enabled=True",
        "identity_federation_enabled=True",
        "auth_runtime_enabled=True",
        "login_enabled=True",
        "persistent_identity_store_enabled=True",
        "tool_execution_enabled=True",
        "browser_action_enabled=True",
        "connector_action_enabled=True",
        "backend_route_enabled=True",
        "alpha_privacy_review_enabled=True",
        "production_authority_granted=True",
        "multi_user_runtime_started=True",
        "tool_execution_performed=True",
        "/multi-user/enable",
        "/tenants/create",
        "/workspaces/share",
        "/identity/federation/enable",
        "/auth/login",
        "/alpha/privacy-review/start",
    ]:
        assert any(fragment in failure for failure in result.failures)
