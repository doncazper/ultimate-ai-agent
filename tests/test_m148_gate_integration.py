from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
import ultimate_ai_agent.core.gate.evaluators as gate_evaluators


def test_m148_foundation_gate_criteria_registered() -> None:
    ids = {criterion.criterion_id for criterion in default_foundation_gate_criteria()}

    assert "m148_external_security_review_contracts" in ids
    assert "m148_external_security_review_static_safety" in ids
    assert "m148_external_security_review_route_boundary" in ids
    assert "m148_roadmap_currentness" in ids


def test_m148_foundation_gate_evaluator_accepts_current_repo() -> None:
    evaluator = gate_evaluators.FoundationGateEvaluator()
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in [
        "m148_external_security_review_contracts",
        "m148_external_security_review_static_safety",
        "m148_external_security_review_route_boundary",
        "m148_roadmap_currentness",
    ]:
        report = evaluator.evaluate([criteria[criterion_id]])
        result = report.results[0]
        assert result.status == "passed", result.failures


def test_m148_route_boundary_rejects_external_security_routes() -> None:
    paths = {
        "/api/manifest": {},
        "/external-security-review": {},
        "/external-security-review/start": {},
        "/external-security-review/export": {},
        "/security/review/start": {},
        "/security/review/export": {},
        "/security/review/runtime": {},
        "/security/vendor": {},
        "/security/vendor/handoff": {},
        "/security/scanner/run": {},
        "/security/vulnerability-scan": {},
        "/security/findings/export": {},
        "/security/audit/upload": {},
        "/repository/export": {},
        "/source/export": {},
        "/issues/export": {},
        "/artifacts/export": {},
        "/auth/login": {},
        "/production/authority/enable": {},
    }
    failures = gate_evaluators.m148_openapi_route_failures(
        paths,
        expected_path_count=len(paths),
    )

    for forbidden in [
        "/external-security-review",
        "/external-security-review/start",
        "/external-security-review/export",
        "/security/review/start",
        "/security/review/export",
        "/security/review/runtime",
        "/security/vendor",
        "/security/vendor/handoff",
        "/security/scanner/run",
        "/security/vulnerability-scan",
        "/security/findings/export",
        "/security/audit/upload",
        "/repository/export",
        "/source/export",
        "/issues/export",
        "/artifacts/export",
        "/auth/login",
        "/production/authority/enable",
    ]:
        assert any(forbidden in failure for failure in failures)
    assert not gate_evaluators.m148_openapi_route_failures(app.openapi().get("paths", {}))


def test_m148_static_safety_detects_external_security_fragments(
    tmp_path: Path,
) -> None:
    src_dir = tmp_path / "src/ultimate_ai_agent/core/productization"
    src_dir.mkdir(parents=True)
    (src_dir / "unsafe.py").write_text(
        "external_vendor_handoff_enabled=True\n"
        "security_vendor_handoff_enabled=True\n"
        "external_review_automation_enabled=True\n"
        "scanner_runtime_enabled=True\n"
        "vulnerability_scan_enabled=True\n"
        "repository_export_enabled=True\n"
        "artifact_export_enabled=True\n"
        "issue_export_enabled=True\n"
        "security_review_runtime_enabled=True\n"
        "auth_runtime_enabled=True\n"
        "login_enabled=True\n"
        "connector_runtime_enabled=True\n"
        "backend_route_enabled=True\n"
        "dependency_added=True\n"
        "beta_release_enabled=True\n"
        "production_authority_granted=True\n"
        "external_vendor_handoff_started=True\n"
        "security_vendor_handoff_started=True\n"
        "external_review_automation_started=True\n"
        "scanner_runtime_performed=True\n"
        "vulnerability_scan_started=True\n"
        "repository_export_performed=True\n"
        "artifact_export_started=True\n"
        "issue_export_started=True\n"
        "security_review_runtime_performed=True\n"
        "auth_runtime_started=True\n"
        "/external-security-review\n"
        "/security/review/start\n"
        "/security/review/export\n"
        "/security/review/runtime\n"
        "/security/vendor\n"
        "/security/scanner/run\n"
        "/security/vulnerability-scan\n"
        "/security/findings/export\n"
        "/security/audit/upload\n"
        "/repository/export\n"
        "/source/export\n"
        "/issues/export\n"
        "/artifacts/export\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/src").mkdir(parents=True)

    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "m148_external_security_review_static_safety"
    )
    result = (
        gate_evaluators.FoundationGateEvaluator(tmp_path)
        .check_m148_external_security_review_static_safety(criterion)
    )

    assert result.status == "failed"
    for fragment in [
        "external_vendor_handoff_enabled=True",
        "security_vendor_handoff_enabled=True",
        "external_review_automation_enabled=True",
        "scanner_runtime_enabled=True",
        "vulnerability_scan_enabled=True",
        "repository_export_enabled=True",
        "artifact_export_enabled=True",
        "issue_export_enabled=True",
        "security_review_runtime_enabled=True",
        "auth_runtime_enabled=True",
        "login_enabled=True",
        "backend_route_enabled=True",
        "dependency_added=True",
        "beta_release_enabled=True",
        "production_authority_granted=True",
        "external_vendor_handoff_started=True",
        "security_vendor_handoff_started=True",
        "external_review_automation_started=True",
        "scanner_runtime_performed=True",
        "vulnerability_scan_started=True",
        "repository_export_performed=True",
        "artifact_export_started=True",
        "issue_export_started=True",
        "security_review_runtime_performed=True",
        "auth_runtime_started=True",
        "/external-security-review",
        "/security/review/start",
        "/security/review/export",
        "/security/review/runtime",
        "/security/vendor",
        "/security/scanner/run",
        "/security/vulnerability-scan",
        "/security/findings/export",
        "/security/audit/upload",
        "/repository/export",
        "/source/export",
        "/issues/export",
        "/artifacts/export",
    ]:
        assert any(fragment in failure for failure in result.failures)
