from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_release_surface.py"
MANIFEST_PATH = ROOT / "docs/control_center/release_surface_manifest.json"
ROUTES_PATH = ROOT / "apps/control-center/src/routes.tsx"
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
VISUAL_MANIFEST_PATH = ROOT / "docs/control_center/visual_regression_manifest.json"


def load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location(
        "verify_control_center_release_surface",
        SCRIPT,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_route_status_manifest() -> dict[str, Any]:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def load_visual_manifest() -> dict[str, Any]:
    return json.loads(VISUAL_MANIFEST_PATH.read_text(encoding="utf-8"))


def test_control_center_release_surface_verifier_passes_current_repo() -> None:
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_control_center_release_surface_manifest_covers_visible_routes() -> None:
    manifest = load_manifest()
    routes_text = ROUTES_PATH.read_text(encoding="utf-8")
    verifier = load_verifier()
    visible_routes = verifier._nav_items(routes_text)

    assert manifest["visual_regression_manifest_ref"] == (
        "docs/control_center/visual_regression_manifest.json"
    )
    assert manifest["status_vocabulary"] == [
        "ship",
        "partial",
        "blocked",
        "experimental",
    ]
    assert len(manifest["routes"]) == len(visible_routes) == 37
    by_path = {route["path"]: route for route in manifest["routes"]}
    assert by_path["/start"]["status"] == "partial"
    assert by_path["/start"]["backend_routes"][0]["path"] == (
        "/control-center/start-here/summary"
    )
    assert by_path["/proof"]["status"] == "partial"
    assert by_path["/proof"]["backend_routes"][0]["path"] == (
        "/control-center/proof/index"
    )
    assert by_path["/proof"]["visual_proof_status"] == "checked_in_baseline"
    assert by_path["/proof"]["visual_baseline_ref"] == (
        "visual-baseline:control-center:proof"
    )
    assert by_path["/trust"]["status"] == "partial"
    assert by_path["/trust"]["backend_routes"][0]["path"] == (
        "/control-center/trust-authority/matrix"
    )
    assert by_path["/trust"]["visual_proof_status"] == "checked_in_baseline"
    assert by_path["/trust"]["visual_baseline_ref"] == (
        "visual-baseline:control-center:trust"
    )
    assert by_path["/today"]["status"] == "partial"
    assert by_path["/today"]["backend_contract_rationale"] == "backend-route-refs-present"
    assert by_path["/today"]["visual_proof_status"] == "checked_in_baseline"
    assert by_path["/today"]["visual_baseline_ref"] == (
        "visual-baseline:control-center:today"
    )
    assert by_path["/inbox"]["status"] == "partial"
    assert by_path["/inbox"]["backend_routes"][0]["path"] == (
        "/control-center/sources/readiness"
    )
    assert by_path["/inbox"]["visual_proof_status"] == "checked_in_baseline"
    assert by_path["/inbox"]["visual_baseline_ref"] == (
        "visual-baseline:control-center:inbox"
    )
    assert by_path["/private-trial"]["status"] == "experimental"
    assert by_path["/private-trial"]["backend_contract_rationale"].startswith(
        "no-backend-route:"
    )
    assert by_path["/private-trial"]["visual_proof_status"] == (
        "experimental_no_baseline"
    )
    assert by_path["/actions"]["status"] == "ship"
    assert by_path["/chat"]["status"] == "ship"
    assert by_path["/chat"]["visual_proof_status"] == "blocked_no_baseline"
    assert by_path["/memory"]["status"] == "ship"
    assert by_path["/evidence"]["status"] == "ship"
    assert by_path["/actions"]["approval_required"] is True
    assert any(
        backend["path"] == "/control-center/actions/{action_id}/reject"
        for backend in by_path["/actions"]["backend_routes"]
    )
    assert by_path["/models"]["status"] == "partial"
    assert by_path["/models"]["backend_routes"][0]["path"] == "/v1/models"
    assert by_path["/models"]["backend_routes"][1]["path"] == (
        "/control-center/local-models/status"
    )
    assert "release_blocker:unsafe_local_model_v1_posture" in (
        by_path["/models"]["blocked_capabilities"]
    )
    assert any(
        "local /v1 runtime posture" in caveat.lower()
        for caveat in by_path["/models"]["product_language_caveats"]
    )
    assert any(
        "dev-only auth bypass" in caveat.lower()
        for caveat in by_path["/chat"]["product_language_caveats"]
    )
    assert by_path["/settings"]["status"] == "partial"
    assert by_path["/settings"]["backend_routes"][0]["path"] == (
        "/control-center/settings/status"
    )
    assert "release_blocker:dev_auth_bypass" in (
        by_path["/settings"]["blocked_capabilities"]
    )
    assert by_path["/crm"]["status"] == "blocked"
    assert by_path["/crm"]["backend_routes"] == []
    assert "missing_backend:control-center-crm-read-route" in (
        by_path["/crm"]["blocked_capabilities"]
    )
    assert by_path["/chat"]["approval_required"] is True
    assert by_path["/files/review"]["approval_required"] is True
    assert by_path["/files/review"]["backend_routes"][0]["path"] == (
        "/files/review/approvals/capture"
    )


def test_control_center_release_surface_verifier_flags_missing_route() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    manifest["routes"] = [
        route for route in manifest["routes"] if route["path"] != "/today"
    ]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("missing visible routes" in failure and "/today" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_fake_ship_without_proof() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/today")
    route["status"] = "ship"
    route["backend_routes"] = []
    route["proof_lanes"] = []
    route["blocked_capabilities"] = ["missing_backend:today-action-mutation-contract"]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("cannot be ship without backend route refs" in failure for failure in failures)
    assert any("cannot be ship without proof lanes" in failure for failure in failures)
    assert any("cannot be ship with blocked capabilities" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_status_drift() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    drifted_manifest = copy.deepcopy(manifest)
    route = next(route for route in drifted_manifest["routes"] if route["path"] == "/today")
    route["status"] = "experimental"

    failures = verifier.verify(
        ROOT,
        manifest=drifted_manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("status drifted from routes.tsx" in failure for failure in failures)
    assert any("status drifted from route status manifest" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_missing_proof_chain() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/today")
    route["promotion_criteria"] = []
    route["product_language_caveats"] = ["Presentation-only caveat."]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("/today promotion_criteria must be a non-empty list" in failure for failure in failures)
    assert any("/today product_language_caveats must block release/authority claims" in failure for failure in failures)
    assert any("/today product_language_caveats must name Python Agent Core as truth" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_no_backend_rationale_drift() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/private-trial")
    route["backend_contract_rationale"] = "backend-route-refs-present"
    route["blocked_capabilities"] = ["public_distribution_claim"]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("/private-trial missing no-backend route rationale" in failure for failure in failures)
    assert any(
        "/private-trial no-backend routes must list a missing_backend blocked capability" in failure
        for failure in failures
    )


def test_control_center_release_surface_verifier_flags_visual_baseline_drift() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/today")
    route["visual_baseline_ref"] = "visual-baseline:control-center:today-drifted"
    route["visual_proof_rationale"] = "Baseline exists."

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("/today visual baseline ref drifted" in failure for failure in failures)
    assert any("/today visual proof rationale must cite checked-in redacted baseline" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_primary_route_without_baseline() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    visual_manifest = load_visual_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/proof")
    route["visual_proof_status"] = "blocked_no_baseline"
    route["visual_baseline_ref"] = "visual-baseline:control-center:proof:not-captured"
    route["visual_proof_rationale"] = "No checked-in visual baseline is recorded."
    visual_manifest["surfaces"] = [
        surface for surface in visual_manifest["surfaces"] if surface["route"] != "/proof"
    ]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        visual_regression_manifest=visual_manifest,
        check_files=False,
    )

    assert any(
        "/proof primary route must have checked-in desktop/mobile visual baseline" in failure
        for failure in failures
    )
    assert any(
        "/proof primary route visual proof must be checked_in_baseline" in failure
        for failure in failures
    )


def test_control_center_release_surface_verifier_flags_missing_visual_baseline_truth() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/chat")
    route["visual_proof_status"] = "checked_in_baseline"
    route["visual_baseline_ref"] = "visual-baseline:control-center:chat"
    route["visual_proof_rationale"] = "Looks complete."

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("/chat visual proof status must be blocked_no_baseline" in failure for failure in failures)
    assert any("/chat missing visual baseline ref must end with :not-captured" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_missing_release_blockers() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/models")
    route["blocked_capabilities"] = [
        capability
        for capability in route["blocked_capabilities"]
        if capability != "release_blocker:unsafe_local_model_v1_posture"
    ]
    route["product_language_caveats"] = [
        "Python Agent Core/API remains product truth; Control Center is presentation only.",
        "Route visibility does not grant public release, production readiness, or production authority.",
    ]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any(
        "/models product_language_caveats must block dev-only auth bypass release posture"
        in failure
        for failure in failures
    )
    assert any(
        "/models product_language_caveats must block unsafe local /v1 runtime posture"
        in failure
        for failure in failures
    )
    assert any(
        "/models blocked_capabilities must include release_blocker:unsafe_local_model_v1_posture"
        in failure
        for failure in failures
    )


def test_control_center_release_surface_verifier_flags_raw_evidence_fragment() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/today")
    route["evidence_refs"] = ["raw prompt transcript"]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any("/today release surface route contains raw evidence fragment" in failure for failure in failures)


def test_control_center_release_surface_verifier_flags_missing_duplicate_backend_ref() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status_manifest = load_route_status_manifest()
    route = next(route for route in manifest["routes"] if route["path"] == "/files/review")
    route["backend_routes"] = []
    route["approval_required"] = False

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status_manifest,
        check_files=False,
    )

    assert any(
        "missing backend route refs" in failure
        and "POST /files/review/approvals/capture" in failure
        for failure in failures
    )
    assert any("mutating backend refs require approval_required=true" in failure for failure in failures)


def test_control_center_release_surface_nav_parser_allows_reordered_fields() -> None:
    verifier = load_verifier()
    routes_text = """
    export const navItems: NavItem[] = [
      { releaseStatus: "partial", role: "primary", status: "storage-backed",
        group: "Founder Loop", label: "Today", path: "/today" },
    ];
    """

    items = verifier._nav_items(routes_text)

    assert items == [
        {
            "path": "/today",
            "label": "Today",
            "group": "Founder Loop",
            "ui_status": "storage-backed",
            "release_status": "partial",
            "role": "primary",
        }
    ]
