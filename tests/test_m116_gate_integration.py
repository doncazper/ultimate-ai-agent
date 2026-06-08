from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m116_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m116_role_based_authority_contracts" in ids
    assert "m116_role_based_authority_static_safety" in ids
    assert "m116_role_based_authority_route_boundary" in ids
    assert "m116_roadmap_currentness" in ids


def test_m116_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m116_role_based_authority_contracts",
        "m116_role_based_authority_static_safety",
        "m116_role_based_authority_route_boundary",
        "m116_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m116_route_boundary_rejects_authority_runtime_and_auth_routes() -> None:
    failures = gate_evaluators.m116_openapi_route_failures(
        {
            "/api/manifest": {},
            "/authority/roles": {},
            "/authority/enforce": {},
            "/authority/permissions": {},
            "/rbac/enforce": {},
            "/roles/assign": {},
            "/auth/login": {},
            "/auth/session": {},
            "/auth/oauth": {},
            "/credentials/read": {},
            "/account/action": {},
            "/context/inject": {},
            "/memory/write": {},
            "/tools/execute": {},
        },
        expected_path_count=14,
    )

    for forbidden in [
        "/authority/roles",
        "/authority/enforce",
        "/authority/permissions",
        "/rbac/enforce",
        "/roles/assign",
        "/auth/login",
        "/auth/session",
        "/auth/oauth",
        "/credentials/read",
        "/account/action",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m116_openapi_route_failures(app.openapi().get("paths", {}))


def test_m116_static_safety_detects_authority_runtime_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/production_readiness"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "authority_runtime_enabled=True\n"
        "role_enforcement_enabled=True\n"
        "permission_enforcement_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "session_cookie_handling_enabled=True\n"
        "oauth_flow_enabled=True\n"
        "token_exchange_enabled=True\n"
        "credential_handling_enabled=True\n"
        "account_action_enabled=True\n"
        "backend_route_added=True\n"
        "control_center_control_added=True\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m116_role_based_authority_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m116_role_based_authority_static_safety(criterion)
    )

    assert result.status == "failed"
    assert any("authority_runtime_enabled=True" in failure for failure in result.failures)
    assert any("role_enforcement_enabled=True" in failure for failure in result.failures)
    assert any(
        "permission_enforcement_enabled=True" in failure for failure in result.failures
    )
    assert any("auth_runtime_enabled=True" in failure for failure in result.failures)
    assert any("login_enabled=True" in failure for failure in result.failures)
    assert any(
        "session_cookie_handling_enabled=True" in failure
        for failure in result.failures
    )
    assert any("oauth_flow_enabled=True" in failure for failure in result.failures)
    assert any("token_exchange_enabled=True" in failure for failure in result.failures)
    assert any(
        "credential_handling_enabled=True" in failure for failure in result.failures
    )
    assert any("account_action_enabled=True" in failure for failure in result.failures)
    assert any("backend_route_added=True" in failure for failure in result.failures)
    assert any("control_center_control_added=True" in failure for failure in result.failures)
