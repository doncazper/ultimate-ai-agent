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


def test_control_center_release_surface_verifier_passes_current_repo() -> None:
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_control_center_release_surface_manifest_covers_visible_routes() -> None:
    manifest = load_manifest()
    routes_text = ROUTES_PATH.read_text(encoding="utf-8")
    verifier = load_verifier()
    visible_routes = verifier._nav_items(routes_text)

    assert manifest["status_vocabulary"] == [
        "ship",
        "partial",
        "blocked",
        "experimental",
    ]
    assert len(manifest["routes"]) == len(visible_routes) == 33
    by_path = {route["path"]: route for route in manifest["routes"]}
    assert by_path["/today"]["status"] == "partial"
    assert by_path["/inbox"]["status"] == "partial"
    assert by_path["/inbox"]["backend_routes"][0]["path"] == (
        "/control-center/sources/readiness"
    )
    assert by_path["/private-trial"]["status"] == "experimental"
    assert by_path["/actions"]["status"] == "ship"
    assert by_path["/chat"]["status"] == "ship"
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
    assert by_path["/settings"]["status"] == "partial"
    assert by_path["/settings"]["backend_routes"][0]["path"] == (
        "/control-center/settings/status"
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
